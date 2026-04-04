from fastapi import HTTPException
from app.helpers.vector_math import ema_update

FAV_ALPHA = 0.08  

async def apply_favorite_to_user_style(conn, user_id: str, outfit_vec: list[float]) -> None:
    row = await conn.fetchrow(
        """
        SELECT style_vec, style_signal_count
        FROM Users
        WHERE id = $1::uuid
        """,
        user_id,
    )
    if not row:
        raise HTTPException(404, "User not found")

    if row["style_vec"] is None:
        style_vec = [0.0] * len(outfit_vec)
        count = 0
    else:
        style_vec = list(row["style_vec"])
        count = int(row["style_signal_count"] or 0)
        if len(style_vec) != len(outfit_vec):
            style_vec = [0.0] * len(outfit_vec)
            count = 0

    new_style = ema_update(style_vec, outfit_vec, learning_rate=FAV_ALPHA, feedback_direction=+1)
    new_count = count + 1

    await conn.execute(
        """
        UPDATE Users
        SET style_vec = $2, style_signal_count = $3
        WHERE id = $1::uuid
        """,
        user_id,
        new_style,
        new_count,
    )