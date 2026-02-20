from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from app.services.outfit_suggestions_service import get_outfit_suggestions_service

router = APIRouter(prefix="/outfitSuggestions", tags=["OutfitSuggestions"])

class SuggestionRequest(BaseModel):
    user_id: str
    lat: float
    lon: float
    occasion_id: Optional[str] = None

@router.post("/get_outfit_suggestions")
async def get_outfit_suggestions(payload: SuggestionRequest, request: Request):
    pool = request.app.state.db
    try:
        return await get_outfit_suggestions_service(
            pool=pool,
            lat=payload.lat,
            lon=payload.lon,
            user_id=payload.user_id,
            occasion_id = payload.occasion_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
