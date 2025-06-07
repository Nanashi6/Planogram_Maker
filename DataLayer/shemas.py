from pydantic import BaseModel
from typing import List, Optional
from DataLayer.enums import BrandSorting, ProductSorting, RatingEnum, SegmentEnum
from datetime import datetime

class OrmBaseModel(BaseModel):
    id: Optional[int] = None

    class Config:
        orm_mode = True

class Category(OrmBaseModel):
    name: Optional[str] = None

class Brand(OrmBaseModel):
    name: Optional[str] = None
    rating: Optional[RatingEnum] = None

class Product(OrmBaseModel):
    segment: Optional[SegmentEnum] = None
    name: Optional[str] = None
    barcode: Optional[int] = None
    SKU_rating: Optional[RatingEnum] = None
    length: Optional[float] = None
    depth: Optional[float] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None

class Shelf(OrmBaseModel):
    shelf_number: Optional[int] = None
    length: Optional[float] = None
    depth: Optional[float] = None
    height: Optional[float] = None
    max_weight: Optional[float] = None
    shelf_unit_id: Optional[int] = None

class ShelfUnit(OrmBaseModel):
    shelf_unit_number: Optional[int] = None

class Planogram(OrmBaseModel):
    name: Optional[str] = None
    created_at: Optional[datetime] = None 
    shelf_unit_id: Optional[int] = None

class PlacedProduct(OrmBaseModel):
    shelf_id: Optional[int] = None
    product_id: Optional[int] = None
    planogram_id: Optional[int] = None
    position: Optional[int] = None

class CategoryRule(OrmBaseModel):
    share: Optional[float] = None 
    min_weight: Optional[float] = None 
    max_weight: Optional[float] = None
    shelf_rule_id: Optional[int] = None
    category_id: Optional[int] = None

class ShelfRule(OrmBaseModel):
    rule_id: Optional[int] = None
    shelf_id: Optional[int] = None

class Rule(OrmBaseModel):
    brand_sorting: Optional[BrandSorting] = None
    product_sorting: Optional[ProductSorting] = None
    spacing: Optional[float] = None
    planogram_id: Optional[int] = None