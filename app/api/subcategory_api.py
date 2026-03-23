# app/routes/category_api.py
from fastapi import APIRouter, Request, HTTPException, Depends

from app.dependencies.auth import get_current_user
from app.services.subcategory_service import (
    get_subcategories_service,
    create_subcategory_service, delete_subcategory_service, get_all_user_subcategories_service,
)

router = APIRouter(prefix="/subcategories", tags=["Subcategories"])

@router.get("/")
async def get_subcategories_api(
    request: Request,
    user_id: str,
    category_id: int,
    current_user=Depends(get_current_user),
):
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")
    pool = request.app.state.db
    return await get_subcategories_service(pool, user_id, category_id)

@router.get("/all")
async def get_all_user_subcategories_api(
    request: Request,
    user_id: str,
    current_user=Depends(get_current_user)
):
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")
    pool = request.app.state.db
    return await get_all_user_subcategories_service(pool, user_id)

@router.post("/create_subcategory")
async def create_subcategory_api(request: Request, payload: dict, current_user=Depends(get_current_user)):
    pool = request.app.state.db
    user_id = payload.get("user_id")
    category_id = payload.get("category_id")
    name = payload.get("name")

    if not user_id or not category_id or not name:
        raise HTTPException(status_code=400, detail="Missing required fields")
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Token user does not match payload user_id")

    return await create_subcategory_service(pool, user_id, category_id, name)
@router.delete("/{subcategory_id}")
async def delete_subcategory_api(
    request: Request,
    subcategory_id: int,
    user_id: str,
    current_user=Depends(get_current_user)
):

    if not subcategory_id or not user_id:
        raise HTTPException(status_code=400, detail="Missing required fields")
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")
    pool = request.app.state.db

    return await delete_subcategory_service(pool, user_id, subcategory_id)