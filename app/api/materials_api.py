# app/api/attribute_api.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from app.services.materials_service import (
 get_materials_options_service,
)

router = APIRouter(prefix="/attributes", tags=["Attributes"])


class NameBody(BaseModel):
    name: str = Field(min_length=1, max_length=50)


@router.get("/materials/options")
async def get_material_options(request: Request):
    pool = request.app.state.db
    options = await get_materials_options_service(pool)
    return {"options": options}
