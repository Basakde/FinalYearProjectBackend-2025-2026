# app/services/category_service.py
from fastapi import HTTPException

async def get_categories_service(pool):
    """Fetch all categories ordered by ID."""
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, name FROM categories ORDER BY id;"
            )
        return [dict(r) for r in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
