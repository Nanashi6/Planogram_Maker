from typing import Dict, List, Type
from flask import Blueprint, render_template, jsonify, request
from DataLayer.dao import ProductDAO, ShelfUnitDAO, PlanogramDAO, PlacedProductDAO
from DataLayer.shemas import Planogram, PlacedProduct
from .enums import *
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
    brand_sort_labels = {
        BrandSorting.RatingDesc.value: 'Rating (High to Low)',
        BrandSorting.RatingAsc.value: 'Rating (Low to High)',
        BrandSorting.NameAsc.value: 'Alphabetical (A-Z)',
        BrandSorting.NameDesc.value: 'Alphabetical (Z-A)',
    }

    product_sort_labels = {
        ProductSorting.PriceAsc.value: 'Price (Low to High)',
        ProductSorting.PriceDesc.value: 'Price (High to Low)',
        ProductSorting.RatingDesc.value: 'Sales Rating (High to Low)', # Метка из вашей формы
        ProductSorting.RatingAsc.value: 'Sales Rating (Low to High)',   # Метка из вашей формы
        ProductSorting.NameAsc.value: 'Alphabetical (A-Z)',
        ProductSorting.NameDesc.value: 'Alphabetical (Z-A)',
    }

    brand_sorting_options = enum_to_select_options(BrandSorting, brand_sort_labels)
    product_sorting_options = enum_to_select_options(ProductSorting, product_sort_labels)

    sorting_rules = {
        "brand_sort_options": brand_sorting_options,
        "product_sort_options": product_sorting_options,
        "defaults": {
            "brand_sort": BrandSorting.RatingDesc.value,
            "product_sort": ProductSorting.PriceAsc.value
        }
    }
    return jsonify(sorting_rules)

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
            "message": "Внутренняя ошибка сервера при обработке сообщения чата."
        }), 200

@editor_bp.route('/calculate_auto_placement', methods=['POST'])
def calculate_auto_placement_route():
    try: 
        data = request.get_json()
        if not data:
            return jsonify({"message": "Ошибка: Тело запроса не содержит JSON."}), 400
        
        rules = data.get('rules')
        shelf_unit_id = data.get('shelf_unit_id')

        if not rules or not shelf_unit_id:
            return jsonify({"message": "Ошибка: Запрос не содержит правила или указатель на стеллаж."}), 400

        server_message = calculate_auto_placement(shelf_unit_id, rules_data.from_dict(rules))    

        return jsonify(server_message.to_json()), 200

    except Exception as e:
        print("Critical error in /calculate_auto_placement endpoint")
        return jsonify({
            "message": "Внутренняя ошибка сервера при обработке сообщения чата."
        }), 200

# # TODO Учитывать доли категорий на полках
# # TODO Учитывать доли брендов на полках
# # TODO Убрать дубляжи товаров на разных полках

# # TODO Дополнительные фейсинги
# # TODO Сортировать товары по правилам из JSON

# # IDEA Формализованный чат с последовательными инструкциями (МБ с подсказками всплывающими)
# # IDEA "1 Полка для категорий ...,...,...", "Порядок сортировок По категориям, По рейтингу бренда, По цене товара", 


            # calculated_planogram_response = {
            #     "id": None,
            #     "name": f"Выкладка для стеллажа {shelf_unit_model.shelf_unit_number}",
            #     "shelf_unit": shelf_unit_model.to_dict(),
            #     "placed_products": placed_products_list
            # }
            

			# ТОВАР для клиента
                                # placed_products_list.append({
                                #     "shelf_id": shelf_id,
                                #     "product_id": product.id,
                                #     "position": ind,
                                #     "product": product.to_dict() # Полные данные о товаре для клиента
                                # })