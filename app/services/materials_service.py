
from typing import Any, Dict, List
from fastapi import HTTPException
from app.utils.normalize import  display_label



async def get_materials_options_service(pool):
    """
    Returns merged list of color options: master (colors_meta)
    """
    try:
        async with pool.acquire() as conn:

            # 1) Fetch master colors
            sql = """
                SELECT id::text AS id, name
                FROM materials_master
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

