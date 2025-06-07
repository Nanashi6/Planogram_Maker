from collections import defaultdict
import operator
from typing import Any, Callable, Dict, List, Tuple
from DataLayer.dao import ProductDAO, ShelfUnitDAO
from DataLayer.models import Brand, Product, Shelf
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

def get_total_product_length_on_category(pps):
    return sum([p.depth + 0.5 for p in pps])


def group_and_sort_by_brand(key, reverse, products: List[Product]) -> Dict[Brand, List[Product]]:
    grouped_products = defaultdict(list)

    for product in products:
        grouped_products[product.brand].append(product)
    sorted_brands_list = sorted(list(grouped_products.keys()), key=key, reverse=reverse) 
    return sorted_brands_list, grouped_products 

def product_sort(key, reverse, products : List[Product]) -> List[Product]:
    return sorted(products, key=key, reverse=reverse)

def category_sort(brand_sorts, product_sorts, products):
    sorted_brand_list, grouped_products = group_and_sort_by_brand(brand_sorts[0], brand_sorts[1], products)

    sorted_products = []
    for key in sorted_brand_list:
        s_p = product_sort(product_sorts[0], product_sorts[1], grouped_products[key])
        sorted_products.extend(s_p)

    return sorted_products


def solve_dp_for_category(products: List[Product], max_weight: float, max_length: int) -> List[Product]: # FIXME переписать/передумать
    # FIXME Учитывать вес
    
    N = len(products)
    M = int(max_length * 10) # Миллиметры

    dp = [[0 for _ in range(M + 1)] for _ in range(N + 1)]

    for i in range(1, N + 1):
        item_idx = i - 1
        item_length = int(products[item_idx].depth * 10) + 5 # Миллиметры           # 5 --- 0.5 * 10 --- отступ между товарами
        item_cost = 1
        for w in range(M + 1):
            cost_without = dp[i-1][w]
            cost_with = 0
            if item_length <= w:
                cost_with = dp[i-1][w - item_length] + item_cost
            dp[i][w] = max(cost_without, cost_with)

    taken_products = []
    current_w = M

    for i in range(N, 0, -1):
        item_idx = i - 1
        item_length = int(products[item_idx].depth * 10) + 5 # Миллиметры           # 5 --- 0.5 * 10 --- отступ между товарами
        item_cost = 1
        if item_length <= current_w and dp[i][current_w] != dp[i-1][current_w]:
            taken_products.append(products[item_idx])
            current_w -= item_length

    return taken_products

def calculate_auto_placement_for_shelf(shelf : Shelf, shelf_rule : shelf_rule, brand_sorts, product_sorts):
    shelf_placed_products = []
    for category_rule in shelf_rule.category_rules:
        products_for_shelf = ProductDAO.get_many_for_category(
            category_rule.category_name,
            shelf.height,
            category_rule.min_weight if category_rule.min_weight else 0,
            category_rule.max_weight if category_rule.max_weight else float('inf')                        
        ) # IDEA также можно исключать товары с других полок чтобы разнообразие повысить

        # тут вызывается DP для расстановки товаров
        share = category_rule.percentage
        category_length = share * shelf.length / 100
        category_placed_products = solve_dp_for_category(products_for_shelf, shelf.max_weight, category_length) # FIXME вес исходя из уже стоящих продуктов 
                    
        # Установка дополнительный фейсингов из того же пула товаров, если осталось свободное место
        flag = True if len(category_placed_products) > 0 else False
        products_length = get_total_product_length_on_category(category_placed_products)
        print(products_length, category_length, flag)
        while flag and products_length < category_length:
            new_products = solve_dp_for_category(products_for_shelf, shelf.max_weight, category_length - products_length)
            flag = True if len(new_products) > 0 else False
            category_placed_products.extend(new_products)
            products_length = get_total_product_length_on_category(category_placed_products)

        category_placed_products = category_sort(brand_sorts, product_sorts, category_placed_products)
                    
        shelf_placed_products.extend(category_placed_products)

    return shelf_placed_products

def calculate_auto_placement(shelf_unit_id : int, planogram_id : int, planogram_name : str, rules : rules_data) -> server_message:
    brand_sorts, product_sorts = get_combined_sorting_steps(rules)

    # Берём стеллаж
    # Перебираем полки в порядке порядка в правилах или наоборот (находим правило для полки)
    # Для каждой категории полки решаем DP +++++ можно разные DP придумать, но сначала только один вид
    # После решения DP сортируем товары и переходим к следующей категории/полке

    shelf_unit = ShelfUnitDAO.get_by_id(shelf_unit_id)
    if shelf_unit:
        placed_products = []
        for shelf_rule in rules.shelves_rules:
            shelf = shelf_unit.get_shelf_by_number(shelf_rule.shelf_number)
            if shelf:
                placed_products.extend([{
                    "shelf_id": shelf.id,
                    "product_id": p.id,
                    "position": i,
                    "product": p.to_dict()
                } for i, p in enumerate(calculate_auto_placement_for_shelf(shelf, shelf_rule, brand_sorts, product_sorts))])
            else:
                # BUG тут сообнение об ошибке с полкой
                ...
        server_mes = server_message(
            "Сформирована автовыкладка",
            planogram_data(
                None, 
                planogram_name if planogram_name else "Автовыкладка", 
                shelf_unit, 
                placed_products
            ),
            rules
        ) # Присылать данные о текущей планограмме если она есть с клиента
        return server_mes
    else:
        # BUG тут сообщение об ошибке со стеллажом
        ...
