from pydantic import BaseModel
from typing import Optional
from DataLayer.enums import RatingEnum, SegmentEnum

class Brand(BaseModel):
    name: Optional[str] = None
    rating: Optional[RatingEnum] = None
    share: Optional[float] = None

class Category(BaseModel):
    name: Optional[str] = None
    share: Optional[float] = None

class Product(BaseModel):
    segment: Optional[SegmentEnum] = None
    product_name: Optional[str] = None
    barcode: Optional[int] = None
    SKU_rating: Optional[RatingEnum] = None
    length: Optional[float] = None
    depth: Optional[float] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None