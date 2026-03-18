# app/api/attribute_api.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from app.services.occasions_service import ( get_occasions_options_service)
from fastapi import Query

router = APIRouter(prefix="/attributes", tags=["Attributes"])


@router.get("/occasions/options")
async def get_occasion_options(request: Request):
    pool = request.app.state.db
    options = await get_occasions_options_service(pool)
    return {"options": options}
