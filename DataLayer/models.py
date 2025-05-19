from app import db
from sqlalchemy import CheckConstraint, ForeignKey, Integer, text, DateTime, Float, BigInteger, Enum
from sqlalchemy.orm import Mapped, declared_attr, class_mapper, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional
import json
from DataLayer.enums import RatingEnum, SegmentEnum

class Base(db.Model):
    '''
    Базовый класс для моделей
    '''
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'
    
    def to_dict(self) -> dict:
        """Универсальный метод для конвертации объекта SQLAlchemy в словарь"""
        columns = class_mapper(self.__class__).columns
        return {column.key: getattr(self, column.key) for column in columns}
    
    def to_json(self) -> str:
        """Конвертирует объект SQLAlchemy в JSON-строку"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

class Category(Base):
    __tablename__ = "categories"

    name: Mapped[str]
    share: Mapped[Optional[float]] = mapped_column(Float, CheckConstraint("share >= 0 AND share <= 100"), default=None)

    category_brand_placements: Mapped[list["CategoryBrandPlacement"]] = relationship(
        "CategoryBrandPlacement",
        back_populates="category",
        cascade="all, delete-orphan"
    )

class Brand(Base):
    __tablename__ = "brands"
    
    name: Mapped[str]
    rating: Mapped[RatingEnum] = mapped_column(Enum(RatingEnum), default=None, server_default=None)

    category_brand_placements: Mapped[list["CategoryBrandPlacement"]] = relationship(
        "CategoryBrandPlacement",
        back_populates="brand",
        cascade="all, delete-orphan"
    )

class CategoryBrandPlacement(Base):
    __tablename__ = "category_brand_placements"

    share: Mapped[Optional[float]] = mapped_column(Float, CheckConstraint("share >= 0 AND share <= 100"), default=None)

    # Категория
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="category_brand_placements"
    )

    # Бренд
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    brand: Mapped["Brand"] = relationship(
        "Brand",
        back_populates="category_brand_placements"
    )

    # Товары
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="category_brand_placement",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        """Конвертирует объект CategoryBrandPlacement в словарь, включая category."""
        data = super().to_dict()

        if self.category:
            data['category'] = self.category.to_dict()
        else:
            data['category'] = None

        if self.brand:
            data['brand'] = self.brand.to_dict()
        else:
            data['brand'] = None

        return data

class Product(Base):
    __tablename__ = "products"
    
    segment: Mapped[SegmentEnum] = mapped_column(default=SegmentEnum.NONE, server_default=text("'NONE'"))
    name: Mapped[str]
    barcode: Mapped[int] = mapped_column(BigInteger)
    SKU_rating: Mapped[RatingEnum] = mapped_column(default=None, server_default=None)

    length: Mapped[float]
    depth: Mapped[float]
    height: Mapped[float]
    weight: Mapped[float]
    price: Mapped[float]

    # Размещения товара на полках
    placed_products: Mapped[list["PlacedProduct"]] = relationship(
        "PlacedProduct",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    # Бренд товара 
    category_brand_placement_id: Mapped[int] = mapped_column(ForeignKey("category_brand_placements.id"))
    category_brand_placement: Mapped["CategoryBrandPlacement"] = relationship(
        "CategoryBrandPlacement",
        back_populates="products"
    )

    def to_dict(self) -> dict:
        """Конвертирует объект Product в словарь, включая category_brand_placement."""
        data = super().to_dict()

        if self.category_brand_placement:
            data['category_brand_placement'] = self.category_brand_placement.to_dict()
        else:
            data['category_brand_placement'] = None
            
        return data

class Shelf(Base):
    __tablename__ = "shelves"

    shelf_number: Mapped[int]
    length: Mapped[int]
    depth: Mapped[int]
    height: Mapped[int]
    max_weight: Mapped[int]

    # Размещённые на полке товары
    placed_products: Mapped[list["PlacedProduct"]] = relationship(
        "PlacedProduct",
        back_populates="shelf",
        cascade="all, delete-orphan"
    )

    # Указание на стеллаж
    shelf_unit_id: Mapped[int] = mapped_column(ForeignKey("shelf_units.id"))
    shelf_unit: Mapped["ShelfUnit"] = relationship(
        "ShelfUnit",
        back_populates="shelves"
    )

class PlacedProduct(Base):
    __tablename__ = "placed_products"

    # Указание на полку
    shelf_id: Mapped[int] = mapped_column(ForeignKey("shelves.id"))
    shelf: Mapped["Shelf"] = relationship(
        "Shelf",
        back_populates="placed_products"
    )

    # Указание на товар
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id")) 
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="placed_products"
    )

    # Указатель на планограмму
    planogram_id: Mapped[int] = mapped_column(ForeignKey("planograms.id"))
    planogram: Mapped["Planogram"] = relationship(
        "Planogram",
        back_populates="placed_products"
    )

    position: Mapped[int]

    def to_dict(self) -> dict:
        """Конвертирует объект PlacedProduct в словарь"""
        data = super().to_dict()

        if self.shelf:
            data['shelf'] = self.shelf.to_dict()
        else:
            data['shelf'] = None

        if self.product:
            data['product'] = self.product.to_dict()
        else:
            data['product'] = None
            
        return data

class ShelfUnit(Base):
    __tablename__ = "shelf_units"
    
    shelf_unit_number: Mapped[int]
    
    # Полки стеллажа
    shelves: Mapped[list["Shelf"]] = relationship(
        "Shelf",
        back_populates="shelf_unit",
        cascade="all, delete-orphan"
    )

    # Связь с планограммой
    planograms: Mapped[list["Planogram"]] = relationship(
        "Planogram",
        back_populates="shelf_unit",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        """Конвертирует объект Shelf в словарь"""
        data = super().to_dict()

        if self.shelves:
            data['shelves'] = [shelf.to_dict() for shelf in self.shelves]
        else:
            data['shelves'] = None
            
        return data

class Planogram(Base):
    name: Mapped[str]
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), default=func.now())

    # Указывает на стеллаж
    shelf_unit_id: Mapped[int] = mapped_column(ForeignKey("shelf_units.id"))
    shelf_unit: Mapped["ShelfUnit"] = relationship(
        "ShelfUnit",
        back_populates="planograms"
    )

    # Связь с PlacedProduct
    placed_products: Mapped[list["PlacedProduct"]] = relationship(
        "PlacedProduct",
        back_populates="planogram",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        """Конвертирует объект Planogram в словарь"""
        data = super().to_dict()

        if self.shelf_unit:
            data['shelf_unit'] = self.shelf_unit.to_dict()
        else:
            data['shelf_unit'] = None

        if self.placed_products:
            data['placed_products'] = [product.to_dict() for product in self.placed_products]
        else:
            data['placed_products'] = None
            
        return data