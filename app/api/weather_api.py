from fastapi import APIRouter
from app.services.weather_service import get_weather_service

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/")
async def get_weather_api(lat: float, lon: float):
    return await get_weather_service(lat, lon)
