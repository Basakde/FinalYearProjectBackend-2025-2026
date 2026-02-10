# app/api/attribute_api.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from app.services.colors_service import (
    list_user_colors_service,
    create_user_color_service,
    rename_user_color_service,
    set_user_color_active_service,
    delete_user_color_service, get_color_options_service,
)

router = APIRouter(prefix="/attributes", tags=["Attributes"])


class NameBody(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class ActiveBody(BaseModel):
    is_active: bool


from fastapi import Query

@router.get("/colors/user/{user_id}")
async def list_user_colors(
    user_id: str,
    request: Request,
    active_only: bool = Query(False)
):
    pool = request.app.state.db
    return {"colors": await list_user_colors_service(pool, user_id, active_only)}



@router.post("/colors/user/{user_id}")
async def create_user_color(user_id: str, body: NameBody, request: Request):
    pool = request.app.state.db
    try:
        return {"color": await create_user_color_service(pool, user_id, body.name)}
    except Exception as e:
        # unique(user_id,name) can throw
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/colors/{color_id}/rename")
async def rename_user_color(color_id: str, body: NameBody, request: Request):
    pool = request.app.state.db
    updated = await rename_user_color_service(pool, color_id, body.name)
    if not updated:
        raise HTTPException(status_code=404, detail="Color not found")
    return {"message": "Color renamed"}


@router.patch("/colors/{color_id}/active")
async def set_user_color_active(color_id: str, body: ActiveBody, request: Request):
    pool = request.app.state.db
    updated = await set_user_color_active_service(pool, color_id, body.is_active)
    if not updated:
        raise HTTPException(status_code=404, detail="Color not found")
    return {"message": "Color updated"}

@router.delete("/colors/{color_id}/user/{user_id}")
async def delete_user_color(color_id: str, user_id: str, request: Request):
    pool = request.app.state.db
    try:
        deleted = await delete_user_color_service(pool, color_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Color not found")
        return {"message": "Color deleted"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/colors/options/user/{user_id}")
async def get_color_options(user_id: str, request: Request, active_only: bool = True):
    pool = request.app.state.db
    options = await get_color_options_service(pool, user_id, active_only=active_only)
    return {"options": options}
