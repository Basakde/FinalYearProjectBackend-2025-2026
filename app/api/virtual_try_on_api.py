import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from app.dependencies.auth import get_current_user
from app.services.virtual_try_on_service import quick_try_on_service

load_dotenv()

router = APIRouter(prefix="/virtual_tryon", tags=["virtual_tryon"])


class QuickTryOnRequest(BaseModel):
    user_id: str
    top_url: Optional[str] = None
    bottom_url: Optional[str] = None
    shoes_url: Optional[str] = None
    outerwear_url: Optional[str] = None
    jumpsuit_url: Optional[str] = None
    outfit_type: Optional[str] = None


@router.post("/quick")
async def quick_try_on(
    request: Request,
    payload: QuickTryOnRequest,
    current_user=Depends(get_current_user),
):
    if str(payload.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Token user does not match payload user_id")

    try:
        async with request.app.state.db.acquire() as conn:
            return await quick_try_on_service(conn, payload)

    except HTTPException:
        raise
    except Exception as e:
        print("Quick try-on error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))