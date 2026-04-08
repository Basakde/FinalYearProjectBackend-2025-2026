from fastapi import HTTPException
from app.helpers.vector_math import ema_update
from app.services.outfit_service import compute_and_store_outfit_vec

LIKE_ALPHA = 0.06
DISLIKE_ALPHA = 0.04

async def ensure_outfit_vec(conn, outfit_id: str) -> list[float]:
    row = await conn.fetchrow(
        "SELECT outfit_vec FROM Outfits WHERE id = $1::uuid",
        outfit_id
    )
    if not row:
        raise HTTPException(404, "Outfit not found")

    if row["outfit_vec"] is None:
        return await compute_and_store_outfit_vec(conn, outfit_id)

    return list(row["outfit_vec"])

async def update_user_style_ema(conn, user_id: str, outfit_vec: list[float], alpha: float, sign: int):
    row = await conn.fetchrow(
        "SELECT style_vec, style_signal_count FROM Users WHERE id = $1::uuid",
        user_id
    )
    if not row:
        raise HTTPException(404, "User not found")

    style_vec = list(row["style_vec"]) if row["style_vec"] is not None else [0.0] * len(outfit_vec)

    # reseting if mismatch
    if len(style_vec) != len(outfit_vec):
        style_vec = [0.0] * len(outfit_vec)

    new_style = ema_update(style_vec, outfit_vec, learning_rate=alpha, feedback_direction=sign)

    await conn.execute(
        "UPDATE Users SET style_vec = $2 WHERE id = $1::uuid",
        user_id,
        new_style,
    )

async def set_outfit_preference_service(conn, user_id: str, outfit_id: str, preference: str):
    if preference not in ("like", "dislike"):
        raise HTTPException(400, "preference must be 'like' or 'dislike'")


    prev = await conn.fetchrow(
        """
        SELECT preference
        FROM OutfitPreference
        WHERE user_id = $1::uuid AND outfit_id = $2::uuid
        """,
        user_id,
        outfit_id
    )
    prev_pref = prev["preference"] if prev else None

    # If user taps same preference again: do nothing
    if prev_pref == preference:
        return {"outfit_id": outfit_id, "preference": preference, "changed": False}

    # Ensure outfit vec exists
    outfit_vec = await ensure_outfit_vec(conn, outfit_id)

    # Apply EMA ONCE based on new preference
    if preference == "like":
        await update_user_style_ema(conn, user_id, outfit_vec, LIKE_ALPHA, sign=+1)
    else:
        await update_user_style_ema(conn, user_id, outfit_vec, DISLIKE_ALPHA, sign=-1)

    # Upsert preference record
    await conn.execute(
        """
        INSERT INTO OutfitPreference (user_id, outfit_id, preference)
        VALUES ($1::uuid, $2::uuid, $3)
        ON CONFLICT (user_id, outfit_id)
        DO UPDATE SET preference = EXCLUDED.preference, updated_at = now()
        """,
        user_id,
        outfit_id,
        preference
    )

    # only count when first time ever
    if prev_pref is None:
        await conn.execute(
            """
            UPDATE Users
            SET style_signal_count = COALESCE(style_signal_count, 0) + 1
            WHERE id = $1::uuid
            """,
            user_id
        )

    return {
        "outfit_id": outfit_id,
        "preference": preference,
        "changed": True,
        "from": prev_pref,
        "to": preference
    }