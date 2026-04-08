from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Depends

from app.dependencies.auth import get_current_user
from app.services.user_service import delete_my_account_service, create_user_service
from app.services.virtual_try_on_image_service import (
    upload_tryon_image_service,
    get_tryon_image_service,
    delete_tryon_image_service,
)
router = APIRouter(prefix="/users", tags=["Consent"])

@router.post("/ensure-profile")
async def ensure_profile(
    request: Request,
    current_user=Depends(get_current_user),
):
    pool = request.app.state.db

    async with pool.acquire() as conn:
        user = await create_user_service(conn, current_user)

    if not user:
        raise HTTPException(status_code=500, detail="Failed to create user profile")

    return {"user": user}


@router.post("/{user_id}/tryon-image")
async def upload_user_tryon_image(
    user_id: str,
    request: Request,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")

    file_bytes = await file.read()

    async with request.app.state.db.acquire() as conn:
        return await upload_tryon_image_service(
            conn=conn,
            user_id=user_id,
            file_content_type=file.content_type,
            file_bytes=file_bytes,
        )


@router.get("/{user_id}/tryon-image")
async def get_user_tryon_image(
    user_id: str,
    request: Request,
    current_user=Depends(get_current_user),
):
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")

    async with request.app.state.db.acquire() as conn:
        return await get_tryon_image_service(conn, user_id)


@router.delete("/{user_id}/tryon-image")
async def delete_user_tryon_image(
    user_id: str,
    request: Request,
    current_user=Depends(get_current_user),
):
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")

    async with request.app.state.db.acquire() as conn:
        return await delete_tryon_image_service(conn, user_id)

@router.delete("/me")
async def delete_my_account(
    request: Request,
    current_user=Depends(get_current_user),
):
    pool = request.app.state.db
    user_id = str(current_user.id)

    await delete_my_account_service(pool, user_id)

    return {"message": "Account deleted"}