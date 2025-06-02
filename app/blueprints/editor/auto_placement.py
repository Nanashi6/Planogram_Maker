import operator
from typing import Any, Callable, List, Tuple
from DataLayer.dao import ProductDAO, ShelfUnitDAO
from DataLayer.models import Product, Shelf
from .models import planogram_data, rules_data, server_message, shelf_rule
from .enums import BrandSorting, ProductSorting

def get_product_sort_key_and_reverse(sort_option: ProductSorting):
    """
    Возвращает кортеж (функция-ключ для сортировки, флаг reverse)
    для объекта Product на основе опции ProductSorting.
    """
    sort_keys = {
        ProductSorting.PriceAsc:    (operator.attrgetter('price'), False),
        ProductSorting.PriceDesc:   (operator.attrgetter('price'), True),
        ProductSorting.RatingAsc:   (operator.attrgetter('rating'), False),
        ProductSorting.RatingDesc:  (operator.attrgetter('rating'), True),
        ProductSorting.NameAsc:     (operator.attrgetter('name'), False),
        ProductSorting.NameDesc:    (operator.attrgetter('name'), True),
    }
    return sort_keys.get(sort_option, (None, False))

def get_brand_sort_key_and_reverse(sort_option: BrandSorting):
    """
    Возвращает кортеж (функция-ключ для сортировки, флаг reverse)
    для объекта Brand на основе опции BrandSorting.
    """
    sort_keys = {
        BrandSorting.NameAsc:    (lambda product: product.category_brand_placement.brand.name if product.category_brand_placement and product.category_brand_placement.brand else '', False),
        BrandSorting.NameDesc:   (lambda product: product.category_brand_placement.brand.name if product.category_brand_placement and product.category_brand_placement.brand else '', True),
        BrandSorting.RatingAsc:  (lambda product: product.category_brand_placement.brand.rating.value if product.category_brand_placement and product.category_brand_placement.brand and product.category_brand_placement.brand.rating else 0, False),
        BrandSorting.RatingDesc: (lambda product: product.category_brand_placement.brand.rating.value if product.category_brand_placement and product.category_brand_placement.brand and product.category_brand_placement.brand.rating else 0, True),
    }
    return sort_keys.get(sort_option, (None, False))

def get_combined_sorting_steps(rules: rules_data) -> List[Tuple[Callable[[Product], Any], bool]]:
    """
    Возвращает список кортежей (функция-ключ, флаг reverse) для последовательной многоступенчатой сортировки.
    Приоритет: сначала бренд, затем продукт.
    """
    brand_key_func, brand_reverse_flag = get_brand_sort_key_and_reverse(rules.brand_sort)
    product_key_func, product_reverse_flag = get_product_sort_key_and_reverse(rules.product_sort)

    sorting_steps = []

    if product_key_func:
        sorting_steps.append((product_key_func, product_reverse_flag))
    
    if brand_key_func:
        sorting_steps.append((brand_key_func, brand_reverse_flag))

    return sorting_steps

def sort_by_categories(): # IDEA мб не надо, т.к. сортировки покатегорийные будут 
    ...

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

def calculate_auto_placement_for_shelf(shelf : Shelf, shelf_rule : shelf_rule, sorting_steps):
    shelf_placed_products = []
    for category_rule in shelf_rule.category_rules:
        print(category_rule.category_name)
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
                    
        for key_func, reverse_flag in sorting_steps:
            category_placed_products.sort(key=key_func, reverse=reverse_flag)
                    
        shelf_placed_products.extend(category_placed_products)

    return shelf_placed_products

def calculate_auto_placement(shelf_unit_id : int, rules : rules_data) -> server_message:
    sorting_steps = get_combined_sorting_steps(rules)

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
                } for i, p in enumerate(calculate_auto_placement_for_shelf(shelf, shelf_rule, sorting_steps))])
            else:
                # тут сообнение об ошибке с полкой
                ...
        server_mes = server_message(
            "Сформирована автовыкладка",
            planogram_data(
                None, 
                "Автовыкладка", 
                shelf_unit, 
                placed_products
            ),
            rules
        ) # Присылать данные о текущей планограмме если она есть с клиента
        return server_mes
    else:
        # тут сообщение об ошибке со стеллажом
        ...
