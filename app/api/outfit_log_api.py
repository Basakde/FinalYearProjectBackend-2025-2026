
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List

from app.dependencies.auth import get_current_user
from app.services.log_outfit_service import log_outfit_service, get_logged_outfits_month_service, \
    get_logged_outfits_day_service, delete_logged_outfit_service

router = APIRouter(prefix="/logged_outfits", tags=["Logged Outfits"])

class LogOutfitPayload(BaseModel):
    user_id: str
    outfit_id : Optional[str] = None
    top_id: Optional[str] = None
    bottom_id: Optional[str] = None
    shoes_id: Optional[str] = None
    outerwear_id: Optional[str] = None
    jumpsuit_id:Optional[str]=None
    accessory_id: Optional[str] = None
    name: Optional[str] = None
    worn_at:Optional[str] = None
    occasion_id:Optional[str] = None

@router.post("/")
async def log_outfit_api(request: Request, payload: LogOutfitPayload,current_user=Depends(get_current_user)):
    if str(payload.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Token user does not match payload user_id")
    pool = request.app.state.db

    # build item_ids array in correct order, skipping nulls
    item_ids: List[Optional[str]] = [
        payload.outerwear_id,  # 0
        payload.top_id,  # 1
        payload.bottom_id,  # 2
        payload.shoes_id,  # 3
        payload.jumpsuit_id,  # 4
        payload.accessory_id,  # 5
    ]

    real_item_ids = [x for x in item_ids if x]
    if len(real_item_ids) < 1:
        raise HTTPException(400, "Need at least 1 item to log an outfit")

    return await log_outfit_service(pool, payload.user_id,item_ids, payload.outfit_id,payload.occasion_id, payload.name,payload.worn_at)

@router.delete("/{wear_log_id}")
async def delete_logged_outfit(wear_log_id: str, user_id: str, request: Request, current_user=Depends(get_current_user)):
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")
    pool = request.app.state.db
    return await delete_logged_outfit_service(pool, user_id, wear_log_id)

# month marks for calendar icons
@router.get("/month")
async def get_logged_outfits_month(request: Request, user_id: str, month: str, current_user=Depends(get_current_user)):
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")
    pool = request.app.state.db
    return await get_logged_outfits_month_service(pool, user_id, month)


# day details for modal list
@router.get("/day")
async def get_logged_outfits_day(request: Request, user_id: str, date_str: str,  current_user=Depends(get_current_user)):
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")
    pool = request.app.state.db
    return await get_logged_outfits_day_service(pool, user_id, date_str)