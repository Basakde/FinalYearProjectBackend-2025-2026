# app/api/user_api.py
from fastapi import APIRouter, Request, HTTPException
from app.services.user_service import create_user_service
from app.models.user_model import UserCreate

router = APIRouter()

@router.post("/users")
async def create_user(user: UserCreate, request: Request):
    pool = request.app.state.db

    async with pool.acquire() as conn:
        created_user = await create_user_service(conn, user)
        return {
            "message": "User created",
            "user": created_user
        }
