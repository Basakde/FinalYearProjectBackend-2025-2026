import os
from io import BytesIO
from typing import Optional

import requests
from fastapi import HTTPException
from google import genai
from google.genai import types
from PIL import Image

from app.helpers.user_image_helper import create_tryon_signed_url
from app.services.user_service import get_tryon_image_path_service


client = genai.Client(
    vertexai=True,
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
)


def load_image_from_url(url: str) -> Image.Image:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGB")


async def quick_try_on_service(conn, payload) -> dict:
    row = await get_tryon_image_path_service(conn, payload.user_id)

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    path = row.get("tryon_image_path")

    if not path:
        mannequin_url = os.getenv("DEFAULT_URL")
        if not mannequin_url:
            raise HTTPException(status_code=500, detail="DEFAULT_URL not configured")

        person_img = load_image_from_url(mannequin_url)
    else:
        signed_url = create_tryon_signed_url(path)
        person_img = load_image_from_url(signed_url)

    contents = [
        """
        Edit the FIRST image only.

        Task:
        - Replace the clothing on the person in the first image with the garments shown in the reference clothing images.
        - Preserve the exact same person identity, face, hair, skin tone, body shape, pose, camera angle, and framing from the first image.
        - Do not change the person.
        - Do not beautify, restyle, regenerate, or alter facial features.
        - Do not change hairstyle.
        - Do not change body proportions.
        - Keep the person in the exact same position.
        - Use the clothing reference images only to transfer the garments.
        - Output a photorealistic try-on result.
        - Plain light gray background for full image size.
        - No border.
        """,
        person_img
    ]

    if payload.outerwear_url:
        contents.append(load_image_from_url(payload.outerwear_url))
    if payload.top_url:
        contents.append(load_image_from_url(payload.top_url))
    if payload.jumpsuit_url:
        contents.append(load_image_from_url(payload.jumpsuit_url))
    if payload.bottom_url:
        contents.append(load_image_from_url(payload.bottom_url))
    if payload.shoes_url:
        contents.append(load_image_from_url(payload.shoes_url))

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="3:4",
                image_size="2K",
            ),
        ),
    )

    generated_image = None

    for part in response.parts:
        if getattr(part, "text", None):
            print("Model text:", part.text)

        img = part.as_image()
        if img is not None:
            generated_image = img
            break

    if generated_image is None:
        raise HTTPException(status_code=500, detail="No image returned by model")

    output_dir = "generated_tryons"
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{payload.user_id}_tryon.png"#model needs to be kept in the dir with that name to save it in disk
    output_path = os.path.join(output_dir, filename)
    generated_image.save(output_path)

    return {
        "success": True,
        "result_path": f"generated_tryons/{filename}",
    }