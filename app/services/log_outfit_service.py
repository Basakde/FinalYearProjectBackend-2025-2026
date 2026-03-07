from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, Optional, List
from fastapi import HTTPException
from datetime import date
import calendar


from app.services.outfit_service import create_outfit_service


async def log_outfit_service(pool, user_id: str, item_ids: List[str], outfit_id:str | None , name: Optional[str] = None, worn_at:Optional[str]=None) -> Dict[str, str]:
    async with pool.acquire() as conn:
        async with conn.transaction():
            print("LOG item_ids:", item_ids)

            if outfit_id:
                # reuse existing outfit
                used_outfit_id = outfit_id
            else:
                # create outfit if none exists
                used_outfit_id = await create_outfit_service(conn, user_id, item_ids, name)

            if worn_at:
                try:
                    used_worn_at = datetime.fromisoformat(worn_at)
                except Exception:
                    raise HTTPException(400, "Invalid worn_at format")
            else:
                used_worn_at = datetime.utcnow()

            row = await conn.fetchrow(
                """
                INSERT INTO outfit_wear_log (worn_at, outfit_id)
                VALUES ($1, $2)
                RETURNING id::text AS wear_log_id, outfit_id::text;
                """,
                used_worn_at,
                used_outfit_id,
            )

            await conn.execute(
                """
                UPDATE ClothingItems
                SET last_worn_at = $1
                WHERE id IN (
                    SELECT item_id
                    FROM OutfitItems
                    WHERE outfit_id = $2
                );
                """,
                used_worn_at,
                used_outfit_id
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
            SELECT (owl.worn_at)::date AS date,
                   COUNT(*)::int AS count
            FROM outfit_wear_log owl
            JOIN Outfits o ON o.id = owl.outfit_id
            WHERE o.user_id = $1::uuid
              AND (owl.worn_at)::date BETWEEN $2 AND $3
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
              AND (owl.worn_at)::date = $2

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
