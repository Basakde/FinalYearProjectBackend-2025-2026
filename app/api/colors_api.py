# app/api/attribute_api.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from app.services.colors_service import (
 get_color_options_service,
)

router = APIRouter(prefix="/attributes", tags=["Attributes"])


class NameBody(BaseModel):
    name: str = Field(min_length=1, max_length=50)


@router.get("/colors/options")
async def get_color_options( request: Request):
    pool = request.app.state.db
    options = await get_color_options_service(pool)
    return {"options": options}
