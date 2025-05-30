from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel
from sqlalchemy import ColumnElement, Integer, delete, literal_column, select, union_all, update
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import select, and_, or_, case, asc, desc
from sqlalchemy.orm import joinedload

from DataLayer.enums import SegmentEnum
from DataLayer.models import Base, Category, Brand, Product, PlacedProduct, Shelf, ShelfUnit, Planogram, CategoryBrandPlacement
from app import db
from flask_sqlalchemy.pagination import Pagination

T = TypeVar("T", bound=Base)

class BaseDAO(Generic[T]):
    """Базовое представление для доступа к данным"""
    model: type[T]

    @classmethod
    def add(cls, values: BaseModel) -> T:
        """Добавить запись"""
        values_dict = values.model_dump(exclude_unset=True)
        new_instance = cls.model(**values_dict)
        db.session.add(new_instance)
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
        return new_instance

    @classmethod
    def add_many(cls, instances: List[BaseModel]) -> List[T]:
        """Добавить несколько записей"""
        values_list = [instance.model_dump(exclude_unset=True) for instance in instances]
        new_instances = [cls.model(**values) for values in values_list]
        db.session.add_all(new_instances)
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
        return new_instances

    @classmethod
    def get_by_id(cls, data_id: int) -> T:
        """Найти запись по ID"""
        try:
            return db.session.get(cls.model, data_id)
        except SQLAlchemyError as e:
            print(f"Error occurred: {e}")
            raise

    @classmethod
    def get_one(cls, filters: BaseModel) -> T:
        """Найти запись по фильтрам"""
        filters_dict = filters.model_dump(exclude_unset=True)
        try:
            query = select(cls.model).filter_by(**filters_dict)
            result = db.session.execute(query)
            record = result.scalar_one_or_none()
            return record
        except SQLAlchemyError as e:
            raise

    @classmethod
    def get_all(cls, filters: BaseModel = None) -> List[T]:
        """Найти несколько записей по фильтрам"""
        try:
            query = select(cls.model)
            if filters:
                filters_dict = filters.model_dump(exclude_unset=True)
                query = query.filter_by(**filters_dict)
            result = db.session.execute(query)
            records = result.scalars().all()
            return records
        except SQLAlchemyError as e:
            raise

    @classmethod
    def get_all_paginated(
        cls,
        page: int,
        per_page: int,
        filters: Optional[BaseModel] = None,
        order_by_clauses: Optional[List[ColumnElement]] = None,
        error_out: bool = False
    ) -> Pagination:
        """
        Найти несколько записей по фильтрам с пагинацией.
        Возвращает объект Flask-SQLAlchemy Pagination.
        """
        try:
            query = select(cls.model)
            if filters:
                filters_dict = filters.model_dump(exclude_unset=True)
                if filters_dict:
                    query = query.filter_by(**filters_dict)

            if order_by_clauses:
                query = query.order_by(*order_by_clauses)
            else:
                if hasattr(cls.model, 'id'):
                    query = query.order_by(cls.model.id)
                elif hasattr(cls.model, 'name'):
                    query = query.order_by(cls.model.name)

            pagination_obj = db.paginate(
                query,
                page=page,
                per_page=per_page,
                error_out=error_out,
                count=True
            )
            return pagination_obj
        except SQLAlchemyError as e:
            print(f"Database error during pagination: {e}")
            db.session.rollback()
            raise

    @classmethod
    def update_by_id(cls, data_id: int, values: BaseModel) -> None:
        """Обновление записи по ID"""
        values_dict = values.model_dump(exclude_unset=True)
        try:
            record = db.session.get(cls.model, data_id)
            if record:
                for key, value in values_dict.items():
                    setattr(record, key, value)
                db.session.commit()
        except SQLAlchemyError as e:
            print(e)
            raise e

    @classmethod
    def update_many(cls, filter_criteria: BaseModel, values: BaseModel) -> int:
        """Обновление нескольких записей"""
        filter_criteria_dict = filter_criteria.model_dump(exclude_unset=True)
        values_dict = values.model_dump(exclude_unset=True)
        try:
            query = update(cls.model).filter_by(**filter_criteria_dict).values(**values_dict)
            result = db.session.execute(query)
            db.session.commit()
            return result.rowcount
        except SQLAlchemyError as e:
            print(f"Error in mass update: {e}")
            raise

    @classmethod
    def delete_by_id(cls, data_id: int) -> None:
        """Удалить запись по ID"""
        try:
            data = db.session.get(cls.model, data_id)
            if data:
                db.session.delete(data)
                db.session.commit()
        except SQLAlchemyError as e:
            print(f"Error occurred: {e}")
            raise

    @classmethod
    def delete_many(cls, filters: BaseModel = None) -> int:
        """Удаление нескольких записей по фильтрам"""
        try:
            stmt = delete(cls.model)
            if filters:
                filters_dict = filters.model_dump(exclude_unset=True)
                stmt = stmt.filter_by(**filters_dict)
            result = db.session.execute(stmt)
            db.session.commit()
            return result.rowcount
        except SQLAlchemyError as e:
            print(f"Error occurred: {e}")
            raise

class CategoryDAO(BaseDAO[Category]):
    model = Category

    @classmethod
    def get_many(cls, names: List[str]) -> List[T]:
        """Найти несколько категорий по названиям"""
        try:
            query = select(cls.model).where(cls.model.name.in_(names))
            result = db.session.execute(query)
            records = result.scalars().all()
            return records
        except SQLAlchemyError as e:
            raise

class BrandDAO(BaseDAO[Brand]):
    model = Brand

class ProductDAO(BaseDAO[Product]):
    model = Product

    @classmethod
    def get_by_id(cls, data_id: int) -> T:
        """Найти запись по ID с загрузкой связанных данных."""
        try:
            query = select(cls.model).where(cls.model.id == data_id).options(
                joinedload(cls.model.category_brand_placement).options(joinedload(CategoryBrandPlacement.category),joinedload(CategoryBrandPlacement.brand))
            )
            return db.session.execute(query).scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Произошла ошибка: {e}")
            raise

    @classmethod
    def get_one(cls, filters: BaseModel) -> T:
        """Найти запись по фильтрам"""
        filters_dict = filters.model_dump(exclude_unset=True)
        try:
            query = select(cls.model).filter_by(**filters_dict)
            query = query.options(
                joinedload(cls.model.category_brand_placement).options(joinedload(CategoryBrandPlacement.category),joinedload(CategoryBrandPlacement.brand))
            )
            result = db.session.execute(query)
            record = result.scalar_one_or_none()
            return record
        except SQLAlchemyError as e:
            raise

    @classmethod
    def get_many_for_category(
        cls, 
        category_name: str, 
        max_height: float = float('inf'),
        min_volume: float = 0, 
        max_volume: float = float('inf')
    ) -> List[T]:
        """Найти несколько записей по категории и фильтрам"""
        try:
            query = select(cls.model)\
                .join(cls.model.category_brand_placement)\
                .join(CategoryBrandPlacement.category)\
                .where(
                    CategoryBrandPlacement.category.has(name=category_name),
                    min_volume <= cls.model.weight,
                    cls.model.weight <= max_volume,
                    cls.model.height <= max_height
                )

            query = query.options(
                joinedload(cls.model.category_brand_placement).options(
                    joinedload(CategoryBrandPlacement.category),
                    joinedload(CategoryBrandPlacement.brand)
                )
            )
            result = db.session.execute(query)
            records = result.scalars().all()
            return records
        except SQLAlchemyError as e:
            raise

    @classmethod
    def get_many_for_cb(
        cls, 
        cbp_id,
        max_height: float,
        min_volume: float = 0, 
        max_volume: float = float('inf')
    ) -> List[T]:
        """Найти несколько записей по категории и фильтрам"""
        try:
            query = select(cls.model)\
                .where(
                    cbp_id == cls.model.category_brand_placement_id,
                    min_volume <= cls.model.weight,
                    cls.model.weight <= max_volume,
                    cls.model.height <= max_height
                )

            query = query.options(
                joinedload(cls.model.category_brand_placement).options(
                    joinedload(CategoryBrandPlacement.category),
                    joinedload(CategoryBrandPlacement.brand)
                )
            )
            result = db.session.execute(query)
            records = result.scalars().all()
            return records
        except SQLAlchemyError as e:
            raise

    @classmethod
    def get_all(cls, filters: BaseModel = None) -> List[T]:
        """Найти несколько записей по фильтрам"""
        try:
            query = select(cls.model)
            if filters:
                filters_dict = filters.model_dump(exclude_unset=True)
                query = query.filter_by(**filters_dict)
            query = query.options(
                joinedload(cls.model.category_brand_placement).options(joinedload(CategoryBrandPlacement.category),joinedload(CategoryBrandPlacement.brand))
            )
            result = db.session.execute(query)
            records = result.scalars().all()
            return records
        except SQLAlchemyError as e:
            raise

    @classmethod
    def get_all_paginated(
        cls,
        page: int,
        per_page: int,
        filters: Optional[BaseModel] = None,
        order_by_clauses: Optional[List[ColumnElement]] = None,
        error_out: bool = False
    ) -> Pagination:
        """
        Найти несколько записей по фильтрам с пагинацией.
        Возвращает объект Flask-SQLAlchemy Pagination.
        """
        try:
            query = select(cls.model)
            if filters:
                filters_dict = filters.model_dump(exclude_unset=True)
                if filters_dict:
                    query = query.filter_by(**filters_dict)

            if order_by_clauses:
                query = query.order_by(*order_by_clauses)
            else:
                if hasattr(cls.model, 'id'):
                    query = query.order_by(cls.model.id)
                elif hasattr(cls.model, 'name'):
                    query = query.order_by(cls.model.name)

            query = query.options(
                joinedload(cls.model.category_brand_placement).options(joinedload(CategoryBrandPlacement.category),joinedload(CategoryBrandPlacement.brand))
            )

            pagination_obj = db.paginate(
                query,
                page=page,
                per_page=per_page,
                error_out=error_out,
                count=True
            )
            return pagination_obj
        except SQLAlchemyError as e:
            print(f"Database error during pagination: {e}")
            db.session.rollback()
            raise

    @classmethod
    def get_products_for_shelf_rules(cls, shelf_category_rules: List[Dict[str, Any]], max_height: float) -> List[T]:
        """
        Получает список товаров, которые относятся к указанным категориям и подходят по весу и высоте.

        Args:
            shelf_category_rules: Список словарей, где каждый словарь описывает правила для категории на полке.
            max_height: Максимально допустимая высота товара.

        Returns:
            Список объектов Product, соответствующих правилам.
        """

        eager_load_options = joinedload(Product.category_brand_placement).options(
            joinedload(CategoryBrandPlacement.category),
            joinedload(CategoryBrandPlacement.brand)
        )

        # Основной запрос
        base_query = select(Product).options(eager_load_options)

        # Список для хранения всех условий фильтрации (OR условия для категорий, AND для остальных)
        all_category_filters = []

        for rule_index, category_rule in enumerate(shelf_category_rules):
            category_name = category_rule.get("name")
            if not category_name:
                print(f"Предупреждение: Пропущено правило для категории без имени (индекс {rule_index}): {category_rule}")
                continue

            # Условия фильтрации для текущего правила категории
            filters_for_current_rule = [
                Category.name == category_name,
                Product.height <= max_height
            ]

            # Фильтр по "объему" (весу) продукта
            if "product_volume_min" in category_rule:
                try:
                    min_val = float(category_rule["product_volume_min"])
                    filters_for_current_rule.append(Product.weight >= min_val)
                except (ValueError, TypeError):
                    print(f"Предупреждение: Неверное значение для product_volume_min в правиле для категории '{category_name}': {category_rule['product_volume_min']}")
            
            if "product_volume_max" in category_rule:
                try:
                    max_val = float(category_rule["product_volume_max"])
                    filters_for_current_rule.append(Product.weight <= max_val)
                except (ValueError, TypeError):
                    print(f"Предупреждение: Неверное значение для product_volume_max в правиле для категории '{category_name}': {category_rule['product_volume_max']}")

            all_category_filters.append(and_(*filters_for_current_rule))

        if not all_category_filters:
            return []

        # Объединение всех условий для категорий с помощью OR
        final_filter = or_(*all_category_filters)

        # Присоединение таблицы для фильтрации по категориям
        final_query = base_query.join(
            Product.category_brand_placement
        ).join(
            CategoryBrandPlacement.category
        ).filter(final_filter)

        try:
            products = db.session.execute(final_query).scalars().all()
            return products
        except SQLAlchemyError as e:
            print(f"Ошибка SQLAlchemy при выполнении запроса товаров: {e}")
            db.session.rollback()
            return []

class ShelfDAO(BaseDAO[Shelf]):
    model = Shelf

class PlacedProductDAO(BaseDAO[PlacedProduct]):
    model = PlacedProduct

class ShelfUnitDAO(BaseDAO[ShelfUnit]):
    model = ShelfUnit

class PlanogramDAO(BaseDAO[Planogram]):
    model = Planogram

class CategoryBrandPlacementDAO(BaseDAO[CategoryBrandPlacement]):
    model = CategoryBrandPlacement