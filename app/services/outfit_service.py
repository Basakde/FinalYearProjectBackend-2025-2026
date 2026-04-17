from typing import Optional
from fastapi import HTTPException

from app.services.favorite_items_helper import apply_favorite_to_user_style
from app.helpers.vector_math import l2_normalize


async def create_outfit_service(conn, user_id: str,item_ids: list[Optional[str]], master_occasion_id: Optional[str] = None, name: Optional[str] = None, is_favorite:bool = False) -> str:
    if not user_id or not isinstance(item_ids, list) or len(item_ids) < 2:
        raise HTTPException(400, "user_id and item_ids (min 2) required")
            # 1) create outfit
    outfit_row = await conn.fetchrow(
        """
        INSERT INTO Outfits (user_id, master_occasion_id, name, is_favorite, favorited_at)
        VALUES ($1, $2, $3, $4 , CASE WHEN $4 THEN NOW() ELSE NULL END )
        RETURNING id;
        """,
        user_id, master_occasion_id, name,is_favorite
    )
    outfit_id = outfit_row["id"]

    # 2) link outfit items
    for pos, item_id in enumerate(item_ids):
        if not item_id:
            continue
        await conn.execute(
            """
            INSERT INTO OutfitItems (outfit_id, item_id, position)
            VALUES ($1, $2, $3)
            ON CONFLICT DO NOTHING;
            """,
            outfit_id, item_id, pos
        )

        #  only compute when we actually favorite on creation
    if is_favorite:
        outfit_vec = await compute_and_store_outfit_vec(conn, outfit_id)
        await apply_favorite_to_user_style(conn, user_id, outfit_vec)

    return str(outfit_id)

async def update_outfit_service(conn, user_id: str, outfit_id: str):
    # 1) Check current state to prevent double counting
    row = await conn.fetchrow(
        """
        SELECT is_favorite, outfit_vec
        FROM Outfits
        WHERE id = $1::uuid AND user_id = $2::uuid
        """,
        outfit_id,
        user_id,
    )
    if not row:
        raise HTTPException(404, "Outfit not found")

    if row["is_favorite"]:
        return {"outfit_id": outfit_id, "already_favorite": True}

    await conn.execute(
        """
        UPDATE Outfits
        SET is_favorite = TRUE, favorited_at = NOW()
        WHERE id = $1::uuid AND user_id = $2::uuid
        """,
        outfit_id,
        user_id,
    )

    if row["outfit_vec"] is None:
        outfit_vec = await compute_and_store_outfit_vec(conn, outfit_id)
    else:
        outfit_vec = list(row["outfit_vec"])

    await apply_favorite_to_user_style(conn, user_id, outfit_vec)

    return {"outfit_id": outfit_id, "favorited": True}


async def compute_and_store_outfit_vec(conn, outfit_id: str) -> list[float]:
    rows = await conn.fetch(
        """
        SELECT ci.attr_vector
        FROM OutfitItems oi
        JOIN ClothingItems ci ON ci.id = oi.item_id
        WHERE oi.outfit_id = $1::uuid
        ORDER BY oi.position ASC;
        """,
        outfit_id,
    )

    vecs = [l2_normalize(list(r["attr_vector"])) for r in rows if r["attr_vector"] is not None]
    if len(vecs) < 2:
        raise HTTPException(400, "Outfit needs at least 2 item vectors")

    L = len(vecs[0])
    if any(len(v) != L for v in vecs):
        raise HTTPException(500, "Vector length mismatch")

    n = len(vecs)
    sums = [0.0] * L
    for v in vecs:
        for i, x in enumerate(v):
            sums[i] += float(x)

    outfit_vec = [s / n for s in sums]
    outfit_vec = l2_normalize(outfit_vec)

    await conn.execute(
        """
        UPDATE Outfits
        SET outfit_vec = $2
        WHERE id = $1::uuid;
        """,
        outfit_id,
        outfit_vec,
    )

    return outfit_vec


async def get_favorite_outfits_service(pool, user_id: str):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
              o.id::text AS outfit_id,
              o.name AS outfit_name,
              o.master_occasion_id::text AS master_occasion_id,
              om.name AS occasion_name,
              COALESCE(
                json_agg(
                  json_build_object(
                    'item_id', ci.id::text,
                    'image_url', ci.image_url,
                    'position', oi.position
                  )
                  ORDER BY oi.position
                ) FILTER (WHERE ci.id IS NOT NULL),
                '[]'::json
              ) AS items
            FROM Outfits o
            LEFT JOIN occasions_master om ON om.id = o.master_occasion_id
            LEFT JOIN OutfitItems oi ON oi.outfit_id = o.id
            LEFT JOIN ClothingItems ci ON ci.id = oi.item_id
            WHERE o.user_id = $1
              AND o.is_favorite = TRUE
            GROUP BY o.id, o.name, o.master_occasion_id, om.name
            ORDER BY o.created_at DESC;
            """,
            user_id,
        )
        return {"outfits": [dict(r) for r in rows]}


async def delete_favorite_outfit_service(pool, outfit_id, user_id):
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE Outfits
                SET is_favorite = FALSE,
                    favorited_at = NULL
                WHERE id = $1::uuid
                  AND user_id = $2::uuid
                """,
                outfit_id,
                user_id,
            )

            return {"outfit_id": outfit_id, "unfavorited": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))