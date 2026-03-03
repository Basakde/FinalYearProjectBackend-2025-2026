from fastapi import APIRouter, UploadFile, File,Request

from app.services.bg_service import remove_bg_bytes

router = APIRouter(prefix="/remove-bg")



@router.post("/")
async def remove_bg_api(request: Request, file: UploadFile = File(...)):
    session = request.app.state.bg_session
    image_data = await file.read()
    result = await remove_bg_bytes(image_data, session)
    return result
