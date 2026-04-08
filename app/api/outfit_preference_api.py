from typing import Optional, List

from pydantic import BaseModel
from fastapi import APIRouter, Request, HTTPException, Depends

from app.dependencies.auth import get_current_user
from app.services.outfit_service import create_outfit_service
from app.services.set_outfit_preference_service import set_outfit_preference_service

router = APIRouter(prefix="/preferences", tags=["Preferences"])

class PreferencePayload(BaseModel):
    user_id: str
    preference: str  # like/dislike
    outfit_id: Optional[str] = None
    item_ids: list[Optional[str]]
    master_occasion_id:Optional[str]=None

@router.post("/")
async def set_preference(payload: PreferencePayload, request: Request,current_user=Depends(get_current_user)):
    if str(payload.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Token user does not match payload user_id")
    pool = request.app.state.db

    async with pool.acquire() as conn:
        async with conn.transaction():

            if payload.outfit_id:
                used_outfit_id = payload.outfit_id
            else:
                real_item_ids = [item_id for item_id in (payload.item_ids or []) if item_id]
                if  len(real_item_ids) < 2:
                    raise HTTPException(400, "Need outfit_id or item_ids (min 2)")
                used_outfit_id = await create_outfit_service(
                    conn,
                    payload.user_id,
                    payload.item_ids,
                    payload.master_occasion_id,
                    name=None,
                    is_favorite=False
                )

            return await set_outfit_preference_service(
                conn, payload.user_id, used_outfit_id, payload.preference
            )