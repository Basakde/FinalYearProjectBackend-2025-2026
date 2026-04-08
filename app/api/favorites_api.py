from pydantic import BaseModel
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Depends
from app.dependencies.auth import get_current_user
from app.services.outfit_service import create_outfit_service, update_outfit_service, delete_favorite_outfit_service, \
    get_favorite_outfits_service

router = APIRouter(prefix="/favorites", tags=["Favorites"])

class FavoritePayload(BaseModel):
    outfit_id: Optional[str] = None
    item_ids: list[Optional[str]]
    master_occasion_id: Optional[str] = None
    name: Optional[str] = None


@router.post("/")
async def favorite_outfit(request: Request, payload: FavoritePayload, current_user=Depends(get_current_user)):
    pool = request.app.state.db
    user_id = str(current_user.id)

    async with pool.acquire() as conn:
        async with conn.transaction():
            # 1) ensure outfit exists
            if payload.outfit_id:
                used_outfit_id = payload.outfit_id
            else:
                real_item_ids = [item_id for item_id in (payload.item_ids or []) if item_id]
                if len(real_item_ids) < 2:
                    raise HTTPException(400, "Need outfit_id or item_ids (min 2)")
                used_outfit_id = await create_outfit_service(
                    conn, user_id, payload.item_ids, payload.master_occasion_id, payload.name, is_favorite=False
                )

            # 2) mark as favorite + apply style vec ONCE
            result = await update_outfit_service(conn, user_id, used_outfit_id)
            return {"outfit_id": used_outfit_id, **result}


@router.delete("/{outfit_id}/favorite")
async def unfavorite_outfit_api(request: Request, outfit_id: str, current_user=Depends(get_current_user)):
    pool = request.app.state.db
    user_id = str(current_user.id)

    await delete_favorite_outfit_service(pool,outfit_id, user_id)
    return {"message": "Outfit deleted"}



@router.get("/user/{user_id}")
async def get_favorite_outfit_api(request: Request, user_id: str, current_user=Depends(get_current_user),):
    pool = request.app.state.db

    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")
    try:
        return await get_favorite_outfits_service(pool, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
