from typing import Generic, List, TypeVar
from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError

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
        
class ShelfDAO(BaseDAO[Shelf]):
    model = Shelf

class PlacedProductDAO(BaseDAO[PlacedProduct]):
    model = PlacedProduct

class ShelfUnitDAO(BaseDAO[ShelfUnit]):
    model = ShelfUnit

class PlanogramDAO(BaseDAO[Planogram]):
    model = Planogram