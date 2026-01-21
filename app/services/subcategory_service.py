from fastapi import HTTPException


async def get_subcategories_service(pool, user_id: str, category_id: int):
    try:
        async with pool.acquire() as con:
            rows = await con.fetch(
                """
                SELECT id, name, category_id
                FROM Subcategories
                WHERE user_id = $1 AND category_id = $2
                ORDER BY name;
                """,
                user_id,
                category_id,
            )

            return {
                "subcategories": [dict(r) for r in rows]
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def create_subcategory_service(pool, user_id: str, category_id: int, name: str):
    clean_name = (name or "").strip()

    if not clean_name:
        raise HTTPException(status_code=400, detail="Subcategory name is required")

    try:
        async with pool.acquire() as con:
            row = await con.fetchrow(
                """
                INSERT INTO Subcategories (user_id, category_id, name)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, category_id, name)
                DO UPDATE SET name = EXCLUDED.name
                RETURNING id, name, category_id;
                """,
                user_id,
                category_id,
                clean_name,
            )

            return {"subcategory": dict(row)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
