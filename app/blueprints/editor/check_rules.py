from DataLayer.dao import ProductDAO
from .models import rules_data

def get_free_percentage(category_name: str, current_rules: rules_data, shelf_number: int, shelf_id: int) -> float:
    """
    Рассчитывает доступный (свободный) процент на полке.
    """
    return 100 - current_rules.get_total_percentage_on_shelf(shelf_number, shelf_id, category_name)

def check_total_percentage(category_name: str, new_percentage: float, current_rules: rules_data, shelf_number: int, shelf_id: int) -> bool:
    """
    Проверяет, можно ли выделить new_percentage для категории, не превысив 100%.
    """
    free_percentage = get_free_percentage(category_name, current_rules, shelf_number, shelf_id)
    return free_percentage >= new_percentage

def get_all_categories_for_shelf(current_rules: rules_data, shelf_number: int, shelf_id: int) -> list:
    """
    Возвращает список имен всех категорий, разрешенных на полке.
    """
    return current_rules.get_all_categories_on_shelf(shelf_number, shelf_id)

def can_place_product(product, current_rules: rules_data, shelf_number: int, shelf_id: int, shelf_len: float, pps: list) -> bool:
    """
    Проверяет, можно ли разместить товар на полке в рамках выделенного для его категории места.
    """
    total_percentage_for_category = current_rules.get_category_percentage_on_shelf(shelf_number, shelf_id, product.category.name)
    
    if total_percentage_for_category is None or total_percentage_for_category <= 0:
        return False

    category_length = total_percentage_for_category * shelf_len / 100

    pps_len = 0
    spacing = current_rules.spacing if current_rules.spacing is not None else 0.5 

    for pp in pps:
        if 'product_id' not in pp or 'shelf_id' not in pp:
            continue
            
        if pp['shelf_id'] == shelf_id:
            pproduct = ProductDAO.get_by_id(pp['product_id'])
            if pproduct and pproduct.category.id == product.category.id:
                pps_len += pproduct.depth + spacing

    return pps_len + product.depth <= category_length