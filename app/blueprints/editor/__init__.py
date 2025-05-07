from flask import Blueprint, render_template, redirect, url_for, jsonify
from DataLayer.dao import ProductDAO

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

