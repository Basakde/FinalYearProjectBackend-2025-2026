from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel

from app.dependencies.auth import get_current_user
from app.services.outfit_suggestions_service import get_outfit_suggestions_service

router = APIRouter(prefix="/outfitSuggestions", tags=["OutfitSuggestions"])

class SuggestionRequest(BaseModel):
    user_id: str
    lat: float
    lon: float
    master_occasion_id: Optional[str] = None

@router.post("/get_outfit_suggestions")
async def get_outfit_suggestions(payload: SuggestionRequest, request: Request,  current_user=Depends(get_current_user)):
    if str(payload.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Token user does not match payload user_id")
    pool = request.app.state.db
    try:
        return await get_outfit_suggestions_service(
            pool=pool,
            lat=payload.lat,
            lon=payload.lon,
            user_id=payload.user_id,
            occasion_id = payload.master_occasion_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
