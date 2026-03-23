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


async def delete_subcategory_service(pool, user_id, subcategory_id):
    async with pool.acquire() as conn:
        count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM clothingitems
            WHERE user_id = $1 AND subcategory_id = $2
        """, user_id, subcategory_id)

        if count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"This subcategory is still used by {count} item(s). Move them first."
            )

        await conn.execute("""
            DELETE FROM subcategories
            WHERE id = $1 AND user_id = $2
        """, subcategory_id, user_id)

        return {"success": True}

async def get_all_user_subcategories_service(pool, user_id: str):
    try:
        async with pool.acquire() as conn:
            sql = """
                SELECT 
                    s.id,
                    s.name,
                    s.category_id,
                    c.name AS category_name,
                    COUNT(ci.id) AS item_count
                FROM subcategories s
                LEFT JOIN categories c
                    ON c.id = s.category_id
                LEFT JOIN clothingitems ci
                    ON ci.subcategory_id = s.id
                    AND ci.user_id = s.user_id
                WHERE s.user_id = $1
                GROUP BY s.id, s.name, s.category_id, c.name
                ORDER BY c.name, s.name
            """

            rows = await conn.fetch(sql, user_id)

            return {
                "subcategories": [dict(r) for r in rows]
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))