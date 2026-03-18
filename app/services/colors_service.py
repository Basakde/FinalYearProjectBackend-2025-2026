
from typing import Any, Dict, List
from fastapi import HTTPException
from app.utils.normalize import  display_label


async def get_color_options_service(pool):
    """
    Returns color options directly from colors_master.
    """
    try:
        async with pool.acquire() as conn:
            sql = """
                SELECT id::text AS id, name
                FROM colors_master
            """

            sql += " ORDER BY COALESCE(sort_order, 9999), name ASC"

            rows = await conn.fetch(sql)

            return [
                {
                    "id": r["id"],
                    "name": display_label(r["name"]),
                }
                for r in rows
            ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))