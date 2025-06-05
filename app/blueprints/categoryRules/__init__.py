from flask import Blueprint, current_app, render_template, redirect, request, url_for
from flask import flash 
from DataLayer.dao import CategoryRuleDAO, ShelfRuleDAO, CategoryDAO 
from .forms import CreateCategoryRule, UpdateCategoryRule
from DataLayer.shemas import CategoryRule


BASE_URL = 'category-rules'
category_rules_bp = Blueprint(
    BASE_URL,
    __name__,
    static_folder='static', 
    template_folder='templates',
    url_prefix=f'/{BASE_URL}'
)

@category_rules_bp.route('', methods=['GET'])
@category_rules_bp.route('/', methods=['GET'])
async def read_all():
    page = request.args.get('page', 1, type=int)
    per_page_from_config = current_app.config.get('ITEMS_PER_PAGE', 15)

    order_by_clauses = ["shelf_rule_id", "category_id"] 

    pagination = CategoryRuleDAO.get_all_paginated(
        page=page,
        per_page=per_page_from_config,
        order_by_clauses=order_by_clauses
    )

    return render_template(f'{BASE_URL}/index.html',
                           category_rules_list=pagination.items,
                           pagination=pagination,
                           title="Правила категорий")

@category_rules_bp.route('/<int:id>', methods=['GET'])
async def read(id: int):
    category_rule_item = CategoryRuleDAO.get_by_id(id)
    if not category_rule_item:
        print('Правило категории не найдено.', 'warning')
        return redirect(url_for(f'.{BASE_URL}_read_all'))
    return render_template(f'{BASE_URL}/item.html',
                           category_rule=category_rule_item,
                           title=f"Детали правила категории ID {category_rule_item.id}")

@category_rules_bp.route('/create', methods=['GET', 'POST'])
async def create():
    shelf_rule_id_from_query = request.args.get('shelf_rule_id', type=int)
    form = CreateCategoryRule()

    if shelf_rule_id_from_query:
        shelf_rule_exists = ShelfRuleDAO.get_by_id(shelf_rule_id_from_query)
        if shelf_rule_exists:
            form.shelf_rule_id.data = shelf_rule_id_from_query
            form.shelf_rule_id.render_kw = {'readonly': True}
        else:
            print(f'Правило полки с ID {shelf_rule_id_from_query} не найдено.', 'warning')
            shelf_rule_id_from_query = None 

    if form.validate_on_submit():
        if form.min_weight.data is not None and \
           form.max_weight.data is not None and \
           form.min_weight.data > form.max_weight.data:
            form.max_weight.errors.append("Максимальный вес не может быть меньше минимального.")
            form.populate_choices()
            return render_template(f'{BASE_URL}/create.html', title='Создать правило категории', form=form)

        shelf_rule_id_to_save = form.shelf_rule_id.data

        category_rule_data = CategoryRule(
            share=form.share.data,
            min_weight=form.min_weight.data,
            max_weight=form.max_weight.data,
            shelf_rule_id=shelf_rule_id_to_save,
            category_id=form.category_id.data
        )
        try:
            new_category_rule = CategoryRuleDAO.add(category_rule_data)
            print('Новое правило категории успешно создано!', 'success')
            if shelf_rule_id_from_query or shelf_rule_id_to_save:
                 parent_shelf_rule_id = shelf_rule_id_from_query or shelf_rule_id_to_save
                 return redirect(url_for('shelf_rules.read', id=parent_shelf_rule_id))
            return redirect(url_for(f'.read', id=new_category_rule.id))
        except Exception as e:
            print(f'Ошибка при создании правила категории: {e}', 'danger')
            form.populate_choices()

    if not form.is_submitted():
        form.populate_choices(shelf_rule_id_to_select=shelf_rule_id_from_query)

    title = "Создать новое правило категории"
    if shelf_rule_id_from_query and form.shelf_rule_id.render_kw.get('readonly'):
        title = f"Добавить правило категории к правилу полки ID {shelf_rule_id_from_query}"

    return render_template(f'{BASE_URL}/create.html', title=title, form=form)


@category_rules_bp.route('/update/<int:id>', methods=['GET', 'POST'])
async def update(id: int):
    category_rule_to_update = CategoryRuleDAO.get_by_id(id)
    if not category_rule_to_update:
        print('Правило категории не найдено.', 'warning')
        return redirect(url_for(f'.read_all'))

    form = UpdateCategoryRule(obj=category_rule_to_update)

    if form.validate_on_submit():
        if form.min_weight.data is not None and \
           form.max_weight.data is not None and \
           form.min_weight.data > form.max_weight.data:
            form.max_weight.errors.append("Максимальный вес не может быть меньше минимального.")
            form.populate_choices(
                shelf_rule_id_to_select=category_rule_to_update.shelf_rule_id,
                category_id_to_select=form.category_id.data
            )
            return render_template(f'{BASE_URL}/update.html', title=f'Изменить правило категории ID {id}', form=form)

        category_rule_data_for_update = CategoryRule(
            share=form.share.data,
            min_weight=form.min_weight.data, 
            max_weight=form.max_weight.data,
            shelf_rule_id=category_rule_to_update.shelf_rule_id, 
            category_id=form.category_id.data
        )
        try:
            CategoryRuleDAO.update_by_id(id, category_rule_data_for_update)
            print('Правило категории успешно обновлено!', 'success')
            return redirect(url_for(f'.read', id=id))
        except Exception as e:
            print(f'Ошибка при обновлении правила категории: {e}', 'danger')
            form.populate_choices(
                shelf_rule_id_to_select=category_rule_to_update.shelf_rule_id,
                category_id_to_select=form.category_id.data
            )
    elif request.method == 'GET':
        form.populate_choices(
            shelf_rule_id_to_select=category_rule_to_update.shelf_rule_id,
            category_id_to_select=category_rule_to_update.category_id
        )
        form.min_weight.data = category_rule_to_update.min_weight
        form.max_weight.data = category_rule_to_update.max_weight


    return render_template(f'{BASE_URL}/update.html', title=f'Изменить правило категории ID {id}', form=form)

@category_rules_bp.route('/delete/<int:id>', methods=['GET', 'POST'])
async def delete(id: int):
    category_rule_to_delete = CategoryRuleDAO.get_by_id(id)
    if not category_rule_to_delete:
        print('Правило категории не найдено.', 'warning')
        return redirect(url_for(f'.read_all'))

    shelf_rule_id_redirect = category_rule_to_delete.shelf_rule_id

    try:
        CategoryRuleDAO.delete_by_id(id)
        print(f'Правило категории ID {id} успешно удалено.', 'success')
    except Exception as e:
        print(f'Ошибка при удалении правила категории: {e}', 'danger')

    if shelf_rule_id_redirect:
        if ShelfRuleDAO.get_by_id(shelf_rule_id_redirect):
            return redirect(url_for('shelf_rules.read', id=shelf_rule_id_redirect))
    return redirect(url_for(f'.read_all'))