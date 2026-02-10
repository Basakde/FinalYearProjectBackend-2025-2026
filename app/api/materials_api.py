# app/api/attribute_api.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from app.services.materials_service import (
    list_user_materials_service,
    create_user_materials_service,
    rename_user_materials_service,
    set_user_materials_active_service,
    delete_user_materials_service, get_materials_options_service,
)

router = APIRouter(prefix="/attributes", tags=["Attributes"])


class NameBody(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class ActiveBody(BaseModel):
    is_active: bool


from fastapi import Query

@router.get("/materials/user/{user_id}")
async def list_user_materials(
    user_id: str,
    request: Request,
    active_only: bool = Query(False)
):
    pool = request.app.state.db
    return {"materials": await list_user_materials_service(pool, user_id, active_only)}



@router.post("/materials/user/{user_id}")
async def create_user_material(user_id: str, body: NameBody, request: Request):
    pool = request.app.state.db
    try:
        return {"material": await create_user_materials_service(pool, user_id, body.name)}
    except Exception as e:
        # unique(user_id,name) can throw
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/materials/{material_id}/rename")
async def rename_user_material(material_id: str, body: NameBody, request: Request):
    pool = request.app.state.db
    updated = await rename_user_materials_service(pool, material_id, body.name)
    if not updated:
        raise HTTPException(status_code=404, detail="material_id not found")
    return {"message": "material_id renamed"}


@router.patch("/materials/{material_id}/active")
async def set_user_material_active(material_id: str, body: ActiveBody, request: Request):
    pool = request.app.state.db
    updated = await set_user_materials_active_service(pool, material_id, body.is_active)
    if not updated:
        raise HTTPException(status_code=404, detail="material_id not found")
    return {"message": "material_id updated"}

@router.delete("/materials/{material_id}/user/{user_id}")
async def delete_user_material(material_id: str, user_id: str, request: Request):
    pool = request.app.state.db
    try:
        deleted = await delete_user_materials_service(pool, material_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="material_id not found")
        return {"message": "material_id deleted"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/materials/options/user/{user_id}")
async def get_material_options(user_id: str, request: Request, active_only: bool = True):
    pool = request.app.state.db
    options = await get_materials_options_service(pool, user_id, active_only=active_only)
    return {"options": options}
