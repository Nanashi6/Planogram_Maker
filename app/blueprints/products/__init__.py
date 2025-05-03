from flask import Blueprint, render_template, redirect, url_for
from DataLayer.dao import ProductDAO
from .forms import *
from DataLayer.shemas import Product

BASE_URL = 'products'
products_bp = Blueprint(BASE_URL, __name__, static_folder='static', template_folder='templates', url_prefix=f'/{BASE_URL}')

@products_bp.route('', methods=['GET'])
@products_bp.route('/', methods=['GET'])
async def read_all():
    return render_template(f'{BASE_URL}/index.html', products = ProductDAO.get_all())

@products_bp.route('/<int:id>', methods=['GET'])
async def read(id: int):
    return render_template(f'{BASE_URL}/item.html', products = ProductDAO.get_by_id(id))

@products_bp.route('/create', methods=['GET', 'POST'])
async def create():
    form = CreateProduct()
    if form.validate_on_submit():
        product_data = Product(
            segment=form.segment.data,
            product_name=form.product_name.data,
            barcode=form.barcode.data,
            SKU_rating=form.SKU_rating.data,
            length=form.length.data,
            depth=form.depth.data,
            height=form.height.data,
            weight=form.weight.data,
            price=form.price.data,
            category_id=form.category_id.data,
            brand_id=form.brand_id.data
        )
        try:
            ProductDAO.add(product_data)
            return redirect(url_for('.read_all'))
        except Exception as e:
            return redirect(url_for('.create'))
    return render_template(f'{BASE_URL}/create.html', title='Create Product', form=form)

@products_bp.route('/update/<int:id>', methods=['GET', 'PUT'])
async def update(id: int):
    product = ProductDAO.get_by_id(id)
    if not product:
        return redirect(url_for('.read_all'))

    form = UpdateProduct(obj=product)

    if form.validate_on_submit():
        product_data = Product(
            segment=form.segment.data,
            product_name=form.product_name.data,
            barcode=form.barcode.data,
            SKU_rating=form.SKU_rating.data,
            length=form.length.data,
            depth=form.depth.data,
            height=form.height.data,
            weight=form.weight.data,
            price=form.price.data,
            category_id=form.category_id.data,
            brand_id=form.brand_id.data
        )
        try:
            ProductDAO.update_by_id(id, product_data)
            return redirect(url_for('.read_all'))
        except Exception as e:
            return redirect(url_for('.update', id=id))
    return render_template(f'{BASE_URL}/update.html', title='Update Product', form=form)

@products_bp.route('/delete/<int:id>', methods=['GET', 'DELETE'])
async def delete(id: int):
    product = ProductDAO.get_by_id(id)
    if not product:
        return "Product not found", 404

    ProductDAO.delete_by_id(id)
    return redirect(url_for('.read_all'))