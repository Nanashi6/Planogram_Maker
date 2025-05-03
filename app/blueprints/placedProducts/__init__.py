from flask import Blueprint, render_template, redirect, url_for
from DataLayer.dao import PlacedProductDAO
from .forms import *
from DataLayer.shemas import PlacedProduct

BASE_URL = 'placedProducts'
placedProducts_bp = Blueprint(BASE_URL, __name__, static_folder='static', template_folder='templates', url_prefix=f'/{BASE_URL}')

@placedProducts_bp.route('', methods=['GET'])
@placedProducts_bp.route('/', methods=['GET'])
async def read_all():
    return render_template(f'{BASE_URL}/index.html', placedProducts = PlacedProductDAO.get_all())

@placedProducts_bp.route('/<int:id>', methods=['GET'])
async def read(id: int):
    return render_template(f'{BASE_URL}/item.html', placedProducts = PlacedProductDAO.get_by_id(id))

@placedProducts_bp.route('/create', methods=['GET', 'POST'])
async def create():
    form = CreatePlacedProduct()
    if form.validate_on_submit():
        placed_product = PlacedProduct(
            shelf_id=form.shelf_id.data,
            product_id=form.product_id.data,
            planogram_id=form.planogram_id.data,
            position=form.position.data
        )
        PlacedProductDAO.add(placed_product)
        return redirect(url_for('.read_all'))
    return render_template(f'{BASE_URL}/create.html', title='Create Placed Product', form=form)

@placedProducts_bp.route('/update/<int:id>', methods=['GET', 'PUT'])
async def update(id: int):
    placed_product = PlacedProductDAO.get_by_id(id)
    if not placed_product:
        return "Placed product not found", 404

    form = UpdatePlacedProduct(obj=placed_product)
    if form.validate_on_submit():
        placed_product_data = PlacedProduct(
            id=id,
            shelf_id=form.shelf_id.data,
            product_id=form.product_id.data,
            planogram_id=form.planogram_id.data,
            position=form.position.data
        )
        PlacedProductDAO.update_by_id(id, placed_product_data)
        return redirect(url_for('.read_all'))
    return render_template(f'{BASE_URL}/update.html', title='Update Placed Product', form=form)

@placedProducts_bp.route('/delete/<int:id>', methods=['GET', 'DELETE'])
async def delete(id: int):
    product = PlacedProductDAO.get_by_id(id)
    if not product:
        return "ShelfUnit not found", 404

    PlacedProductDAO.delete_by_id(id)
    return redirect(url_for('.read_all'))