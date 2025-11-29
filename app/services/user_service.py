# app/services/user_service.py
from fastapi import HTTPException

async def create_user_service(conn, user):
    try:
        sql = """
            INSERT INTO users (id, email)
            VALUES ($1, $2)
            ON CONFLICT (id) DO NOTHING
            RETURNING *;
        """
        row = await conn.fetchrow(sql, user.id, user.email)
        return dict(row) if row else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
