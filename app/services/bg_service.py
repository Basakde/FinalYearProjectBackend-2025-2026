# app/services/bg_service.py

import base64
from io import BytesIO
from fastapi import HTTPException, UploadFile
from rembg import remove
from PIL import Image

async def remove_bg_service(file: UploadFile, session):
    try:
        # Read uploaded file bytes
        image_data = await file.read()

        # Load it
        input_image = Image.open(BytesIO(image_data))

        # Remove background using preloaded u2net session
        output_image = remove(input_image, session=session)

        # Convert result to base64
        buffer = BytesIO()
        output_image.save(buffer, format="PNG")
        processed_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return processed_b64

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
