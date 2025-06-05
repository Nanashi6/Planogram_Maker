from flask import Blueprint, current_app, render_template, redirect, request, url_for
from DataLayer.dao import ShelfRuleDAO 
from .forms import CreateShelfRule, UpdateShelfRule
from DataLayer.shemas import ShelfRule 
from DataLayer.models import ShelfRule as ShelfRuleModel 

BASE_URL = 'shelf-rules'
shelf_rules_bp = Blueprint(BASE_URL, __name__, static_folder='static', template_folder='templates', url_prefix=f'/{BASE_URL}')

@shelf_rules_bp.route('', methods=['GET'])
@shelf_rules_bp.route('/', methods=['GET'])
async def read_all():
    page = request.args.get('page', 1, type=int)
    per_page_from_config = current_app.config.get('ITEMS_PER_PAGE', 10)

    order_by_clauses = [ShelfRuleModel.id.asc()]

    pagination = ShelfRuleDAO.get_all_paginated(
        page=page,
        per_page=per_page_from_config,
        order_by_clauses=order_by_clauses
    )

    return render_template(f'{BASE_URL}/index.html',
                           shelf_rules_list=pagination.items,
                           pagination=pagination,
                           title="Правила для полок")

@shelf_rules_bp.route('/<int:id>', methods=['GET'])
async def read(id: int):
    shelf_rule_item = ShelfRuleDAO.get_by_id(id)
    if not shelf_rule_item:
        print('Правило для полки не найдено.', 'warning')
        return redirect(url_for('.read_all'))
    return render_template(f'{BASE_URL}/item.html', shelf_rule=shelf_rule_item, title=f"Детали правила для полки ID {shelf_rule_item.id}")

@shelf_rules_bp.route('/create', methods=['GET', 'POST'])
async def create():
    form = CreateShelfRule()
    if form.validate_on_submit():
        if not form.rule_id.data or not form.shelf_id.data:
            if not form.rule_id.data:
                 form.rule_id.errors.append("Необходимо выбрать общее правило.")
            if not form.shelf_id.data:
                form.shelf_id.errors.append("Необходимо выбрать полку.")
            return render_template(f'{BASE_URL}/create.html', title='Создать правило для полки', form=form)

        shelf_rule_data = ShelfRule(
            rule_id=form.rule_id.data,
            shelf_id=form.shelf_id.data
        )
        try:
            new_shelf_rule = ShelfRuleDAO.add(shelf_rule_data)
            print('Новое правило для полки успешно создано!', 'success')
            return redirect(url_for('.read', id=new_shelf_rule.id))
        except Exception as e:
            print(f'Ошибка при создании правила для полки: {e}', 'danger')
    return render_template(f'{BASE_URL}/create.html', title='Создать правило для полки', form=form)

@shelf_rules_bp.route('/update/<int:id>', methods=['GET', 'POST'])
async def update(id: int):
    shelf_rule_to_update = ShelfRuleDAO.get_by_id(id)
    if not shelf_rule_to_update:
        print('Правило для полки не найдено.', 'warning')
        return redirect(url_for('.read_all'))

    form = UpdateShelfRule(obj=shelf_rule_to_update)

    if form.validate_on_submit():
        if not form.rule_id.data or not form.shelf_id.data:
            if not form.rule_id.data:
                 form.rule_id.errors.append("Необходимо выбрать общее правило.")
            if not form.shelf_id.data:
                form.shelf_id.errors.append("Необходимо выбрать полку.")
            return render_template(f'{BASE_URL}/update.html', title=f'Изменить правило для полки ID {id}', form=form)

        shelf_rule_data_for_update = ShelfRule(
            rule_id=form.rule_id.data,
            shelf_id=form.shelf_id.data
        )
        try:
            ShelfRuleDAO.update_by_id(id, shelf_rule_data_for_update)
            print('Правило для полки успешно обновлено!', 'success')
            return redirect(url_for('.read', id=id))
        except Exception as e:
            print(f'Ошибка при обновлении правила для полки: {e}', 'danger')
    return render_template(f'{BASE_URL}/update.html', title=f'Изменить правило для полки ID {id}', form=form)

@shelf_rules_bp.route('/delete/<int:id>', methods=['GET', 'POST'])
async def delete(id: int):
    shelf_rule_to_delete = ShelfRuleDAO.get_by_id(id)
    if not shelf_rule_to_delete:
        print('Правило для полки не найдено.', 'warning')
        return redirect(url_for('.read_all'))

    try:
        ShelfRuleDAO.delete_by_id(id)
        print(f'Правило для полки ID {id} и все связанные правила категорий успешно удалены.', 'success')
    except Exception as e:
        print(f'Ошибка при удалении правила для полки: {e}', 'danger')
    return redirect(url_for('.read_all'))