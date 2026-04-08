from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel

from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/consent", tags=["Consent"])


class ConsentPayload(BaseModel):
    gdpr_consent: bool


@router.get("/")
async def get_my_consent(
    request: Request,
    current_user=Depends(get_current_user),
):
    pool = request.app.state.db
    user_id = str(current_user.id)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            select gdpr_consent, gdpr_consent_at
            from users
            where id = $1
            """,
            user_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "gdpr_consent": row["gdpr_consent"],
        "gdpr_consent_at": row["gdpr_consent_at"]
    }


@router.patch("/")
async def update_my_consent(
    payload: ConsentPayload,
    request: Request,
    current_user=Depends(get_current_user),
):
    pool = request.app.state.db
    user_id = str(current_user.id)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            update users
            set gdpr_consent = $1,
                gdpr_consent_at = now()
            where id = $2
            returning gdpr_consent, gdpr_consent_at
            """,
            payload.gdpr_consent,
            user_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "message": "Consent updated",
        "gdpr_consent": row["gdpr_consent"],
        "gdpr_consent_at": row["gdpr_consent_at"],
    }