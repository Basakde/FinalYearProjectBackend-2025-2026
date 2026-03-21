from typing import Optional, List

from pydantic import BaseModel
from fastapi import APIRouter, Request, HTTPException

from app.services.outfit_service import create_outfit_service
from app.services.set_outfit_preference_service import set_outfit_preference_service

router = APIRouter(prefix="/preferences", tags=["Preferences"])

class PreferencePayload(BaseModel):
    user_id: str
    preference: str  # like/dislike
    outfit_id: Optional[str] = None
    item_ids: Optional[List[str]] = None
    master_occasion_id:Optional[str]=None

@router.post("/")
async def set_preference(payload: PreferencePayload, request: Request):
    pool = request.app.state.db

    async with pool.acquire() as conn:
        async with conn.transaction():

            if payload.outfit_id:
                used_outfit_id = payload.outfit_id
            else:
                if not payload.item_ids or len(payload.item_ids) < 2:
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