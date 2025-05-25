import itertools
from typing import Dict, List
from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from DataLayer.dao import ProductDAO, ShelfUnitDAO, PlanogramDAO, PlacedProductDAO, CategoryDAO, CategoryBrandPlacementDAO
from DataLayer.shemas import Planogram, PlacedProduct, Category, CategoryBrandPlacement
from DataLayer.models import Product

import json


class CategoryPlacementLimitation():
    '''Класс для хранения долей категорий и брендов'''
    def __init__(self, cat_share: float, brands_shares: Dict[str, float]):
        self.share = sum([share if share is not None else cat_share for share in brands_shares.values()]) # cat_share
        self.brands = brands_shares

BASE_URL = 'editor'
editor_bp = Blueprint(BASE_URL, __name__, static_folder='static', template_folder='templates', url_prefix=f'/{BASE_URL}')

@editor_bp.route('', methods=['GET'])
@editor_bp.route('/', methods=['GET'])
async def index():
    return render_template(f'{BASE_URL}/index.html')

@editor_bp.route('/get_products', methods=['GET'])
async def get_products():
    products = [product.to_dict() for product in ProductDAO.get_all()]
    return jsonify(products)

@editor_bp.route('/get_shelfUnits', methods=['GET'])
async def get_shelfUnits():
    shelfUnits = [shelfUnit.to_dict() for shelfUnit in ShelfUnitDAO.get_all()]
    return jsonify(shelfUnits)

@editor_bp.route('/get_planograms', methods=['GET'])
async def get_planograms():
    planograms = [planogram.to_dict() for planogram in PlanogramDAO.get_all()]
    return jsonify(planograms)

@editor_bp.route('/save_planogram', methods=['POST'])
async def save_planogram():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    planogram_id = data.get('id')
    name = data.get('name')
    shelf_unit_id = data.get('shelf_unit_id')
    placed_products_payload = data.get('placed_products', [])

    if not name or shelf_unit_id is None:
        return jsonify({"error": "Missing name or shelf_unit_id"}), 400

    new_planogram = Planogram(name = name, shelf_unit_id = shelf_unit_id)
    try:
        if planogram_id: # Обновление существующей планограммы
            planogram = PlanogramDAO.get_by_id(planogram_id)
            if not planogram:
                return jsonify({"error": f"Planogram with id {planogram_id} not found"}), 404
            PlanogramDAO.update_by_id(planogram_id, new_planogram)
            PlacedProductDAO.delete_many(PlacedProduct(planogram_id=planogram_id))
        else: # Создание новой планограммы
            planogram = PlanogramDAO.add(new_planogram)
            if not planogram or not planogram.id:
                return jsonify({"error": "Failed to create new planogram"}), 500
            planogram_id = planogram.id

        new_pps = [PlacedProduct(shelf_id=pp.get('shelf_id'), product_id=pp.get('product_id'), position=pp.get('position'), planogram_id=planogram_id) for pp in placed_products_payload]
        pps = PlacedProductDAO.add_many(new_pps)

        final_planogram_obj = PlanogramDAO.get_by_id(planogram_id)
        if not final_planogram_obj:
            return jsonify({"error": "Failed to retrieve saved planogram details"}), 500

        return jsonify(final_planogram_obj.to_dict()), 200

    except Exception as e:
        print(f"Error saving planogram: {e}")
        return jsonify({"error": str(e)}), 500
    

@editor_bp.route('/chat_message', methods=['POST'])
def message_handle():
    return {"reply": "ответ сервера"}, 200

def get_current_products_length(placed_products: List[Product], product_spacing: float = 0) -> float:
    '''Вычисляет текущую общую длину размещённых товаров включая межтоварное расстояние'''
    return sum([p.depth + product_spacing for p in placed_products])

def solve_dp_for_category(products: List[Product], max_weight: float, max_length: int) -> List[Product]:
    # FIXME Учитывать вес
    
    N = len(products)
    M = int(max_length * 10) # Миллиметры

    dp = [[0 for _ in range(M + 1)] for _ in range(N + 1)]

    for i in range(1, N + 1):
        item_idx = i - 1
        item_length = int(products[item_idx].depth * 10) # Миллиметры
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
        item_length = int(products[item_idx].depth * 10) # Миллиметры
        item_cost = 1
        if item_length <= current_w and dp[i][current_w] != dp[i-1][current_w]:
            taken_products.append(products[item_idx])
            current_w -= item_length

    return taken_products

def get_relevant_products(
        unused_space: Dict[str, CategoryPlacementLimitation], 
        all_products: Dict[str, List[Product]], 
        max_weight: float = 100,
        current_deviation: int = 0,
        current_placed_products: List[Product] = []
    ) -> List[Product]:
    '''Формирует набор товаров для полки с учётом текущих ограничений'''
    shelf_products = []
    free_weight = max_weight

    for category, brands in all_products.items():
        for brand, products in brands.items():
            length = unused_space[category].brands[brand] if unused_space[category].brands[brand] is not None else unused_space[category].share
            shelf_products.extend(solve_dp_for_category(products, free_weight, length))
            free_weight = max_weight - sum([p.weight for p in shelf_products])
    
    return shelf_products

@editor_bp.route('/calculate_auto_placement', methods=['POST'])
async def calculate_auto_placement():
    if 'rules_file' not in request.files:
        return jsonify({"error": "Файл правил не найден"}), 400
    if 'shelf_unit_id' not in request.form:
        return jsonify({"error": "ID стеллажа не указан"}), 400

    rules_file = request.files['rules_file']
    shelf_unit_id_str = request.form['shelf_unit_id']

    if not shelf_unit_id_str.isdigit():
        return jsonify({"error": "Неверный ID стеллажа"}), 400
    shelf_unit_id = int(shelf_unit_id_str)

    if rules_file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400

    if rules_file:
        try:
            # Парсинг правил
            rules_content = rules_file.read().decode('utf-8')
            parsed_rules = json.loads(rules_content)

            # Получение данных стеллажа
            shelf_unit_model = ShelfUnitDAO.get_by_id(shelf_unit_id)
            if not shelf_unit_model:
                return jsonify({"error": f"Стеллаж с ID {shelf_unit_id} не найден"}), 404

            # Получаем правила расстановки
            arrangement_rules = parsed_rules.get("shelf_arrangement_rules", {})
            vertical_space = float(arrangement_rules.get("vertical_space", {}).get("min", 0))
            product_spacing = float(arrangement_rules.get("product_spacing", {}).get("value", 0))
            space_allocation_deviation = float(arrangement_rules.get("brand_space_allocation", {}).get("deviation", 0)) # Допустимые отклонения по доле выкладки для брендов

            # Итерация по полкам стеллажа (отсортированным по номеру)
            sorted_shelves_from_db = sorted(shelf_unit_model.shelves, key=lambda s: s.shelf_number)
            placed_products_list = [] # Товары, которые подобраны для стеллажа
            placed_products_for_shelf = {}

            for shelf_model in sorted_shelves_from_db:
                shelf_db_id = shelf_model.id
                shelf_number_in_rules = shelf_model.shelf_number # Номер полки для поиска в правилах

                # Найти правила для текущей полки
                shelf_rule_data = next((r for r in parsed_rules.get("product_rules", {}).get("shelves", []) if r.get("number") == shelf_number_in_rules), None)
                if not shelf_rule_data:
                    print(f"Правила для полки номер {shelf_number_in_rules} не найдены, полка пропускается.")
                    continue

                products_for_shelf: Dict[str, List[Product]] = {} # Товары для полки по категориям {'Категория': {'Бренд': [...]}}
                unused_space = {} # Неиспользуемое пространство для каждой категории

                # FIXME Множественные запросы к БД придумать как исправить --- полная шляпа
                for c in shelf_rule_data.get("categories", []):
                    category = CategoryDAO.get_one(Category(name = c.get('name', 'mommy'))) # IDEA 'mommy' 🤣🤣🤣😂😂😂😁😁😁
                    categoryBrandPlacements = CategoryBrandPlacementDAO.get_all(CategoryBrandPlacement(category_id=category.id))
                    # products_for_category = ProductDAO.get_many_for_category(
                    #     category.name, 
                    #     shelf_model.height - vertical_space,
                    #     c.get('product_volume_min', 0),
                    #     c.get('product_volume_max', float('inf'))
                    # )
                    # products_for_shelf[category.name] = products_for_category
                    products_for_shelf[category.name] = {}
                    unused_space[category.name] = CategoryPlacementLimitation(
                        cat_share = shelf_model.length * category.share / 100,
                        brands_shares = {p.brand.name: 
                                         (p.share + space_allocation_deviation) * shelf_model.length * category.share / 100**2 
                                         if p.share is not None else None \
                                         for p in categoryBrandPlacements
                                        }
                    ) 
                    for cbp in categoryBrandPlacements:
                        products = list(set(ProductDAO.get_many_for_cb(
                            cbp.id,
                            shelf_model.height - vertical_space, 
                            c.get('product_volume_min', 0), 
                            c.get('product_volume_max', float('inf'))
                        )) - set(itertools.chain.from_iterable(placed_products_for_shelf.values())))
                        products_for_shelf[category.name][cbp.brand.name] = products
                    # BUG Обработку None запилить 😥😥😥

                placed_products_for_shelf[shelf_model.id] = get_relevant_products(unused_space, products_for_shelf, shelf_model.max_weight, 0, placed_products_for_shelf)
                # for ind, product in enumerate(get_relevant_products(unused_space, products_for_shelf, shelf_model.max_weight, 0, placed_products_for_shelf)):
                #     placed_products_list.append({
                #                     "shelf_id": shelf_db_id,
                #                     "product_id": product.id,
                #                     "position": ind,
                #                     "product": product.to_dict() # Полные данные о товаре для клиента
                #                 })

            for shelf_id, products in placed_products_for_shelf.items():
                for ind, product in enumerate(products):
                    placed_products_list.append({
                                    "shelf_id": shelf_id,
                                    "product_id": product.id,
                                    "position": ind,
                                    "product": product.to_dict() # Полные данные о товаре для клиента
                                })
                    
            calculated_planogram_response = {
                "id": None,
                "name": f"Выкладка для стеллажа {shelf_unit_model.shelf_unit_number}",
                "shelf_unit": shelf_unit_model.to_dict(),
                "placed_products": placed_products_list
            }
            return jsonify(calculated_planogram_response), 200

# # TODO Учитывать доли категорий на полках
# # TODO Учитывать доли брендов на полках
# # TODO Убрать дубляжи товаров на разных полках

# # TODO Дополнительные фейсинги
# # TODO Сортировать товары по правилам из JSON

# # IDEA Формализованный чат с последовательными инструкциями (МБ с подсказками всплывающими)
# # IDEA "1 Полка для категорий ...,...,...", "Порядок сортировок По категориям, По рейтингу бренда, По цене товара", 

        except json.JSONDecodeError:
            return jsonify({"error": "Ошибка парсинга файла правил (неверный JSON)"}), 400
        except Exception as e:
            print(f"Ошибка при обработке файла правил: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Ошибка сервера при обработке правил: {str(e)}"}), 500
    else:
        return jsonify({"error": "Неподдерживаемый тип файла или ошибка файла"}), 400