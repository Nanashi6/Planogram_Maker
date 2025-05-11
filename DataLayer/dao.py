from typing import Generic, List, TypeVar
from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import joinedload

from DataLayer.models import Base, Category, Brand, Product, PlacedProduct, Shelf, ShelfUnit, Planogram
from app import db

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

class BrandDAO(BaseDAO[Brand]):
    model = Brand

class ProductDAO(BaseDAO[Product]):
    model = Product

    @classmethod
    def get_products_by_categories_and_weight(cls, category_filters: list[dict]) -> list[Product]: #TODO Добавить условие для вертикального промежутка
        """
        Получает список товаров, соответствующих заданным критериям категорий и веса.
        Args:
            category_filters: Список словарей, где каждый словарь представляет фильтр
                              для одной или нескольких категорий.
                              Пример:
                              [
                                  {
                                      "name": "Электроника",
                                      "min_weight": 0.5,
                                      "max_weight": 2.0 
                                  },
                                  {
                                      "category_names": "Книги",
                                  }
                              ]
                              Товары будут выбраны, если они принадлежат ЛЮБОЙ из указанных
                              групп категорий И соответствуют весовым ограничениям ЭТОЙ группы.
        Returns:
            Список объектов Product, соответствующих критериям.
        """
        or_conditions = []

        if not category_filters:
            return []

        for cat_filter in category_filters:
            category_name = cat_filter.get("name")
            min_weight = cat_filter.get("product_volume_min")
            max_weight = cat_filter.get("product_volume_max")

            current_group_conditions = []

            if not category_name:
                continue 
            
            current_group_conditions.append(Product.category.has(Category.name == category_name))

            if min_weight is not None:
                current_group_conditions.append(Product.weight >= min_weight)
            if max_weight is not None:
                current_group_conditions.append(Product.weight <= max_weight)
            
            if current_group_conditions:
                or_conditions.append(and_(*current_group_conditions))
        
        if not or_conditions:
            return []

        stmt = (
            select(Product)
            .join(Product.category)
            .where(or_(*or_conditions))
            .options(joinedload(Product.category))
            .distinct()
        )
        
        result = db.session.execute(stmt)
        products = result.scalars().all()
        
        return products
        
class ShelfDAO(BaseDAO[Shelf]):
    model = Shelf

class PlacedProductDAO(BaseDAO[PlacedProduct]):
    model = PlacedProduct

class ShelfUnitDAO(BaseDAO[ShelfUnit]):
    model = ShelfUnit

class PlanogramDAO(BaseDAO[Planogram]):
    model = Planogram