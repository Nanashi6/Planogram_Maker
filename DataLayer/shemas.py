from pydantic import BaseModel
from typing import Optional
from DataLayer.enums import RatingEnum

class Brand(BaseModel):
    name: Optional[str] = None
    rating: Optional[RatingEnum] = None
    share: Optional[float] = None

class Category(BaseModel):
    name: Optional[str] = None
    share: Optional[float] = None