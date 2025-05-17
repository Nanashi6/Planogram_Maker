from flask import Blueprint, current_app, render_template, redirect, request, url_for
from DataLayer.dao import PlanogramDAO
from .forms import *
from DataLayer.shemas import Planogram
from DataLayer.models import Planogram as P
from datetime import datetime

BASE_URL = 'planograms'
planograms_bp = Blueprint(BASE_URL, __name__, static_folder='static', template_folder='templates', url_prefix=f'/{BASE_URL}')

@planograms_bp.route('', methods=['GET'])
@planograms_bp.route('/', methods=['GET'])
async def read_all():
    page = request.args.get('page', 1, type=int)
    per_page_from_config = current_app.config.get('ITEMS_PER_PAGE', 10)

    order_by_clauses = [P.name.asc()] 

    pagination = PlanogramDAO.get_all_paginated(
        page=page,
        per_page=per_page_from_config,
        order_by_clauses=order_by_clauses
    )
    
    return render_template(f'{BASE_URL}/index.html',
                           planograms=pagination.items,
                           pagination=pagination)

@planograms_bp.route('/<int:id>', methods=['GET'])
async def read(id: int):
    return render_template(f'{BASE_URL}/item.html', planogram = PlanogramDAO.get_by_id(id))

@planograms_bp.route('/create', methods=['GET', 'POST'])
async def create():
    form = CreatePlanogram()
    if form.validate_on_submit():
        planogram = Planogram(name=form.name.data, shelf_unit_id=form.shelf_unit_id.data, created_at=datetime.now())
        PlanogramDAO.add(planogram)
        return redirect(url_for('.read_all'))
    return render_template(f'{BASE_URL}/create.html', title='Create Planogram', form=form)

@planograms_bp.route('/update/<int:id>', methods=['GET', 'POST'])
async def update(id: int):
    planogram = PlanogramDAO.get_by_id(id)
    if not planogram:
        return "Planogram not found", 404

    form = UpdatePlanogram(obj=planogram)
    if form.validate_on_submit():
        planogram_data = Planogram(
            id=id,
            name=form.name.data,
            shelf_unit_id=form.shelf_unit_id.data,
            created_at=planogram.created_at  # Сохраняем время создания
        )
        PlanogramDAO.update_by_id(id, planogram_data)
        return redirect(url_for('.read_all'))
    return render_template(f'{BASE_URL}/update.html', title='Update Planogram', form=form)

@planograms_bp.route('/delete/<int:id>', methods=['GET', 'DELETE'])
async def delete(id: int):
    planogram = PlanogramDAO.get_by_id(id)
    if not planogram:
        return "ShelfUnit not found", 404

    PlanogramDAO.delete_by_id(id)
    return redirect(url_for('.read_all'))