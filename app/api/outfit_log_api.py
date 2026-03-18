
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List

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
    name: Optional[str] = None
    worn_at:Optional[str] = None
    occasion_id:Optional[str] = None

@router.post("/")
async def log_outfit_api(request: Request, payload: LogOutfitPayload):
    pool = request.app.state.db

    # build item_ids array in correct order, skipping nulls
    item_ids: List[str] = [
        x for x in [payload.top_id, payload.bottom_id,payload.jumpsuit_id, payload.shoes_id, payload.outerwear_id] if x
    ]

    if len(item_ids) < 1:
        raise HTTPException(400, "Need at least 1 item to log an outfit")

    return await log_outfit_service(pool, payload.user_id,item_ids, payload.outfit_id,payload.occasion_id,  payload.name,payload.worn_at)

@router.delete("/{wear_log_id}")
async def delete_logged_outfit(wear_log_id: str, user_id: str, request: Request):
    pool = request.app.state.db
    return await delete_logged_outfit_service(pool, user_id, wear_log_id)

# month marks for calendar icons
@router.get("/month")
async def get_logged_outfits_month(request: Request, user_id: str, month: str):
    pool = request.app.state.db
    return await get_logged_outfits_month_service(pool, user_id, month)


# day details for modal list
@router.get("/day")
async def get_logged_outfits_day(request: Request, user_id: str, date_str: str):
    pool = request.app.state.db
    return await get_logged_outfits_day_service(pool, user_id, date_str)