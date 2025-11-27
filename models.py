from pydantic import BaseModel
from typing import Optional, List


class ClothingItemCreate(BaseModel):
    user_id: str

    img_description: Optional[str] = None
    image_url: Optional[str] = None
    processed_img_url: Optional[str] = None
    category_id: Optional[int] = None
    subcategory: Optional[str] = None

    colors: List[str] = []
    materials: List[str] = []
    occasion: List[str] = []
    season: List[str] = []


class UserCreate(BaseModel):
    id: str
    email: str
    user_img_url:Optional[str]=None



class ItemUpdate(BaseModel):
    image_url: Optional[str] = None
    processed_img_url: Optional[str] = None
    category_id: Optional[int] = None
    subcategory: Optional[str] = None
    img_description: Optional[str] = None
    colors: Optional[List[str]]
    materials: Optional[List[str]]
    occasion: Optional[List[str]]
    season: Optional[List[str]]

