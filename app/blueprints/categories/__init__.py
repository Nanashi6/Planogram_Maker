from flask import Blueprint, current_app, render_template, redirect, request, url_for
from DataLayer.dao import CategoryDAO
from .forms import *
from DataLayer.shemas import Category
from DataLayer.models import Category as C

BASE_URL = 'categories'
categories_bp = Blueprint(BASE_URL, __name__, static_folder='static', template_folder='templates', url_prefix=f'/{BASE_URL}')

@categories_bp.route('', methods=['GET'])
@categories_bp.route('/', methods=['GET'])
async def read_all():
    page = request.args.get('page', 1, type=int)
    per_page_from_config = current_app.config.get('ITEMS_PER_PAGE', 10)

    order_by_clauses = [C.name.asc()]

    pagination = CategoryDAO.get_all_paginated(
        page=page,
        per_page=per_page_from_config,
        order_by_clauses=order_by_clauses
    )
    return render_template(f'{BASE_URL}/index.html',
                           categories=pagination.items,
                           pagination=pagination)

@categories_bp.route('/<int:id>', methods=['GET'])
async def read(id: int):
    return render_template(f'{BASE_URL}/item.html', category = CategoryDAO.get_by_id(id))

@categories_bp.route('/create', methods=['GET', 'POST'])
async def create():
    form = CreateCategory()
    if form.validate_on_submit():
        category = Category(name=form.name.data, share=form.share.data)
        CategoryDAO.add(category)
        return redirect(url_for('.read_all'))
    return render_template(f'{BASE_URL}/create.html', title='Home', form=form)

@categories_bp.route('/update/<int:id>', methods=['GET', 'POST'])
async def update(id: int):
    category = CategoryDAO.get_by_id(id)
    if not category:
        return "Category not found", 404
    
    form = UpdateCategory(obj=category)
    if form.validate_on_submit():
        category1 = Category(name=form.name.data, share=form.share.data)
        CategoryDAO.update_by_id(id, category1)
        return redirect(url_for('.read_all'))
    return render_template(f'{BASE_URL}/update.html', title='Home', form=form)

@categories_bp.route('/delete/<int:id>', methods=['GET', 'DELETE'])
async def delete(id: int):
    category = CategoryDAO.get_by_id(id)
    if not category:
        return "Category not found", 404
    
    CategoryDAO.delete_by_id(id)
    return redirect(url_for('.read_all'))