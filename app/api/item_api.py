# app/api/item_api.py

from fastapi import APIRouter, Request, HTTPException, Depends

from app.dependencies.auth import get_current_user
from app.services.item_service import (
    get_item_by_id_service,
    get_items_by_user_service,
    create_item_service, delete_item_service, update_item_service,

)
from app.models.item_modal import ClothingItemCreate
router = APIRouter(prefix="/items", tags=["Items"])


# /items/{item_id}
@router.get("/{item_id}")
async def get_item_by_id(item_id: str, request: Request,current_user=Depends(get_current_user),):
    pool = request.app.state.db
    result = await get_item_by_id_service(pool, item_id)

    if not result:
        raise HTTPException(status_code=404, detail="Item not found")

    if str(result["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed to access this item")
    return {"item": result}


# /items/user/{user_id}
@router.get("/user/{user_id}")
async def get_items_by_user(user_id: str, request: Request, current_user=Depends(get_current_user),):
    if str(current_user.id) != str(user_id):
        raise HTTPException(status_code=403, detail="Not allowed")

    pool = request.app.state.db
    items = await get_items_by_user_service(pool, str(current_user.id))
    return {"items": items}

@router.post("/")
async def create_item(item: ClothingItemCreate, request: Request, current_user=Depends(get_current_user)):
    if str(item.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Token user does not match payload user_id")
    pool=request.app.state.db
    result = await create_item_service(pool,item)
    return result


@router.delete("/{item_id}")
async def delete_item(item_id: str, request: Request, current_user=Depends(get_current_user),):
    pool = request.app.state.db
    existing = await get_item_by_id_service(pool, item_id) #find user first
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")

    if str(existing["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed to delete this item")

    await delete_item_service(pool, item_id)
    return {"message": "Item deleted"}


@router.patch("/{item_id}")
async def update_item(item_id: str, request: Request, current_user=Depends(get_current_user),):
    pool = request.app.state.db
    existing = await get_item_by_id_service(pool, item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")

    if str(existing["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed to update this item")

    data = await request.json()

    if "user_id" in data and str(data["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Cannot change user_id")

    result = await update_item_service(pool, item_id, data)
    return result

