from flask import Blueprint, current_app, render_template, redirect, request, url_for, flash
from DataLayer.dao import CategoryBrandPlacementDAO
from .forms import CreateCategoryBrandPlacementForm, UpdateCategoryBrandPlacementForm
from DataLayer.models import CategoryBrandPlacement as CBPModel
from DataLayer.shemas import CategoryBrandPlacement as CategoryBrandPlacementSchema

BASE_URL = 'categoryBrandPlacements'
cbp_bp = Blueprint(
    BASE_URL,
    __name__, 
    static_folder='static', 
    template_folder='templates', 
    url_prefix=f'/{BASE_URL}'
)

@cbp_bp.route('', methods=['GET'])
@cbp_bp.route('/', methods=['GET'])
async def read_all():
    page = request.args.get('page', 1, type=int)
    per_page_from_config = current_app.config.get('ITEMS_PER_PAGE', 10)

    order_by_clauses = [CBPModel.id.asc()]

    pagination = CategoryBrandPlacementDAO.get_all_paginated(
        page=page,
        per_page=per_page_from_config,
        order_by_clauses=order_by_clauses
    )

    return render_template(f'{BASE_URL}/index.html',
                           title='Category-Brand Placements',
                           placements=pagination.items,
                           pagination=pagination)

@cbp_bp.route('/<int:id>', methods=['GET'])
async def read(id: int):
    placement = CategoryBrandPlacementDAO.get_by_id(id)
    if not placement:
        return redirect(url_for(f'.read_all'))
    return render_template(f'{BASE_URL}/item.html',
                           title=f"Placement: {placement.category.name} - {placement.brand.name}",
                           placement=placement)

@cbp_bp.route('/create', methods=['GET', 'POST'])
async def create():
    form = CreateCategoryBrandPlacementForm()
    if form.validate_on_submit():
        placement_data = CategoryBrandPlacementSchema(
            category_id=form.category_id.data,
            brand_id=form.brand_id.data,
            share=form.share.data if form.share.data is not None else None
        )
        try:
            CategoryBrandPlacementDAO.add(placement_data)
            return redirect(url_for(f'.read_all'))
        except Exception as e:
            return redirect(url_for('.create'))

    return render_template(f'{BASE_URL}/create.html',
                           title='Create Category-Brand Placement',
                           form=form)

@cbp_bp.route('/update/<int:id>', methods=['GET', 'POST'])
async def update(id: int):
    placement = CategoryBrandPlacementDAO.get_by_id(id)
    if not placement:
        return redirect(url_for(f'.read_all'))

    form = UpdateCategoryBrandPlacementForm(obj=placement)

    if form.validate_on_submit():
        placement_update_data = CategoryBrandPlacementSchema(
            category_id=form.category_id.data,
            brand_id=form.brand_id.data,
            share=form.share.data if form.share.data is not None else None,
            id=id
        )
        try:
            CategoryBrandPlacementDAO.update_by_id(id, placement_update_data)
            return redirect(url_for('.read_all'))
        except Exception as e:
            return redirect(url_for('.update', id=id))

    return render_template(f'{BASE_URL}/update.html',
                           title=f"Update Placement: {placement.category.name} - {placement.brand.name}",
                           form=form,
                           placement_id=id) 

@cbp_bp.route('/delete/<int:id>', methods=['GET', 'POST'])
async def delete(id: int):
    placement = CategoryBrandPlacementDAO.get_by_id(id)
    if not placement:
        return redirect(url_for(f'.read_all'))
        
    CategoryBrandPlacementDAO.delete_by_id(id)
    return redirect(url_for(f'.read_all'))