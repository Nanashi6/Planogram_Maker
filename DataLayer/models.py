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

    # Товары категории
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="category",
        cascade="all, delete-orphan"
    )

class Brand(Base):
    __tablename__ = "brands"
    
    name: Mapped[str]
    rating: Mapped[RatingEnum] = mapped_column(Enum(RatingEnum), default=None, server_default=None)
    share: Mapped[Optional[float]] = mapped_column(Float, CheckConstraint("share >= 0 AND share <= 100"), default=None)

    # Товары бренда
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="brand",
        cascade="all, delete-orphan"
    )

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

    # Категория товара
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="products"
    )

    # Бренд товара 
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    brand: Mapped["Brand"] = relationship(
        "Brand",
        back_populates="products"
    )

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