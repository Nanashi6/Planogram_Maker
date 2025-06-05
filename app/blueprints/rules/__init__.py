from flask import Blueprint, current_app, render_template, redirect, request, url_for
from DataLayer.dao import RuleDAO
from .forms import CreateRule, UpdateRule
from DataLayer.shemas import Rule
from DataLayer.models import Rule as RuleModel
from DataLayer.enums import BrandSorting, ProductSorting #

BASE_URL = 'rules' 
rules_bp = Blueprint(BASE_URL, __name__, static_folder='static', template_folder='templates', url_prefix=f'/{BASE_URL}')

@rules_bp.route('', methods=['GET'])
@rules_bp.route('/', methods=['GET'])
async def read_all():
    page = request.args.get('page', 1, type=int)
    per_page_from_config = current_app.config.get('ITEMS_PER_PAGE', 10)

    order_by_clauses = [RuleModel.id.asc()]

    pagination = RuleDAO.get_all_paginated(
        page=page,
        per_page=per_page_from_config,
        order_by_clauses=order_by_clauses
    )

    return render_template(f'{BASE_URL}/index.html',
                           rules=pagination.items, 
                           pagination=pagination,
                           title="Правила выкладки")

@rules_bp.route('/<int:id>', methods=['GET'])
async def read(id: int):
    rule_item = RuleDAO.get_by_id(id) 
    if not rule_item:
        print('Правило не найдено.', 'warning')
        return redirect(url_for('.read_all'))
    return render_template(f'{BASE_URL}/item.html', rule=rule_item, title=f"Детали правила ID {rule_item.id}")

@rules_bp.route('/create', methods=['GET', 'POST'])
async def create():
    form = CreateRule()
    if form.validate_on_submit():
        brand_sorting_enum = BrandSorting(form.brand_sorting.data)
        product_sorting_enum = ProductSorting(form.product_sorting.data)

        planogram_id_data = form.planogram_id.data
        if isinstance(planogram_id_data, str) and not planogram_id_data.strip(): 
            planogram_id_data = None
        elif planogram_id_data == 0 : 
             planogram_id_data = None


        rule_data = Rule( 
            brand_sorting=brand_sorting_enum,
            product_sorting=product_sorting_enum,
            spacing=form.spacing.data,
            planogram_id=planogram_id_data
        )
        try:
            RuleDAO.add(rule_data)
            print('Новое правило успешно создано!', 'success')
            return redirect(url_for('.read_all'))
        except Exception as e:
            print(f'Ошибка при создании правила: {e}', 'danger')
    return render_template(f'{BASE_URL}/create.html', title='Создать новое правило', form=form)

@rules_bp.route('/update/<int:id>', methods=['GET', 'POST'])
async def update(id: int):
    rule_to_update = RuleDAO.get_by_id(id)
    if not rule_to_update:
        print('Правило не найдено.', 'warning')
        return redirect(url_for('.read_all'))

    form_obj_data = {
        'brand_sorting': rule_to_update.brand_sorting.value if rule_to_update.brand_sorting else None,
        'product_sorting': rule_to_update.product_sorting.value if rule_to_update.product_sorting else None,
        'spacing': rule_to_update.spacing,
        'planogram_id': rule_to_update.planogram_id,
        'id' : rule_to_update.id
    }
    form = UpdateRule(data=form_obj_data) 

    if form.validate_on_submit():
        brand_sorting_enum = BrandSorting(form.brand_sorting.data)
        product_sorting_enum = ProductSorting(form.product_sorting.data)

        planogram_id_data = form.planogram_id.data
        if isinstance(planogram_id_data, str) and not planogram_id_data.strip():
            planogram_id_data = None
        elif planogram_id_data == 0 :
             planogram_id_data = None

        rule_data_for_update = Rule(
            brand_sorting=brand_sorting_enum,
            product_sorting=product_sorting_enum,
            spacing=form.spacing.data,
            planogram_id=planogram_id_data
        )
        try:
            RuleDAO.update_by_id(id, rule_data_for_update)
            print('Правило успешно обновлено!', 'success')
            return redirect(url_for('.read', id=id)) 
        except Exception as e:
            print(f'Ошибка при обновлении правила: {e}', 'danger')
    return render_template(f'{BASE_URL}/update.html', title=f'Изменить правило ID {id}', form=form)

@rules_bp.route('/delete/<int:id>', methods=['GET', 'POST'])
async def delete(id: int):
    rule_to_delete = RuleDAO.get_by_id(id)
    if not rule_to_delete:
        print('Правило не найдено.', 'warning')
        return redirect(url_for('.read_all'))

    try:
        RuleDAO.delete_by_id(id)
        print(f'Правило ID {id} успешно удалено.', 'success')
    except Exception as e:
        print(f'Ошибка при удалении правила: {e}', 'danger')
    return redirect(url_for('.read_all'))