from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    id: str
    email: str
    user_img_url: Optional[str] = None
