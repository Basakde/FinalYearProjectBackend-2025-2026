from fastapi import APIRouter, Request, HTTPException, UploadFile, File


import io
from PIL import Image, ImageOps
from app.config.supabase_client import supabase

router = APIRouter()


# Private bucket for try-on/profile body images
TRYON_BUCKET = "virtual_tryon_gallery"


def build_tryon_path(user_id: str) -> str:
    # One fixed file path per user
    # This makes replacement simple
    return f"{user_id}/tryon.webp"


def convert_image_to_webp(file_bytes: bytes) -> bytes:
    """
    Convert uploaded image bytes into WebP bytes.
    We do this to reduce file size and keep format consistent with the other images.
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))

        # Fix orientation using EXIF before saving
        img = ImageOps.exif_transpose(img)

        # Convert safely for WEBP
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        output = io.BytesIO()
        img.save(output, format="WEBP", quality=95)
        output.seek(0)
        return output.read()

    except Exception as e:
        raise ValueError(f"Could not process image: {str(e)}")


def create_tryon_signed_url(path: str, expires_in: int = 3600) -> str | None:
    """
    Create a temporary signed URL for a private bucket image.
    This lets the frontend view the image safely.
    """
    if not path:
        return None

    result = supabase.storage.from_(TRYON_BUCKET).create_signed_url(path, expires_in)
    return result.get("signedURL") or result.get("signedUrl")





