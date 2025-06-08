from collections import defaultdict
from typing import Dict, List, Type
from flask import Blueprint, render_template, jsonify, request
from DataLayer.dao import ProductDAO, ShelfUnitDAO, PlanogramDAO, PlacedProductDAO, RuleDAO, ShelfRuleDAO, CategoryRuleDAO, CategoryDAO
from DataLayer.shemas import Planogram, PlacedProduct, Category, Rule, ShelfRule, CategoryRule
from DataLayer.enums import *
from app.blueprints.editor.exceptions import AutoPlacementError
from .models import rules_data
from .commands_handlers import commands_handler
from .auto_placement import calculate_auto_placement

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

def enum_to_select_options(enum_class: Type[enum.Enum], custom_labels: Dict[str, str] = None) -> List[Dict[str, str]]:
    """
    Преобразует Enum в список словарей для использования в HTML select.
    Каждый словарь имеет ключи "value" и "label".
    """
    options = []
    if custom_labels is None:
        custom_labels = {}

    for member in enum_class:
        # Пытаемся создать "человекочитаемую" метку, если нет кастомной
        default_label = member.name.replace('_', ' ')
        if default_label.endswith(" Asc"):
            default_label = f"{default_label[:-4]} (Low to High / A-Z)"
        elif default_label.endswith(" Desc"):
            default_label = f"{default_label[:-5]} (High to Low / Z-A)"
        
        label = custom_labels.get(member.value, default_label)
        
        options.append({"value": member.value, "label": label})
    return options

@editor_bp.route('/get_sorting_rules', methods=['GET'])
async def get_sorting_rules():
    p_sort_keys = {
        ProductSorting.PriceAsc:    "Цена по возрастанию",
        ProductSorting.PriceDesc:   "Цена по убыванию",
        ProductSorting.RatingAsc:   "Рейтинг по возрастанию",
        ProductSorting.RatingDesc:  "Рейтинг по убыванию",
        ProductSorting.NameAsc:     "Название (А-Я)",
        ProductSorting.NameDesc:    "Название (Я-А)",
    }

    b_sort_keys = {
        BrandSorting.NameAsc:    "Название бренда (А-Я)",
        BrandSorting.NameDesc:   "Название бренда (Я-А)",
        BrandSorting.RatingAsc:  "Рейтинг бренда (по возрастанию)",
        BrandSorting.RatingDesc: "Рейтинг бренда (по убыванию)",
    }

    brand_sorting_options = enum_to_select_options(BrandSorting, b_sort_keys)
    product_sorting_options = enum_to_select_options(ProductSorting, p_sort_keys)

    sorting_rules = {
        "brand_sort_options": brand_sorting_options,
        "product_sort_options": product_sorting_options,
        "defaults": {
            "brand_sort": BrandSorting.RatingDesc.value,
            "product_sort": ProductSorting.PriceAsc.value
        }
    }
    return jsonify(sorting_rules)

def is_correct_planogram(pps, rules : rules_data):
    errors : List[str] = []

    shelf_rules = rules.shelves_rules
    categoryAllocationRules = defaultdict(list)
    shelf_numbers = {}

    for sr in shelf_rules:
        shelfId = sr.shelf_id
        shelf_numbers[shelfId] = sr.shelf_number
        for cr in sr.category_rules:
            categoryAllocationRules[shelfId].append(cr.category_name)

    for pp in pps:
        product = ProductDAO.get_by_id(pp.get('product_id'))
        if product.category.name not in categoryAllocationRules[pp.get('shelf_id')]:
            errors.append(f'Товар \'{product.name}\' не может быть размещён на полке. Т.к. категория \'{product.category.name}\' отсутствует среди указанных категорий для полки №{shelf_numbers[pp.get('shelf_id')]}')

    is_correct = False if len(errors) > 0 else True
    return is_correct, errors

def save_rule_for_planogram(planogram_id : int, rules : rules_data):
    existing_rule = RuleDAO.get_one(Rule(planogram_id=planogram_id))
    if existing_rule:
        RuleDAO.delete_by_id(existing_rule.id)

    global_rule = Rule(brand_sorting=rules.brand_sort, product_sorting=rules.product_sort, spacing = rules.spacing, planogram_id=planogram_id)
    global_rule_id = RuleDAO.add(global_rule).id

    for sr in rules.shelves_rules:
        sr_id = ShelfRuleDAO.add(ShelfRule(rule_id=global_rule_id, shelf_id=sr.shelf_id)).id
        cat_rules : list[CategoryRule] = []
        for cr in sr.category_rules:
            cat_rules.append(CategoryRule(share = cr.percentage, min_weight=cr.min_weight, max_weight=cr.max_weight, shelf_rule_id=sr_id, category_id=cr.category_id))
        CategoryRuleDAO.add_many(cat_rules)

@editor_bp.route('/save_planogram', methods=['POST'])
async def save_planogram():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    planogram_data = data.get('planogramData')

    planogram_id = planogram_data.get('id')
    name = planogram_data.get('name')
    shelf_unit_id = planogram_data.get('shelf_unit_id')
    placed_products_payload = planogram_data.get('placed_products', [])

    if not name or shelf_unit_id is None:
        return jsonify({"error": "Missing name or shelf_unit_id"}), 400
    
    rules = rules_data.from_dict(data.get('rules'))

    is_correct, error_messages = is_correct_planogram(placed_products_payload, rules)
    if is_correct:
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

            # Беру правила и сохраняю их с привязкой к планограмме + правила для полок + правила для категорий
            save_rule_for_planogram(planogram_id, rules)

            return jsonify(final_planogram_obj.to_dict()), 200

        except Exception as e:
            print(f"Error saving planogram: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({'errors': error_messages}), 200

@editor_bp.route('/chat_message', methods=['POST'])
async def message_handle():
    try: 
        data = request.get_json()
        if not data:
            return jsonify({"message": "Ошибка: Тело запроса не содержит JSON."}), 400
        
        user_message = data.get('message')
        planogram_data = data.get('planogram')
        rules = data.get('rules')

        if user_message is None:
            return jsonify({"message": "Ошибка: Ключ 'message' отсутствует в JSON."}), 400
        if not isinstance(user_message, str):
            return jsonify({"message": "Ошибка: Значение 'message' должно быть строкой."}), 400

        message = commands_handler(user_message, planogram_data, rules)

        return message.to_json(), 200

    except Exception as e:
        import traceback
        print("Critical error in /chat_message endpoint:")
        print(e)
        traceback.print_exc()
        return jsonify({
            "message": "Внутренняя ошибка сервера при обработке сообщения."
        }), 200

@editor_bp.route('/calculate_auto_placement', methods=['POST'])
def calculate_auto_placement_route():
    try: 
        data = request.get_json()
        if not data:
            return jsonify({"message": "Ошибка: Тело запроса не содержит JSON."}), 400
        
        rules = data.get('rules')
        shelf_unit_id = data.get('shelf_unit_id')
        planogram_id = data.get('planogram_id')
        planogram_name = data.get('planogram_name')

        if not rules or not shelf_unit_id:
            return jsonify({"message": "Ошибка: Запрос не содержит правила или ID стеллажа."}), 400

        server_message = calculate_auto_placement(shelf_unit_id, planogram_id, planogram_name, rules_data.from_dict(rules))
        return jsonify(server_message.to_json()), 200

    except AutoPlacementError as e:
        print(f"Ошибка авторасстановки: {e}")
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        print(f"Критическая ошибка в /calculate_auto_placement: {e}")
        # traceback.print_exc()
        return jsonify({
            "message": "Внутренняя ошибка сервера. Пожалуйста, обратитесь к администратору."
        }), 500

# # TODO Учитывать доли брендов на полках