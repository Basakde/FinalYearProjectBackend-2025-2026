# app/services/bg_service.py
import base64
from io import BytesIO
from fastapi import HTTPException
from rembg import remove
from PIL import Image

async def remove_bg_bytes(image_data: bytes, session):
    try:
        input_image = Image.open(BytesIO(image_data)).convert("RGBA")
        out = remove(input_image, session=session)

        if isinstance(out, (bytes, bytearray)):
            output_image = Image.open(BytesIO(out)).convert("RGBA")
        else:
            output_image = out.convert("RGBA")

        MAX_W = 1000
        if output_image.width > MAX_W:
            ratio = MAX_W / output_image.width
            new_h = int(output_image.height * ratio)
            output_image = output_image.resize((MAX_W, new_h), Image.LANCZOS)

        buf = BytesIO()
        output_image.save(buf, format="WEBP", quality=75, method=6)

        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return {"b64": b64, "mime": "image/webp"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
