from fastapi import APIRouter, Request, HTTPException, Depends

from app.dependencies.auth import get_current_user
from app.services.outfit_service import create_outfit_service

router = APIRouter(prefix="/outfits", tags=["Outfits"])

@router.post("/")
async def create_outfit_api(request: Request, payload: dict,current_user=Depends(get_current_user),):
    pool = request.app.state.db

    user_id = payload.get("user_id")
    item_ids = payload.get("item_ids")
    name = payload.get("name")
    is_favorite = payload.get("is_favorite")
    master_occasion_id = payload.get("occasion_id")

    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Token user does not match payload user_id")
    try:
        return {"outfit_id": await create_outfit_service(pool, user_id, item_ids, master_occasion_id, name, is_favorite)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


