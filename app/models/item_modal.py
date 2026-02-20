from pydantic import BaseModel
from typing import Optional, List


class ClothingItemCreate(BaseModel):
    user_id: str
    img_description: Optional[str] = ""
    image_url: Optional[str] = None
    processed_img_url: Optional[str] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    in_laundry: bool = False
    last_worn_at:Optional[str] = None

    colors: List[str] = []
    materials: List[str] = []
    occasions: List[str] = []
    seasons: List[str] = []


class ItemUpdate(BaseModel):
    img_description: Optional[str] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    image_url: Optional[str] = None
    processed_img_url: Optional[str] = None
    in_laundry: Optional[bool] = None
    last_worn_at: Optional[str] = None

    colors: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    occasion: Optional[List[str]] = None
    season: Optional[List[str]] = None
