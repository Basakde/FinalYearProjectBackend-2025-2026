# app/api/item_api.py

from fastapi import APIRouter, Request, HTTPException
from app.services.item_service import (
    get_item_by_id_service,
    get_items_by_user_service,
    create_item_service, delete_item_service, update_item_service,

)
from app.models.item_modal import ClothingItemCreate
router = APIRouter(prefix="/items", tags=["Items"])


# /items/{item_id}
@router.get("/{item_id}")
async def get_item_by_id(item_id: str, request: Request):
    pool = request.app.state.db
    result = await get_item_by_id_service(pool, item_id)
    return {"item": result}


# /items/user/{user_id}
@router.get("/user/{user_id}")
async def get_items_by_user(user_id: str, request: Request):
    pool = request.app.state.db
    items = await get_items_by_user_service(pool, user_id)
    return {"items": items}

@router.post("/")
async def create_item(item: ClothingItemCreate, request: Request):
    pool=request.app.state.db
    result = await create_item_service(pool,item)
    return result


@router.delete("/{item_id}")
async def delete_item(item_id: str, request: Request):
    pool = request.app.state.db
    await delete_item_service(pool, item_id)
    return {"message": "Item deleted"}


@router.patch("/{item_id}")
async def update_item(item_id: str, request: Request):
    pool = request.app.state.db
    data = await request.json()
    result = await update_item_service(pool, item_id, data)
    return result

