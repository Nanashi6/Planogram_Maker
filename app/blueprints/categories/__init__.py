from flask import Blueprint, render_template, redirect, url_for
from DataLayer.dao import CategoryDAO
from .forms import *
from DataLayer.shemas import Category

BASE_URL = 'categories'
categories_bp = Blueprint(BASE_URL, __name__, static_folder='static', template_folder='templates', url_prefix=f'/{BASE_URL}')

@categories_bp.route('', methods=['GET'])
@categories_bp.route('/', methods=['GET'])
async def read_all():
    return render_template(f'{BASE_URL}/index.html', categories = CategoryDAO.get_all())

@categories_bp.route('/<int:id>', methods=['GET'])
async def read(id: int):
    return render_template(f'{BASE_URL}/item.html', categories = CategoryDAO.get_by_id(id))

@categories_bp.route('/create', methods=['GET', 'POST'])
async def create():
    form = CreateCategory()
    if form.validate_on_submit():
        category = Category(name=form.name.data, share=form.share.data)
        CategoryDAO.add(category)
        return redirect(url_for('.read_all'))
    return render_template(f'{BASE_URL}/create.html', title='Home', form=form)

@categories_bp.route('/update/<int:id>', methods=['GET', 'PUT'])
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

@categories_bp.route('/delete/<int:id>', methods=['DELETE'])
async def delete(id: int):
    category = CategoryDAO.get_by_id(id)
    if not category:
        return "Category not found", 404
    
    CategoryDAO.delete_by_id(id)
    return redirect(url_for('.read_all'))