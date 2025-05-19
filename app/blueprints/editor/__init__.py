from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from DataLayer.dao import ProductDAO, ShelfUnitDAO, PlanogramDAO, PlacedProductDAO
from DataLayer.shemas import Planogram, PlacedProduct

import json

BASE_URL = 'editor'
editor_bp = Blueprint(BASE_URL, __name__, static_folder='static', template_folder='templates', url_prefix=f'/{BASE_URL}')

@editor_bp.route('', methods=['GET'])
@editor_bp.route('/', methods=['GET'])
async def index():
    return render_template(f'{BASE_URL}/index.html')

@editor_bp.route('/get_products', methods=['GET'])
async def get_products(): # TODO Можно получать товары по указанным фильтрам (товары конкретных категорий или КОЛЛЕКЦИЙ)
                            # FIXME Можно Эту функцию полностью на модуль продуктов переложить
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
    


# FIXME Реализовать детерминированную автовыкладку
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

            # Итерация по полкам стеллажа (отсортированным по номеру)
            sorted_shelves_from_db = sorted(shelf_unit_model.shelves, key=lambda s: s.shelf_number)
            placed_products_list = []

            for shelf_model in sorted_shelves_from_db:
                shelf_db_id = shelf_model.id
                shelf_number_in_rules = shelf_model.shelf_number # Номер полки для поиска в правилах

                # Найти правила для текущей полки
                shelf_rule_data = next((r for r in parsed_rules.get("product_rules", {}).get("shelf", []) if r.get("number") == shelf_number_in_rules), None)
                if not shelf_rule_data:
                    print(f"Правила для полки номер {shelf_number_in_rules} не найдены, полка пропускается.")
                    continue

                # TODO Сортировать товары по категориям и правилам из JSON
                products_for_shelf = ProductDAO.get_products_by_categories_and_weight(shelf_rule_data.get("category", []), shelf_model.height - vertical_space)

                free_len = shelf_model.length
                free_weights = shelf_model.max_weight
                position_counter = 0

                for product in products_for_shelf:
                    if free_len - product.depth >= 0 and free_weights - product.weight >= 0:
                        placed_products_list.append({
                            "shelf_id": shelf_db_id,
                            "product_id": product.id,
                            "position": position_counter,
                            "product": product.to_dict() # Полные данные о товаре для клиента
                        })
                        position_counter += 1
                        free_len -= product.depth + product_spacing
                        free_weights -= product.weight

            calculated_planogram_response = {
                "id": None,
                "name": f"Автовыкладка для стеллажа {shelf_unit_model.shelf_unit_number}",
                "shelf_unit": shelf_unit_model.to_dict(),
                "placed_products": placed_products_list
            }
            
            return jsonify(calculated_planogram_response), 200

        except json.JSONDecodeError:
            return jsonify({"error": "Ошибка парсинга файла правил (неверный JSON)"}), 400
        except Exception as e:
            print(f"Ошибка при обработке файла правил: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Ошибка сервера при обработке правил: {str(e)}"}), 500
    else:
        return jsonify({"error": "Неподдерживаемый тип файла или ошибка файла"}), 400