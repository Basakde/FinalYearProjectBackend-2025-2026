# app/api/attribute_api.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from app.services.occasions_service import (
    list_user_occasions_service, get_occasions_options_service,create_user_occasions_service,set_user_occasions_active_service
)

router = APIRouter(prefix="/attributes", tags=["Attributes"])


class NameBody(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class ActiveBody(BaseModel):
    is_active: bool


from fastapi import Query

@router.get("/occasions/user/{user_id}")
async def list_user_occasions(
    user_id: str,
    request: Request,
    active_only: bool = Query(False)
):
    pool = request.app.state.db
    return {"occasions": await list_user_occasions_service(pool, user_id, active_only)}

@router.patch("/occasions/{occasion_id}/active")
async def set_user_occasion_active(occasion_id: str, body: ActiveBody, request: Request):
    pool = request.app.state.db
    updated = await set_user_occasions_active_service(pool, occasion_id, body.is_active)
    if not updated:
        raise HTTPException(status_code=404, detail="occasion_id not found")
    return {"message": "occasion_id updated"}

@router.post("/occasions/user/{user_id}")
async def create_user_occasion(user_id: str, body: NameBody, request: Request):
    pool = request.app.state.db
    try:
        return {"occasion": await create_user_occasions_service(pool, user_id, body.name)}
    except Exception as e:
        # unique(user_id,name) can throw
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/occasions/options/user/{user_id}")
async def get_occasion_options(user_id: str, request: Request, active_only: bool = True):
    pool = request.app.state.db
    options = await get_occasions_options_service(pool, user_id, active_only=active_only)
    return {"options": options}
