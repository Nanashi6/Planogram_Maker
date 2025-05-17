from flask import Blueprint, current_app, render_template, redirect, request, url_for
from DataLayer.dao import ShelfDAO
from .forms import *
from DataLayer.shemas import Shelf
from DataLayer.models import Shelf as S

BASE_URL = 'shelves'
shelves_bp = Blueprint(BASE_URL, __name__, static_folder='static', template_folder='templates', url_prefix=f'/{BASE_URL}')

@shelves_bp.route('', methods=['GET'])
@shelves_bp.route('/', methods=['GET'])
async def read_all():
    page = request.args.get('page', 1, type=int)
    per_page_from_config = current_app.config.get('ITEMS_PER_PAGE', 10)

    order_by_clauses = [S.id.asc()] 

    pagination = ShelfDAO.get_all_paginated(
        page=page,
        per_page=per_page_from_config,
        order_by_clauses=order_by_clauses
    )
    
    return render_template(f'{BASE_URL}/index.html',
                           shelves=pagination.items,
                           pagination=pagination)

@shelves_bp.route('/<int:id>', methods=['GET'])
async def read(id: int):
    return render_template(f'{BASE_URL}/item.html', shelf = ShelfDAO.get_by_id(id))

@shelves_bp.route('/create', methods=['GET', 'POST'])
async def create():
    form = CreateShelf()
    if form.validate_on_submit():
        shelf_data = Shelf(
            shelf_number=form.shelf_number.data,
            length=form.length.data,
            depth=form.depth.data,
            height=form.height.data,
            max_weight=form.max_weight.data,
            shelf_unit_id=form.shelf_unit_id.data
        )
        try:
            ShelfDAO.add(shelf_data)
            return redirect(url_for('.read_all'))
        except Exception as e:
            return redirect(url_for('.create'))
    return render_template(f'{BASE_URL}/create.html', title='Create Shelf', form=form)

@shelves_bp.route('/update/<int:id>', methods=['GET', 'POST'])
async def update(id: int):
    shelf = ShelfDAO.get_by_id(id)
    if not shelf:
        return redirect(url_for('.read_all'))

    form = UpdateShelf(obj=shelf)

    if form.validate_on_submit():
        shelf_data = Shelf(
            shelf_number=form.shelf_number.data,
            length=form.length.data,
            depth=form.depth.data,
            height=form.height.data,
            max_weight=form.max_weight.data,
            shelf_unit_id=form.shelf_unit_id.data
        )
        try:
            ShelfDAO.update_by_id(id, shelf_data)
            return redirect(url_for('.read_all'))
        except Exception as e:
            return redirect(url_for('.update', id=id))
    return render_template(f'{BASE_URL}/update.html', title='Update Shelf', form=form)

@shelves_bp.route('/delete/<int:id>', methods=['GET', 'DELETE'])
async def delete(id: int):
    shelf = ShelfDAO.get_by_id(id)
    if not shelf:
        return "Shelf not found", 404

    ShelfDAO.delete_by_id(id)
    return redirect(url_for('.read_all'))