from collections import defaultdict
import operator
from typing import Any, Callable, Dict, List, Set, Tuple
from DataLayer.dao import ProductDAO, ShelfUnitDAO
from DataLayer.models import Brand, Product, Shelf
from app.blueprints.editor.exceptions import AutoPlacementError
from .models import planogram_data, rules_data, server_message, shelf_rule
from DataLayer.enums import BrandSorting, ProductSorting

def get_product_sort_key_and_reverse(sort_option: ProductSorting):
    """
    Возвращает кортеж (функция-ключ для сортировки, флаг reverse)
    для объекта Product на основе опции ProductSorting.
    """
    sort_keys = {
        ProductSorting.PriceAsc:    (lambda product: product.price, False),
        ProductSorting.PriceDesc:   (lambda product: product.price, True),
        ProductSorting.RatingAsc:   (lambda product: product.SKU_rating.value if product.SKU_rating else 0, False),
        ProductSorting.RatingDesc:  (lambda product: product.SKU_rating.value if product.SKU_rating else 0, True),
        ProductSorting.NameAsc:     (lambda product: product.name, False),
        ProductSorting.NameDesc:    (lambda product: product.name, True),
    }
    return sort_keys.get(sort_option, (None, False))

def get_brand_sort_key_and_reverse(sort_option: BrandSorting):
    """
    Возвращает кортеж (функция-ключ для сортировки, флаг reverse)
    для объекта Brand на основе опции BrandSorting.
    """
    sort_keys = {
        BrandSorting.NameAsc:    (lambda brand: brand.name, False),
        BrandSorting.NameDesc:   (lambda brand: brand.name, True),
        BrandSorting.RatingAsc:  (lambda brand: brand.rating.value if brand.rating else 0, False),
        BrandSorting.RatingDesc: (lambda brand: brand.rating.value if brand.rating else 0, True),
    }
    return sort_keys.get(sort_option, (None, False))

def get_combined_sorting_steps(rules: rules_data) -> List[Tuple[Callable[[Product], Any], bool]]:
    """
    Возвращает список кортежей (функция-ключ, флаг reverse) для последовательной многоступенчатой сортировки.
    Приоритет: сначала бренд, затем продукт.
    """
    brand_key_func, brand_reverse_flag = get_brand_sort_key_and_reverse(rules.brand_sort)
    product_key_func, product_reverse_flag = get_product_sort_key_and_reverse(rules.product_sort)

    return (brand_key_func, brand_reverse_flag), (product_key_func, product_reverse_flag)

def get_total_product_length_on_category(pps, spacing : float):
    return sum([p.depth + spacing for p in pps])


def group_and_sort_by_brand(key, reverse, products: List[Product]) -> Dict[Brand, List[Product]]:
    grouped_products = defaultdict(list)

    for product in products:
        grouped_products[product.brand].append(product)
    sorted_brands_list = sorted(list(grouped_products.keys()), key=key, reverse=reverse) 
    return sorted_brands_list, grouped_products 

def product_sort(key, reverse, products : List[Product]) -> List[Product]:
    return sorted(sorted(products, key=lambda p: p.name), key=key, reverse=reverse)

def category_sort(brand_sorts, product_sorts, products):
    sorted_brand_list, grouped_products = group_and_sort_by_brand(brand_sorts[0], brand_sorts[1], products)

    sorted_products = []
    for key in sorted_brand_list:
        s_p = product_sort(product_sorts[0], product_sorts[1], grouped_products[key])
        sorted_products.extend(s_p)

    return sorted_products


def solve_dp_for_category(products: List[Product], max_weight: float, max_length: float, spacing: float) -> List[Product]:
    """
    Решает задачу о максимальном заполнении полки, максимизируя количество товаров
    с учетом ограничений по длине и весу.
    Использует 2D DP, где ячейка хранит (количество_товаров, их_суммарный_вес).
    """
    N = len(products)
    
    max_length_mm = int(max_length * 10)
    max_weight_g = int(max_weight * 1000)

    if max_length_mm <= 0 or max_weight_g <= 0:
        return []

    # dp[i][l] = (count, total_weight)
    dp = [[(0, 0) for _ in range(max_length_mm + 1)] for _ in range(N + 1)]

    for i in range(1, N + 1):
        item_idx = i - 1
        product = products[item_idx]
        
        item_length_mm = int((product.depth + spacing) * 10)
        item_weight_g = int(product.weight * 1000)
        
        for l in range(max_length_mm + 1):
            count_without, weight_without = dp[i-1][l]
            count_with, weight_with = -1, -1 

            if l >= item_length_mm:
                prev_count, prev_weight = dp[i-1][l - item_length_mm]
                
                new_total_weight = prev_weight + item_weight_g
                if new_total_weight <= max_weight_g:
                    count_with = prev_count + 1
                    weight_with = new_total_weight
            
            if count_with > count_without:
                dp[i][l] = (count_with, weight_with)
            elif count_with == count_without and weight_with < weight_without:
                dp[i][l] = (count_with, weight_with)
            else:
                dp[i][l] = (count_without, weight_without)
    
    taken_products = []
    current_l = max_length_mm

    for i in range(N, 0, -1):
        if dp[i][current_l] != dp[i-1][current_l]:
            product = products[i-1]
            item_length_mm = int((product.depth + spacing) * 10)
            taken_products.append(product)
            current_l -= item_length_mm
            
    return taken_products

def calculate_auto_placement_for_shelf(shelf: Shelf, shelf_rule: shelf_rule, brand_sorts, product_sorts, spacing: float, used_product_ids: Set[int]):
    shelf_placed_products = []
    remaining_shelf_weight = shelf.max_weight

    for category_rule in shelf_rule.category_rules:
        if remaining_shelf_weight <= 0:
            break

        # Шаг 1: Получаем всех возможных кандидатов для категории
        all_products_for_category = ProductDAO.get_many_for_category(
            category_rule.category_name,
            shelf.height,
            category_rule.min_weight if category_rule.min_weight else 0,
            category_rule.max_weight if category_rule.max_weight else float('inf')
        )

        # <<< ИЗМЕНЕНИЕ 5: Фильтруем кандидатов, оставляя только те, которых еще нет на стеллаже.
        available_products = [
            p for p in all_products_for_category if p.id not in used_product_ids
        ]
        
        # Если после фильтрации не осталось доступных товаров, переходим к следующему правилу
        if not available_products:
            continue

        share = category_rule.percentage
        category_length = share * shelf.length / 100
        
        # <<< ИЗМЕНЕНИЕ 6: Используем отфильтрованный список `available_products` для вызова DP.
        category_placed_products = solve_dp_for_category(
            available_products, remaining_shelf_weight, category_length, spacing
        )
        
        placed_weight = sum(p.weight for p in category_placed_products)
        remaining_shelf_weight -= placed_weight
        products_length = get_total_product_length_on_category(category_placed_products, spacing)
        
        # Добавление фейсингов (здесь также используется отфильтрованный список)
        while len(category_placed_products) > 0 and products_length < category_length and remaining_shelf_weight > 0:
            # <<< ИЗМЕНЕНИЕ 7: И для фейсингов используем `available_products`.
            new_products = solve_dp_for_category(
                available_products, remaining_shelf_weight, category_length - products_length, spacing
            )
            if not new_products:
                break

            newly_placed_weight = sum(p.weight for p in new_products)
            remaining_shelf_weight -= newly_placed_weight
            
            category_placed_products.extend(new_products)
            products_length = get_total_product_length_on_category(category_placed_products, spacing)

        category_placed_products = category_sort(brand_sorts, product_sorts, category_placed_products)
        shelf_placed_products.extend(category_placed_products)

    return shelf_placed_products

def calculate_auto_placement(shelf_unit_id: int, planogram_id: int, planogram_name: str, rules: rules_data) -> server_message:
    brand_sorts, product_sorts = get_combined_sorting_steps(rules)

    spacing = rules.spacing
    shelf_unit = ShelfUnitDAO.get_by_id(shelf_unit_id)
    
    if not shelf_unit:
        raise AutoPlacementError(f"Стеллаж с ID {shelf_unit_id} не найден.")

    placed_products_on_unit = []
    used_product_ids: Set[int] = set()

    for shelf_rule in rules.shelves_rules:
        shelf = shelf_unit.get_shelf_by_number(shelf_rule.shelf_number)
        
        if not shelf:
            raise AutoPlacementError(f"Полка с номером {shelf_rule.shelf_number} не найдена в стеллаже.")

        products_for_this_shelf = calculate_auto_placement_for_shelf(
            shelf, shelf_rule, brand_sorts, product_sorts, spacing, used_product_ids
        )
        
        for p in products_for_this_shelf:
            used_product_ids.add(p.id)

        placed_products_on_unit.extend([{
            "shelf_id": shelf.id,
            "product_id": p.id,
            "position": i,
            "product": p.to_dict()
        } for i, p in enumerate(products_for_this_shelf)])
    
    # Этот код выполнится только если все прошло успешно
    server_mes = server_message(
        "Сформирована автовыкладка",
        planogram_data(
            planogram_id, 
            planogram_name if planogram_name else "Автовыкладка", 
            shelf_unit, 
            placed_products_on_unit
        ),
        rules
    )
    return server_mes