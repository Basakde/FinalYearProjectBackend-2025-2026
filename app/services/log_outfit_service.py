from __future__ import annotations

import json
from datetime import datetime, timezone, date, time
from typing import Dict, Optional, List
from zoneinfo import ZoneInfo

from fastapi import HTTPException
import calendar
from app.services.outfit_service import create_outfit_service


from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import List, Optional, Dict
from fastapi import HTTPException

DUBLIN_TZ = ZoneInfo("Europe/Dublin")

async def log_outfit_service(
    pool,
    user_id: str,
    item_ids: List[Optional[str]],
    outfit_id: str | None,
    master_occasion_id: Optional[str] = None,
    name: Optional[str] = None,
    worn_at: Optional[str] = None
) -> Dict[str, str]:
    async with pool.acquire() as conn:
        async with conn.transaction():

            if outfit_id:
                used_outfit_id = outfit_id
            else:
                used_outfit_id = await create_outfit_service(
                    conn, user_id, item_ids, master_occasion_id, name
                )

            if worn_at:
                try:
                    selected_date = date.fromisoformat(worn_at)
                    used_worn_at = datetime.combine(
                        selected_date,
                        time(12, 0),
                        tzinfo=DUBLIN_TZ

                    )
                except Exception:
                    raise HTTPException(400, "Invalid worn_at format, expected YYYY-MM-DD")
            else:
                used_worn_at = datetime.now(DUBLIN_TZ)

            row = await conn.fetchrow(
                """
                INSERT INTO outfit_wear_log (worn_at, outfit_id)
                VALUES ($1, $2)
                RETURNING id::text AS wear_log_id, outfit_id::text;
                """,
                used_worn_at,
                used_outfit_id,
            )

            now_local = datetime.now(DUBLIN_TZ)

            if used_worn_at <= now_local:
                await conn.execute(
                    """
                    UPDATE ClothingItems ci
                    SET last_worn_at = sub.max_worn_at
                    FROM (
                        SELECT
                            oi.item_id,
                            MAX(owl.worn_at) AS max_worn_at
                        FROM OutfitItems oi
                        JOIN outfit_wear_log owl
                            ON owl.outfit_id = oi.outfit_id
                        WHERE oi.item_id IN (
                            SELECT item_id
                            FROM OutfitItems
                            WHERE outfit_id = $1
                        )
                        GROUP BY oi.item_id
                    ) sub
                    WHERE ci.id = sub.item_id;
                    """,
                    used_outfit_id,
                )

        return dict(row)


async def get_logged_outfits_month_service(pool, user_id: str, month: str):
    """
    Returns a list of {date: 'YYYY-MM-DD', count: int} for all days in the month
    that have at least 1 logged outfit for this user.
    """
    try:
        y, m = map(int, month.split("-"))
        start = date(y, m, 1)
        end = date(y, m, calendar.monthrange(y, m)[1])
    except Exception:
        raise HTTPException(400, "month must be YYYY-MM")

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT (owl.worn_at AT TIME ZONE 'Europe/Dublin')::date AS date,
                   COUNT(*)::int AS count
            FROM outfit_wear_log owl
            JOIN Outfits o ON o.id = owl.outfit_id
            WHERE o.user_id = $1::uuid
              AND (owl.worn_at AT TIME ZONE 'Europe/Dublin')::date BETWEEN $2 AND $3
            GROUP BY 1
            ORDER BY 1;
            """,
            user_id,
            start,
            end,
        )

    return [{"date": str(r["date"]), "count": r["count"]} for r in rows]


async def get_logged_outfits_day_service(pool, user_id: str, date_str: str):
    """
    Returns all logs for a given day as:
    {wear_log_id, worn_at, note, outfit_id, outfit_name}
    """
    try:
        y, m, d = map(int, date_str.split("-"))
        day = date(y, m, d)
    except Exception:
        raise HTTPException(400, "date_str must be YYYY-MM-DD")

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
              owl.id::text AS wear_log_id,
              owl.worn_at,
              o.id::text AS outfit_id,

              COALESCE(
                json_agg(
                  json_build_object(
                    'item_id', ci.id::text,
                    'image_url', ci.image_url,
                    'category', ci.category,
                    'position', oi.position
                  )
                  ORDER BY oi.position
                ) FILTER (WHERE ci.id IS NOT NULL),
                '[]'::json
              ) AS items

            FROM outfit_wear_log owl
            JOIN Outfits o ON o.id = owl.outfit_id
            LEFT JOIN OutfitItems oi ON oi.outfit_id = o.id
            LEFT JOIN ClothingItems ci ON ci.id = oi.item_id

            WHERE o.user_id = $1::uuid
              AND (owl.worn_at AT TIME ZONE 'Europe/Dublin')::date = $2

            GROUP BY owl.id, owl.worn_at, o.id
            ORDER BY owl.worn_at DESC;
            """,
            user_id,
            day
        )

    return [
        {
            "wear_log_id": r["wear_log_id"],
            "worn_at": r["worn_at"].isoformat() if r["worn_at"] else None,
            "outfit_id": r["outfit_id"],
            "items": json.loads(r["items"]) if isinstance(r["items"], str) else (r["items"] or [])
        }
        for r in rows
    ]


async def delete_logged_outfit_service(pool, user_id: str, wear_log_id: str) -> Dict[str, str]:
    async with pool.acquire() as conn:
        async with conn.transaction():

            # 1) Make sure the wear log exists and belongs to this user
            log_row = await conn.fetchrow(
                """
                SELECT
                    owl.id,
                    owl.outfit_id
                FROM outfit_wear_log owl
                JOIN Outfits o ON o.id = owl.outfit_id
                WHERE owl.id = $1::uuid
                  AND o.user_id = $2::uuid;
                """,
                wear_log_id,
                user_id,
            )

            if not log_row:
                raise HTTPException(status_code=404, detail="Wear log not found")

            outfit_id = log_row["outfit_id"]

            # 2) Get all items that belong to the outfit of this wear log
            item_rows = await conn.fetch(
                """
                SELECT item_id
                FROM OutfitItems
                WHERE outfit_id = $1;
                """,
                outfit_id,
            )
            item_ids = [row["item_id"] for row in item_rows]

            # 3) Delete only the wear log row
            await conn.execute(
                """
                DELETE FROM outfit_wear_log
                WHERE id = $1::uuid;
                """,
                wear_log_id,
            )

            # 4) Recalculate last_worn_at for each affected item
            #    using remaining wear logs up to "now" only
            now_utc = datetime.now(DUBLIN_TZ)

            for item_id in item_ids:
                latest_row = await conn.fetchrow(
                    """
                    SELECT MAX(owl.worn_at) AS latest_worn_at
                    FROM outfit_wear_log owl
                    JOIN OutfitItems oi ON oi.outfit_id = owl.outfit_id
                    JOIN Outfits o ON o.id = owl.outfit_id
                    WHERE oi.item_id = $1
                      AND o.user_id = $2::uuid
                      AND owl.worn_at <= $3;
                    """,
                    item_id,
                    user_id,
                    now_utc,
                )

                latest_worn_at = latest_row["latest_worn_at"] if latest_row else None

                await conn.execute(
                    """
                    UPDATE ClothingItems
                    SET last_worn_at = $1
                    WHERE id = $2;
                    """,
                    latest_worn_at,
                    item_id,
                )

            return {"message": "OOTD log deleted successfully"}