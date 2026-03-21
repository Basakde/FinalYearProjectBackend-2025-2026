from fastapi import APIRouter, Request, HTTPException

from app.services.outfit_service import create_outfit_service, update_outfit_service, get_favorite_outfits_service

router = APIRouter(prefix="/outfits", tags=["Outfits"])

@router.post("/")
async def create_outfit_api(request: Request, payload: dict):
    pool = request.app.state.db

    user_id = payload.get("user_id")
    item_ids = payload.get("item_ids")
    name = payload.get("name")
    is_favorite = payload.get("is_favorite")
    master_occasion_id = payload.get("occasion_id")
    try:
        return {"outfit_id": await create_outfit_service(pool, user_id, item_ids, master_occasion_id, name, is_favorite)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/favorites")
async def get_favorite_outfit_api(request: Request, user_id: str):
    pool = request.app.state.db
    try:
        return await get_favorite_outfits_service(pool, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))