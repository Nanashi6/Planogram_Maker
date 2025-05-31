from flask import Blueprint, render_template, jsonify, request
from DataLayer.dao import ProductDAO, ShelfUnitDAO, PlanogramDAO, PlacedProductDAO
from DataLayer.shemas import Planogram, PlacedProduct
from .commands_handlers import commands_handler

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
async def message_handle():
    try: 
        data = request.get_json()
        if not data:
            return jsonify({"reply": "Ошибка: Тело запроса не содержит JSON.", "parsed_command": None}), 400
        
        user_message = data.get('message')
        planogram_data = data.get('planogram')

        if user_message is None:
            return jsonify({"reply": "Ошибка: Ключ 'message' отсутствует в JSON.", "parsed_command": None}), 400
        if not isinstance(user_message, str):
            return jsonify({"reply": "Ошибка: Значение 'message' должно быть строкой.", "parsed_command": None}), 400

        message = commands_handler(user_message, planogram_data)

        return message.to_json(), 200

    except Exception as e:
        import traceback
        print("Critical error in /chat_message endpoint:")
        print(e)
        traceback.print_exc()
        return jsonify({
            "reply": "Внутренняя ошибка сервера при обработке сообщения чата.",
            "parsed_command": None
        }), 200 #FIXME Тут можно 200 код сделать и в чат ошибку выводить а не код ошибки

# def solve_dp_for_category(products: List[prod], max_weight: float, max_length: int) -> List[prod]: #FIXME реализовать автовыкладку
#     # FIXME Учитывать вес
    
#     N = len(products)
#     M = int(max_length * 10) # Миллиметры

#     dp = [[0 for _ in range(M + 1)] for _ in range(N + 1)]

#     for i in range(1, N + 1):
#         item_idx = i - 1
#         item_length = int(products[item_idx].depth * 10) # Миллиметры
#         item_cost = 1
#         for w in range(M + 1):
#             cost_without = dp[i-1][w]
#             cost_with = 0
#             if item_length <= w:
#                 cost_with = dp[i-1][w - item_length] + item_cost
#             dp[i][w] = max(cost_without, cost_with)

#     taken_products = []
#     current_w = M

#     for i in range(N, 0, -1):
#         item_idx = i - 1
#         item_length = int(products[item_idx].depth * 10) # Миллиметры
#         item_cost = 1
#         if item_length <= current_w and dp[i][current_w] != dp[i-1][current_w]:
#             taken_products.append(products[item_idx])
#             current_w -= item_length

#     return taken_products

@editor_bp.route('/calculate_auto_placement', methods=['POST'])
def calculate_auto_placement_route():
    return "", 200
    # data = request.get_json()
    # if not data:
    #     return jsonify({"error": "Invalid JSON payload"}), 400

    # shelf_unit_id = data.get('shelf_unit_id')
    # rules = data.get('rules') # Это будет словарь с 'global' и 'shelves'

    # if not shelf_unit_id or not rules:
    #     return jsonify({"error": "Missing shelf_unit_id or rules in payload"}), 400

    # print(f"Received Shelf Unit ID: {shelf_unit_id}")
    # print(f"Received Global Rules: {rules.get('global')}")
    # print(f"Received Shelf Specific Rules: {rules.get('shelves')}")

    # # Здесь ваша логика для получения данных стеллажа по shelf_unit_id,
    # # получения товаров, и применения правил (rules) для генерации планограммы.
    # # Это самая сложная часть, зависящая от вашей бизнес-логики.

    # # --- Начало примера логики обработки (очень упрощенно) ---
    # # 1. Получить данные стеллажа (shelf_unit_data) из БД по shelf_unit_id
    # # 2. Получить все товары (all_products_data) из БД
    # # 3. Применить global rules для общей сортировки товаров
    # # 4. Для каждой полки в shelf_unit_data:
    # #    - Найти соответствующие shelf-specific rules.
    # #    - Для каждой категории в правилах полки:
    # #        - Отфильтровать товары по категории.
    # #        - Применить product sorting rules (из global или специфичные для категории, если есть).
    # #        - Учесть вес, процент полки.
    # #        - Разместить товары на полке.
    # # 5. Сформировать `calculated_planogram_data` в том же формате, что и при загрузке планограммы.
    # # --- Конец примера логики обработки ---
    
    # # Предположим, вы сформировали calculated_planogram_data
    # # Это заглушка, замените реальной логикой
    # try:
    #     # Имитация вызова вашей основной функции расчета
    #     # from your_placement_logic_module import calculate_layout
    #     # calculated_planogram_data = calculate_layout(shelf_unit_id, rules, all_products_data)
        
    #     # Заглушка для демонстрации ответа
    #     # Найдите реальный стеллаж и его полки
    #     # shelf_unit_from_db = ShelfUnit.query.get(shelf_unit_id)
    #     # if not shelf_unit_from_db:
    #     #      return jsonify({"error": f"Shelf unit with ID {shelf_unit_id} not found"}), 404

    #     # Просто для примера: создаем пустую планограмму с названием
    #     # calculated_planogram_data = {
    #     #     "name": f"Auto-Rules for Unit {shelf_unit_from_db.shelf_unit_number}",
    #     #     "shelf_unit": shelf_unit_from_db.to_dict(rules=['shelves.products']), # Сериализуйте стеллаж
    #     #     "placed_products": [], # Здесь должны быть размещенные товары
    #     #     # "id": None, # т.к. это новая, не сохраненная планограмма
    #     # }
        
    #     # # Очень простой пример: взять первые N товаров и поместить их на первую полку
    #     # # Это НЕ РАБОЧИЙ КОД для реальной выкладки, а просто пример структуры ответа
    #     # if shelf_unit_from_db.shelves:
    #     #     first_shelf_db_id = shelf_unit_from_db.shelves[0].id
    #     #     # products_to_place = Product.query.limit(2).all() # взять первые 2 товара из БД
    #     #     # for i, p_to_place in enumerate(products_to_place):
    #     #     #     calculated_planogram_data["placed_products"].append({
    #     #     #         "product_id": p_to_place.id,
    #     #     #         "shelf_id": first_shelf_db_id,
    #     #     #         "position": i,
    #     #     #         "product": p_to_place.to_dict() # Включаем полные данные товара
    #     #     #     })
    #     #     # Заполните placed_products реальной логикой!

    #     # return jsonify(calculated_planogram_data), 200

    # except Exception as e:
    #     # import traceback
    #     # traceback.print_exc()
    #     return jsonify({"error": str(e)}), 500

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