from flask import Blueprint, current_app, render_template, redirect, request, url_for
from DataLayer.dao import ShelfUnitDAO
from .forms import *
from DataLayer.shemas import ShelfUnit
from DataLayer.models import ShelfUnit as SU

BASE_URL = 'shelfUnits'
shelfUnits_bp = Blueprint(BASE_URL, __name__, static_folder='static', template_folder='templates', url_prefix=f'/{BASE_URL}')

@shelfUnits_bp.route('', methods=['GET'])
@shelfUnits_bp.route('/', methods=['GET'])
async def read_all():
    page = request.args.get('page', 1, type=int)
    per_page_from_config = current_app.config.get('ITEMS_PER_PAGE', 10)

    order_by_clauses = [SU.shelf_unit_number.asc()] 

    pagination = ShelfUnitDAO.get_all_paginated(
        page=page,
        per_page=per_page_from_config,
        order_by_clauses=order_by_clauses
    )
    
    return render_template(f'{BASE_URL}/index.html',
                           shelfUnits=pagination.items,
                           pagination=pagination)

@shelfUnits_bp.route('/<int:id>', methods=['GET'])
async def read(id: int):
    return render_template(f'{BASE_URL}/item.html', shelfUnit = ShelfUnitDAO.get_by_id(id))

@shelfUnits_bp.route('/create', methods=['GET', 'POST'])
async def create():
    form = CreateShelfUnit()
    if form.validate_on_submit():
        shelf_unit_data = ShelfUnit(
            shelf_unit_number=form.shelf_unit_number.data
        )
        try:
            ShelfUnitDAO.add(shelf_unit_data)
            return redirect(url_for('.read_all'))
        except Exception as e:
            return redirect(url_for('.create'))
    return render_template(f'{BASE_URL}/create.html', title='Create Shelf Unit', form=form)

@shelfUnits_bp.route('/update/<int:id>', methods=['GET', 'POST'])
async def update(id: int):
    shelf_unit = ShelfUnitDAO.get_by_id(id)
    if not shelf_unit:
        return redirect(url_for('.read_all'))

    form = UpdateShelfUnit(obj=shelf_unit)

    if form.validate_on_submit():
        shelf_unit_data = ShelfUnit(
            shelf_unit_number=form.shelf_unit_number.data
        )
        try:
            ShelfUnitDAO.update_by_id(id, shelf_unit_data)
            return redirect(url_for('.read_all'))
        except Exception as e:
            return redirect(url_for('.update', id=id))
    return render_template(f'{BASE_URL}/update.html', title='Update Shelf Unit', form=form)

@shelfUnits_bp.route('/delete/<int:id>', methods=['GET', 'DELETE'])
async def delete(id: int):
    shelfUnit = ShelfUnitDAO.get_by_id(id)
    if not shelfUnit:
        return "ShelfUnit not found", 404

    ShelfUnitDAO.delete_by_id(id)
    return redirect(url_for('.read_all'))