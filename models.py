from pydantic import BaseModel
from typing import Optional

class ClothingItemCreate(BaseModel):
    user_id: str
    img_description: Optional[str] = None
    image_url: Optional[str] = None
    processed_img_url: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None

class UserCreate(BaseModel):
    id: str
    email: str
    user_img_url:Optional[str]=None