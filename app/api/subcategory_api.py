# app/routes/category_api.py
from fastapi import APIRouter, Request, HTTPException
from app.services.subcategory_service import (
    get_subcategories_service,
    create_subcategory_service,
)

router = APIRouter(prefix="/subcategories", tags=["Subcategories"])

@router.get("/")
async def get_subcategories_api(
    request: Request,
    user_id: str,
    category_id: int,
):
    pool = request.app.state.db
    return await get_subcategories_service(pool, user_id, category_id)


@router.post("/")
async def create_subcategory_api(request: Request, payload: dict):
    pool = request.app.state.db

    user_id = payload.get("user_id")
    category_id = payload.get("category_id")
    name = payload.get("name")

    if not user_id or not category_id or not name:
        raise HTTPException(status_code=400, detail="Missing required fields")

    return await create_subcategory_service(pool, user_id, category_id, name)