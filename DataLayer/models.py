from app import db
from sqlalchemy import CheckConstraint, ForeignKey, Integer, text, DateTime, Float, BigInteger, Enum
from sqlalchemy.orm import Mapped, declared_attr, class_mapper, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List
import json
from DataLayer.enums import BrandSorting, ProductSorting, RatingEnum, SegmentEnum

class Base(db.Model):
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    def to_dict(self, exclude_relations: Optional[List[str]] = None) -> dict:
        """Универсальный метод для конвертации объекта SQLAlchemy в словарь, исключая указанные отношения для предотвращения рекурсии."""
        if exclude_relations is None:
            exclude_relations = []

        data = {}
        for column in class_mapper(self.__class__).columns:
            data[column.key] = getattr(self, column.key)

        for rel_name, rel_obj in class_mapper(self.__class__).relationships.items():
            if rel_name not in exclude_relations:
                value = getattr(self, rel_name)
                if value is None:
                    data[rel_name] = None
                elif isinstance(value, list):
                    child_exclude = [rel_obj.back_populates] if rel_obj.back_populates else []
                    data[rel_name] = [item.to_dict(exclude_relations=child_exclude) for item in value]
                else:
                    child_exclude = [rel_obj.back_populates] if rel_obj.back_populates else []
                    data[rel_name] = value.to_dict(exclude_relations=child_exclude)
            # else:
            #     value = getattr(self, rel_name)
            #     if value is not None:
            #         fk_columns = list(rel_obj.local_columns)
            #         if fk_columns:
            #              # Попробуем получить значение FK, если это простое поле
            #             try:
            #                 data[rel_name + "_id"] = getattr(self, fk_columns[0].name)
            #             except AttributeError:
            #                 pass # Не удалось получить FK


        return data

    def to_json(self, exclude_relations: Optional[List[str]] = None) -> str:
        return json.dumps(self.to_dict(exclude_relations=exclude_relations), ensure_ascii=False, default=str) # default=str для Enum и DateTime

class Category(Base):
    __tablename__ = "categories"
    name: Mapped[str]

    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="category",
        cascade="all, delete-orphan"
    )

    category_rules: Mapped[List["CategoryRule"]] = relationship(
        "CategoryRule",
        back_populates="category",
        cascade="all, delete-orphan"
    )

class Brand(Base):
    __tablename__ = "brands"
    name: Mapped[str]
    rating: Mapped[Optional[RatingEnum]] = mapped_column(Enum(RatingEnum), nullable=True)

    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="brand",
        cascade="all, delete-orphan"
    )

class Product(Base):
    __tablename__ = "products"
    segment: Mapped[SegmentEnum] = mapped_column(Enum(SegmentEnum), default=SegmentEnum.NONE, server_default=text(f"'{SegmentEnum.NONE.value}'"))
    name: Mapped[str]
    barcode: Mapped[int] = mapped_column(BigInteger, nullable=False)
    SKU_rating: Mapped[RatingEnum] = mapped_column(Enum(RatingEnum), nullable=False)

    length: Mapped[float]
    depth: Mapped[float]
    height: Mapped[float]
    weight: Mapped[float]
    price: Mapped[float]

    placed_products: Mapped[List["PlacedProduct"]] = relationship(
        "PlacedProduct",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    brand: Mapped["Brand"] = relationship("Brand", back_populates="products")

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship("Category", back_populates="products")

class Shelf(Base):
    __tablename__ = "shelves"
    shelf_number: Mapped[int]
    length: Mapped[float]
    depth: Mapped[float]
    height: Mapped[float]
    max_weight: Mapped[float]

    placed_products: Mapped[List["PlacedProduct"]] = relationship(
        "PlacedProduct",
        back_populates="shelf",
        cascade="all, delete-orphan"
    )

    shelf_unit_id: Mapped[int] = mapped_column(ForeignKey("shelf_units.id"))
    shelf_unit: Mapped["ShelfUnit"] = relationship("ShelfUnit", back_populates="shelves")

    shelf_rules: Mapped[List["ShelfRule"]] = relationship( 
        "ShelfRule",
        back_populates="shelf",
        cascade="all, delete-orphan"
    )

class PlacedProduct(Base):
    __tablename__ = "placed_products"
    shelf_id: Mapped[int] = mapped_column(ForeignKey("shelves.id"))
    shelf: Mapped["Shelf"] = relationship("Shelf", back_populates="placed_products")

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product: Mapped["Product"] = relationship("Product", back_populates="placed_products")

    planogram_id: Mapped[int] = mapped_column(ForeignKey("planograms.id"))
    planogram: Mapped["Planogram"] = relationship("Planogram", back_populates="placed_products")

    position: Mapped[int]

class ShelfUnit(Base):
    __tablename__ = "shelf_units"
    shelf_unit_number: Mapped[int]

    shelves: Mapped[List["Shelf"]] = relationship(
        "Shelf",
        back_populates="shelf_unit",
        cascade="all, delete-orphan",
        order_by="Shelf.shelf_number"
    )

    planograms: Mapped[List["Planogram"]] = relationship(
        "Planogram",
        back_populates="shelf_unit",
        cascade="all, delete-orphan"
    )

    def get_shelf_by_number(self, shelf_number: int) -> Optional["Shelf"]:
        for shelf_obj in self.shelves:
            if shelf_obj.shelf_number == shelf_number:
                return shelf_obj
        return None

class Planogram(Base):
    __tablename__ = "planograms"
    name: Mapped[str]
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), default=func.now())

    shelf_unit_id: Mapped[int] = mapped_column(ForeignKey("shelf_units.id"))
    shelf_unit: Mapped["ShelfUnit"] = relationship("ShelfUnit", back_populates="planograms")

    placed_products: Mapped[List["PlacedProduct"]] = relationship(
        "PlacedProduct",
        back_populates="planogram",
        cascade="all, delete-orphan"
    )

    rule: Mapped[Optional["Rule"]] = relationship(
        "Rule",
        back_populates="planogram",
        cascade="all, delete-orphan",
        uselist=False
    )

class Rule(Base):
    __tablename__ = "rules"
    brand_sorting: Mapped[BrandSorting] = mapped_column(Enum(BrandSorting), nullable=False)
    product_sorting: Mapped[ProductSorting] = mapped_column(Enum(ProductSorting), nullable=False)
    spacing: Mapped[float] = mapped_column(Float, default=0.5)

    shelf_rules: Mapped[List["ShelfRule"]] = relationship(
        "ShelfRule",
        back_populates="rule",
        cascade="all, delete-orphan"
    )

    planogram_id: Mapped[int] = mapped_column(ForeignKey("planograms.id"), unique=True, nullable=False)
    planogram: Mapped["Planogram"] = relationship("Planogram", back_populates="rule")


class ShelfRule(Base):
    __tablename__ = "shelf_rules"

    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id"))
    rule: Mapped["Rule"] = relationship("Rule", back_populates="shelf_rules")

    shelf_id: Mapped[int] = mapped_column(ForeignKey("shelves.id"))
    shelf: Mapped["Shelf"] = relationship("Shelf", back_populates="shelf_rules") 

    category_allocation_rules: Mapped[List["CategoryRule"]] = relationship( 
        "CategoryRule",
        back_populates="shelf_rule",
        cascade="all, delete-orphan"
    )

class CategoryRule(Base):
    __tablename__ = "category_rules"
    share: Mapped[float] = mapped_column(Float, CheckConstraint("share >= 0 AND share <= 100"), default=0.0)
    min_weight: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    max_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    shelf_rule_id: Mapped[int] = mapped_column(ForeignKey("shelf_rules.id"))
    shelf_rule: Mapped["ShelfRule"] = relationship("ShelfRule", back_populates="category_allocation_rules")

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship("Category", back_populates="category_rules") 