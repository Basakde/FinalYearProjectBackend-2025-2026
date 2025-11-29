from pydantic import BaseModel
from typing import Optional, List


class ClothingItemCreate(BaseModel):
    user_id: str
    img_description: Optional[str] = ""
    image_url: Optional[str] = None
    processed_img_url: Optional[str] = None
    category_id: Optional[int] = None
    subcategory: Optional[str] = ""

    colors: List[str] = []
    materials: List[str] = []
    occasion: List[str] = []
    season: List[str] = []


class ItemUpdate(BaseModel):
    img_description: Optional[str] = None
    category_id: Optional[int] = None
    subcategory: Optional[str] = None
    image_url: Optional[str] = None
    processed_img_url: Optional[str] = None

    colors: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    occasion: Optional[List[str]] = None
    season: Optional[List[str]] = None
