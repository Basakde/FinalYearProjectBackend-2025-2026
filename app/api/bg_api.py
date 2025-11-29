from fastapi import APIRouter, UploadFile, File,Request
from app.services.bg_service import remove_bg_service


router = APIRouter(prefix="/remove-bg")

@router.post("/")
async def remove_bg_api(request: Request, file: UploadFile = File(...)):
    session = request.app.state.bg_session
    result = await remove_bg_service(file, session)
    return {"processed_base64": result}
