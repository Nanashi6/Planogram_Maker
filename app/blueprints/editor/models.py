from typing import Any, Dict, List, Optional
from DataLayer.models import ShelfUnit
from DataLayer.enums import BrandSorting, MessageTypes, ProductSorting

class planogram_data():
    """
    Данные о планограмме.
    """
    def __init__(self, id : int = None, name : str = None, shelf_unit : ShelfUnit = None, placed_products : dict = None):
        self.name = name
        self.id = id
        self.shelf_unit = shelf_unit
        self.placed_products = placed_products

    def to_json(self):
        """
        Преобразует объект planogram_data в словарь для JSON-сериализации.
        """
        shelf_unit_json = None
        if self.shelf_unit:
            shelf_unit_json = self.shelf_unit.to_dict()

        return {
            "id": self.id,
            "name": self.name,
            "shelf_unit": shelf_unit_json,
            "placed_products": self.placed_products
        }

class category_rule():
    def __init__(self, category_name: str, category_id: int, 
                 percentage: Optional[int] = None, 
                 min_weight: Optional[float] = None, 
                 max_weight: Optional[float] = None):
        self.category_name = category_name
        self.category_id = category_id
        self.percentage = percentage
        self.min_weight = min_weight
        self.max_weight = max_weight

    def to_json(self) -> dict:
        return {
            "category_name": self.category_name,
            "category_id": self.category_id,
            "percentage": self.percentage,
            "min_weight": self.min_weight,
            "max_weight": self.max_weight
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'category_rule':
        """Создает экземпляр category_rule из словаря."""
        if not isinstance(data, dict):
            raise TypeError("Input data for category_rule must be a dictionary.")
            
        return category_rule(
            category_name=data.get("categoryName", data.get('category_name')),
            category_id=data.get("categoryId", data.get('category_id')),
            percentage=data.get("percentage"),
            min_weight=data.get("minWeight", data.get('min_weight')),
            max_weight=data.get("maxWeight", data.get('max_weight'))
        )

class shelf_rule():
    def __init__(self, shelf_number: int, shelf_id: int, 
                 category_rules: Optional[List[category_rule]] = []):
        self.shelf_number = shelf_number
        self.shelf_id = shelf_id
        self.category_rules = category_rules

    def set_category_rules(self, rules: List['category_rule']):
        """Полностью заменяет список правил для категорий."""
        self.category_rules = rules

    def get_category_rule(self, category_id: int) -> Optional[category_rule]:
        """
        Находит и возвращает правило для категории по ее ID.
        Возвращает None, если правило не найдено.
        """
        for rule in self.category_rules:
            if rule.category_id == category_id:
                return rule
        return None

    def add_category_rule(self, rule_to_add: category_rule):
        """
        Добавляет или ОБНОВЛЯЕТ правило для категории на этой полке.
        Сначала удаляет любое существующее правило для той же категории, а затем добавляет новое.
        """
        # self.category_rules = [
        #     rule for rule in self.category_rules 
        #     if rule.category_id != rule_to_add.category_id
        # ]
        self.category_rules.append(rule_to_add)

    def delete_category_rule(self, rule_to_delete: category_rule):
        """
        Удаляет ВСЕ правила для указанной категории (по ID) с полки.
        """
        initial_len = len(self.category_rules)
        self.category_rules = [
            rule for rule in self.category_rules 
            if rule.category_id != rule_to_delete.category_id
        ]
        if len(self.category_rules) < initial_len:
            print(f"Удалено правило для категории ID: {rule_to_delete.category_id}")

    def get_categories(self):
        return [c.category_name for c in self.category_rules]

    def get_total_percentage(self, except_category_name):
        total_percentage = 0
        for c in self.category_rules:
            if except_category_name.lower() != c.category_name.lower():
                total_percentage += c.percentage
        return total_percentage

    def get_category_percentage(self, category_name):
        c_rule = None
        for category in self.category_rules:
            if category.category_name.lower() == category_name.lower():
                c_rule = category
                break
        if c_rule:
            return c_rule.percentage
        return 0

    def to_json(self) -> dict:
        return {
            "shelf_number": self.shelf_number,
            "shelf_id": self.shelf_id,
            "category_rules": [rule.to_json() for rule in self.category_rules]
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'shelf_rule':
        """Создает экземпляр shelf_rule из словаря."""
        if not isinstance(data, dict):
            raise TypeError("Input data for shelf_rule must be a dictionary.")

        category_allocations_data = data.get("categoryAllocations", data.get('category_rules', []))
        parsed_category_rules = []
        if isinstance(category_allocations_data, list):
            for cat_rule_data in category_allocations_data:
                if isinstance(cat_rule_data, dict):
                    try:
                        parsed_category_rules.append(category_rule.from_dict(cat_rule_data))
                    except TypeError as e:
                        print(f"Skipping invalid category rule data: {cat_rule_data}. Error: {e}")
                else:
                    print(f"Skipping non-dictionary item in categoryAllocations: {cat_rule_data}")
        else:
            print(f"Warning: categoryAllocations is not a list, it's {type(category_allocations_data)}. No category rules loaded.")
            
        return shelf_rule(
            shelf_id=data.get("shelfDbId", data.get('shelf_id')),
            shelf_number=data.get("shelfNumber", data.get('shelf_number')),
            category_rules=parsed_category_rules
        )

class rules_data():
    def __init__(self, brand_sort: str = BrandSorting.RatingAsc, product_sort: str = ProductSorting.PriceAsc, 
                 spacing: float = 0.5, 
                 shelves_rules: Optional[List[shelf_rule]] = None):
        self.brand_sort = brand_sort
        self.product_sort = product_sort
        self.spacing = spacing
        self.shelves_rules = shelves_rules if shelves_rules is not None else []

    def get_category_rule_on_shelf(self, shelf_number: int, category_id: int) -> Optional[category_rule]:
        """Находит правило для категории на конкретной полке."""
        shelf = self.get_shelf_rule(shelf_number)
        if shelf:
            return shelf.get_category_rule(category_id)
        return None

    def set_rules_for_shelf(self, shelf_number: int, shelf_id: int, new_category_rules):
        """
        Находит правило для полки и полностью заменяет его правила для категорий.
        Если правило для полки не найдено, создает новое.
        """
        s_rule = self.get_shelf_rule(shelf_number)
        if s_rule:
            s_rule.set_category_rules(new_category_rules)
        else:
            new_s_rule = shelf_rule(shelf_number, shelf_id, category_rules=new_category_rules)
            self.add_shelf_rule(new_s_rule)

    def add_shelf_rule(self, rule: shelf_rule):
        """Добавляет правило полки к общим правилам."""
        self.shelves_rules.append(rule)

    def get_shelf_rule(self, shelf_number: int):
        for shelf in self.shelves_rules:
            if shelf.shelf_number == shelf_number:
                return shelf

    def add_category_rule(self, shelf_number : int, shelf_id : int, rule: category_rule):
        """Добавляет или обновляет правило категории для полки."""
        s_rule = self.get_shelf_rule(shelf_number)
        if not s_rule:
            s_rule = shelf_rule(shelf_number, shelf_id)
            self.add_shelf_rule(s_rule)
        s_rule.add_category_rule(rule)

    def delete_category_rule(self, shelf_number : int, shelf_id : int, rule: category_rule):
        """Удаляет правило категории у полки."""
        s_rule = self.get_shelf_rule(shelf_number)
        if s_rule:
            s_rule.delete_category_rule(rule)

    def get_total_percentage_on_shelf(self, shelf_number : int, shelf_id : int, except_category_name):
        s_rule = self.get_shelf_rule(shelf_number)
        if s_rule:
            return s_rule.get_total_percentage(except_category_name)
        return 0
    
    def get_all_categories_on_shelf(self, shelf_number, shelf_id):
        s_rule = self.get_shelf_rule(shelf_number)
        if s_rule:
            return s_rule.get_categories()
        return []

    def get_category_percentage_on_shelf(self, shelf_number, shelf_id, category_name):
        s_rule = self.get_shelf_rule(shelf_number)
        if s_rule:
            return s_rule.get_category_percentage(category_name)
        return 0

    def to_json(self) -> dict:
        return {
            "global_rules": { # Отдельный блок для глобальных правил для ясности
                "brand_sort_by": self.brand_sort,
                "product_sort_by": self.product_sort,
                "spacing": self.spacing
            },
            "shelves_rules": [rule.to_json() for rule in self.shelves_rules]
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'rules_data':
        """Создает экземпляр rules_data из словаря."""
        if not isinstance(data, dict):
            raise TypeError("Input data for rules_data must be a dictionary.")

        global_rules_data = data.get("global", data.get('global_rules', {}))
        if not isinstance(global_rules_data, dict):
            print(f"Warning: 'global' key in rules_data is not a dictionary. Using defaults.")
            global_rules_data = {}
            
        shelves_data = data.get("shelves", data.get('shelves_rules', []))
        parsed_shelves_rules = []
        if isinstance(shelves_data, list):
            for shelf_data_item in shelves_data:
                if isinstance(shelf_data_item, dict):
                    try:
                        parsed_shelves_rules.append(shelf_rule.from_dict(shelf_data_item))
                    except TypeError as e:
                         print(f"Skipping invalid shelf rule data: {shelf_data_item}. Error: {e}")
                else:
                    print(f"Skipping non-dictionary item in shelves: {shelf_data_item}")

        else:
            print(f"Warning: 'shelves' key in rules_data is not a list. No shelf rules loaded.")


        return rules_data(
            brand_sort=global_rules_data.get("brandSortBy", global_rules_data.get('brand_sort_by')),
            product_sort=global_rules_data.get("productSortBy", global_rules_data.get('product_sort_by')),
            spacing=global_rules_data.get("spacing", 0.5),
            shelves_rules=parsed_shelves_rules
        )

class server_message():
    """
    Серверное сообщение клиенту.
    """
    def __init__(self, message = "", data: any = None, rules : rules_data = None, type : MessageTypes = MessageTypes.Info):
        self.message = message
        self.data = data
        self.rules = rules if rules is not None else rules_data()
        self.type = type

    def to_json(self):
        """
        Преобразует объект server_message в словарь для JSON-сериализации.
        """
        data_json = None
        if self.data:
            if hasattr(self.data, 'to_json') and callable(self.data.to_json):
                data_json = self.data.to_json()
            else:
                data_json = self.data

        rules_json = self.rules.to_json() if self.rules else None

        return {
            "message": self.message,
            "data": data_json,
            "rules": rules_json,
            "type": self.type
        }