from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Depends

from app.dependencies.auth import get_current_user
from app.services.virtual_tryon_service import (
    upload_tryon_image_service,
    get_tryon_image_service,
    delete_tryon_image_service,
)

router = APIRouter()


@router.post("/users/{user_id}/tryon-image")
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


@router.get("/users/{user_id}/tryon-image")
async def get_user_tryon_image(
    user_id: str,
    request: Request,
    current_user=Depends(get_current_user),
):
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")

    async with request.app.state.db.acquire() as conn:
        return await get_tryon_image_service(conn, user_id)


@router.delete("/users/{user_id}/tryon-image")
async def delete_user_tryon_image(
    user_id: str,
    request: Request,
    current_user=Depends(get_current_user),
):
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed")

    async with request.app.state.db.acquire() as conn:
        return await delete_tryon_image_service(conn, user_id)