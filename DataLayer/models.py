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

    def to_dict(self) -> dict:
        """Универсальный метод для конвертации объекта SQLAlchemy в словарь"""
        columns = class_mapper(self.__class__).columns
        return {column.key: getattr(self, column.key) for column in columns}

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

    def to_dict(self) -> dict:
        """Конвертирует объект PlacedProduct в словарь"""
        data = super().to_dict()

        # if self.shelf:
        #     data['shelf'] = self.shelf.to_dict()
        # else:
        #     data['shelf'] = None

        if self.product:
            data['product'] = self.product.to_dict()
        else:
            data['product'] = None
            
        return data

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

    def to_dict(self) -> dict:
        """Конвертирует объект Shelf в словарь"""
        data = super().to_dict()

        if self.shelves:
            data['shelves'] = [shelf.to_dict() for shelf in self.shelves]
        else:
            data['shelves'] = None
            
        return data

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

    rule: Mapped["Rule"] = relationship(
        "Rule",
        back_populates="planogram",
        cascade="all, delete-orphan",
        uselist=False
    )

    def to_dict(self) -> dict:
        """Конвертирует объект Planogram в словарь"""
        data = super().to_dict()

        if self.shelf_unit:
            data['shelf_unit'] = self.shelf_unit.to_dict()
        else:
            data['shelf_unit'] = None

        if self.rule:
            data['rule'] = self.rule.to_dict()
        else:
            data['rule'] = None

        if self.placed_products:
            data['placed_products'] = [product.to_dict() for product in self.placed_products]
        else:
            data['placed_products'] = None
            
        return data

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

    def to_dict(self) -> dict:
        """Конвертирует объект Rule в словарь"""
        return {
            "global_rules": {
                'brand_sort_by': self.brand_sorting,
                'product_sort_by': self.product_sorting,
                'spacing': self.spacing
            },
            'shelves_rules': [sr.to_dict() for sr in self.shelf_rules]
        }

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

    def to_dict(self) -> dict:
        """Конвертирует объект ShelfRule в словарь"""
        return {
            'shelf_id': self.shelf_id,
            'category_rules': [cr.to_dict() for cr in self.category_allocation_rules]
        }

class CategoryRule(Base):
    __tablename__ = "category_rules"
    share: Mapped[float] = mapped_column(Float, CheckConstraint("share >= 0 AND share <= 100"), default=0.0)
    min_weight: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    max_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    shelf_rule_id: Mapped[int] = mapped_column(ForeignKey("shelf_rules.id"))
    shelf_rule: Mapped["ShelfRule"] = relationship("ShelfRule", back_populates="category_allocation_rules")

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship("Category", back_populates="category_rules") 

    def to_dict(self) -> dict:
        """Конвертирует объект CategoryRule в словарь"""
        return {
            'category_id': self.category_id,
            'percentage': self.share,
            'min_weight': self.min_weight,
            'max_weight': self.max_weight,
            'category_name': self.category.name
        }