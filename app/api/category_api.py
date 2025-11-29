# app/routes/category_api.py
from fastapi import APIRouter, Request
from app.services.category_service import get_categories_service

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/")
async def get_categories_api(request: Request):
    pool = request.app.state.db
    categories = await get_categories_service(pool)
    return {"categories": categories}
