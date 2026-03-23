# app/services/user_service.py
from fastapi import HTTPException

from app.helpers.vector_math import l2_normalize


async def create_user_service(conn, user):
    try:
        sql = """
            INSERT INTO users (id, email)
            VALUES ($1, $2)
            ON CONFLICT (id) DO NOTHING
            RETURNING *;
        """
        row = await conn.fetchrow(sql, user.id, user.email)

        if row:
            return dict(row)

        existing = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user.id
        )
        return dict(existing) if existing else None

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_user_by_id_service(conn, user_id: str):
    try:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
        return dict(row) if row else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_user_style_vec(pool, user_id: str) -> list[float] | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT style_vec FROM Users WHERE id = $1::uuid",
            user_id
        )
        if not row or row["style_vec"] is None:
            return None
        return l2_normalize([float(x) for x in row["style_vec"]])

async def update_tryon_image_path_service(conn, user_id: str, tryon_image_path: str | None):
    try:
        row = await conn.fetchrow(
            """
            UPDATE users
            SET tryon_image_path = $1
            WHERE id = $2
            RETURNING *;
            """,
            tryon_image_path,
            user_id
        )
        return dict(row) if row else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_tryon_image_path_service(conn, user_id: str):
    try:
        row = await conn.fetchrow(
            """
            SELECT tryon_image_path
            FROM users
            WHERE id = $1
            """,
            user_id
        )
        return dict(row) if row else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))