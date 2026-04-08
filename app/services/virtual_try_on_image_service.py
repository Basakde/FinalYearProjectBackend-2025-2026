from fastapi import HTTPException

from app.config.supabase_client import supabase
from app.helpers.user_image_helper import (
    TRYON_BUCKET,
    build_tryon_path,
    convert_image_to_webp,
    create_tryon_signed_url,
)
from app.services.user_service import (
    get_user_by_id_service,
    get_tryon_image_path_service,
    update_tryon_image_path_service,
)


async def upload_tryon_image_service(conn, user_id: str, file_content_type: str | None, file_bytes: bytes):
    if not file_content_type or not file_content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed.")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file.")

    user_row = await get_user_by_id_service(conn, user_id)
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found.")

    webp_bytes = convert_image_to_webp(file_bytes)
    path = build_tryon_path(user_id)

    supabase.storage.from_(TRYON_BUCKET).upload(
        path=path,
        file=webp_bytes,
        file_options={
            "content-type": "image/webp",
            "upsert": "true",
        },
    )

    await update_tryon_image_path_service(conn, user_id, path)

    signed_url = create_tryon_signed_url(path)

    return {
        "message": "Try-on image uploaded successfully.",
        "tryon_image_path": path,
        "tryon_image_url": signed_url,
    }


async def get_tryon_image_service(conn, user_id: str):
    row = await get_tryon_image_path_service(conn, user_id)

    if not row:
        raise HTTPException(status_code=404, detail="User not found.")

    path = row.get("tryon_image_path")
    signed_url = create_tryon_signed_url(path) if path else None

    return {
        "tryon_image_path": path,
        "tryon_image_url": signed_url,
        "has_tryon_image": bool(path),
    }


async def delete_tryon_image_service(conn, user_id: str):
    row = await get_tryon_image_path_service(conn, user_id)

    if not row:
        raise HTTPException(status_code=404, detail="User not found.")

    path = row.get("tryon_image_path")

    await update_tryon_image_path_service(conn, user_id, None)

    if path:
        supabase.storage.from_(TRYON_BUCKET).remove([path])

    return {
        "message": "Try-on image removed.",
        "tryon_image_path": None,
        "tryon_image_url": None,
    }