from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from DataLayer.dao import ProductDAO, ShelfUnitDAO, PlanogramDAO, PlacedProductDAO
from DataLayer.shemas import Planogram, PlacedProduct

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
            # PlacedProductDAO.delete_by_planogram_id(planogram_id)
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
            # Данные стеллажа
            shelf_unit = ShelfUnitDAO.get_by_id(shelf_unit_id)
            if not shelf_unit:
                return jsonify({"error": f"Стеллаж с ID {shelf_unit_id} не найден"}), 404

            # ЗАГЛУШКА ДЛЯ ЛОГИКИ АВТОВЫКЛАДКИ
            print(f"Получен файл правил: {rules_file.filename} для стеллажа ID: {shelf_unit_id}")
            
            all_products = ProductDAO.get_all()
            placed_products_list = []
            
            if shelf_unit.shelves and len(shelf_unit.shelves) > 0:
                first_shelf_db_id = shelf_unit.shelves[0].id

                if len(all_products) >= 2:
                    product1 = all_products[0]
                    product2 = all_products[1]
                    shelf1_db_id = shelf_unit.shelves[0].id

                    placed_products_list.append({
                        "shelf_id": shelf1_db_id,
                        "product_id": product1.id,
                        "position": 0,
                        "product": product1.to_dict()
                    })
                    placed_products_list.append({
                        "shelf_id": shelf1_db_id,
                        "product_id": product2.id,
                        "position": 1,
                        "product": product2.to_dict()
                    })
            # КОНЕЦ ЗАГЛУШКИ

            calculated_planogram_response = {
                "id": None,
                "name": f"Автовыкладка для стеллажа {shelf_unit.shelf_unit_number}",
                "shelf_unit": shelf_unit.to_dict(),
                "placed_products": placed_products_list
            }
            
            return jsonify(calculated_planogram_response), 200

        except Exception as e:
            print(f"Ошибка при обработке файла правил: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Ошибка сервера при обработке правил: {str(e)}"}), 500
    else:
        return jsonify({"error": "Неподдерживаемый тип файла или ошибка файла"}), 400