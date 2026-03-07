from pydantic import BaseModel
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException

from app.services.outfit_service import create_outfit_service, update_outfit_service, delete_favorite_outfit_service

router = APIRouter(prefix="/favorites", tags=["Favorites"])

class FavoritePayload(BaseModel):
    user_id: str
    outfit_id: Optional[str] = None
    item_ids: Optional[List[str]] = None
    name: Optional[str] = None

@router.post("/")
async def favorite_outfit(request: Request, payload: FavoritePayload):
    pool = request.app.state.db

    async with pool.acquire() as conn:
        async with conn.transaction():
            # 1) ensure outfit exists
            if payload.outfit_id:
                used_outfit_id = payload.outfit_id
            else:
                if not payload.item_ids or len(payload.item_ids) < 2:
                    raise HTTPException(400, "Need outfit_id or item_ids (min 2)")
                used_outfit_id = await create_outfit_service(
                    conn, payload.user_id, payload.item_ids, payload.name, is_favorite=False
                )

            # 2) mark as favorite + apply style vec ONCE
            result = await update_outfit_service(conn, payload.user_id, used_outfit_id)
            return {"outfit_id": used_outfit_id, **result}


@router.delete("/{outfit_id}/favorite")
async def unfavorite_outfit_api(request: Request, outfit_id: str, user_id: str):
    pool = request.app.state.db
    await delete_favorite_outfit_service(pool,outfit_id, user_id)
    return {"message": "Outfit deleted"}




