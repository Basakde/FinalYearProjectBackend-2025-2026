import os
import requests
from fastapi import HTTPException

OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")

async def get_weather_service(lat: float, lon: float):
    """Fetch temperature + icon from OpenWeather API."""

    if not OPENWEATHER_KEY:
        raise HTTPException(status_code=500, detail="Weather API key missing")

    url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat={lat}&lon={lon}&appid={OPENWEATHER_KEY}&units=metric"
    )

    try:
        response = requests.get(url)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to contact weather API")

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Weather API error")

    return response.json()