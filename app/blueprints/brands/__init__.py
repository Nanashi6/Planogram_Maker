from flask import Blueprint, render_template, redirect, url_for, request, current_app
from DataLayer.dao import BrandDAO
from .forms import *
from DataLayer.shemas import Brand
from DataLayer.models import Brand as B

BASE_URL = 'brands'
brands_bp = Blueprint(BASE_URL, __name__, static_folder='static', template_folder='templates', url_prefix=f'/{BASE_URL}')

@brands_bp.route('', methods=['GET'])
@brands_bp.route('/', methods=['GET'])
async def read_all():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)

    order_by_clauses = [B.name.asc()]

    pagination = BrandDAO.get_all_paginated(
        page=page,
        per_page=per_page,
        order_by_clauses=order_by_clauses
    )

    return render_template(f'{BASE_URL}/index.html',
                           brands=pagination.items,
                           pagination=pagination)

@brands_bp.route('/<int:id>', methods=['GET'])
async def read(id: int):
    return render_template(f'{BASE_URL}/item.html', brand = BrandDAO.get_by_id(id))

@brands_bp.route('/create', methods=['GET', 'POST'])
async def create():
    form = CreateBrand()
    if form.validate_on_submit():
        brand = Brand(name=form.name.data, share=form.share.data, rating=form.rating.data, category_id=form.category_id.data,)
        BrandDAO.add(brand)
        return redirect(url_for('.read_all'))
    return render_template(f'{BASE_URL}/create.html', title='Home', form=form)

@brands_bp.route('/update/<int:id>', methods=['GET', 'POST'])
async def update(id: int):
    brand = BrandDAO.get_by_id(id)
    if not brand:
        return "Brand not found", 404
    
    form = UpdateBrand(obj=brand)
    if form.validate_on_submit():
        brand1 = Brand(name=form.name.data, share=form.share.data, rating=form.rating.data, category_id=form.category_id.data,)
        BrandDAO.update_by_id(id, brand1)
        return redirect(url_for('.read_all'))
    return render_template(f'{BASE_URL}/update.html', title='Home', form=form)

@brands_bp.route('/delete/<int:id>', methods=['GET', 'DELETE'])
async def delete(id: int):
    brand = BrandDAO.get_by_id(id)
    if not brand:
        return "Brand not found", 404
    
    BrandDAO.delete_by_id(id)
    return redirect(url_for('.read_all'))