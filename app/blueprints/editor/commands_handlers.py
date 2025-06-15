from app.blueprints.editor.exceptions import CommandError, ParsingError
from .models import server_message, planogram_data, rules_data
from .parser import CommandParser
from DataLayer.dao import ShelfUnitDAO, CategoryDAO, ProductDAO, BrandDAO
from DataLayer.shemas import ShelfUnit as SU, Category as Cat, Product as P, Brand as B
from .models import category_rule, shelf_rule, rules_data
from .check_rules import can_place_product, get_all_categories_for_shelf, check_total_percentage, get_free_percentage
from .sort_dictionaries import *


REVERSE_PRODUCT_SORT_MAP = {v: k for k, v in p_sort_keys.items()}
REVERSE_BRAND_SORT_MAP = {v: k for k, v in b_sort_keys.items()}

COMANDS_EXAMPLE = """
[
  {
    "command": "ОПРЕДЕЛИ ПРАВИЛА ДЛЯ ПОЛКИ",
    "description": "Задаёт полный набор правил для категорий на одной полке, полностью заменяя все предыдущие правила для этой полки. Сумма процентов всех категорий на полке не должна превышать 100%.",
    "syntax": "ПОЛКА <номер_полки>: <имя_категории_1> (<параметры_1>), <имя_категории_2> (<параметры_2>), ...",
    "examples": [
      "ПОЛКА 1: охлаждающие жидкости (25% / от 1 кг / до 5 кг), стеклоомыватели (от 1 кг/ до 5 кг/ 25%), вода дистиллированная(25%)",
      "ПОЛКА 2: электролит(50% / от 1 кг), густые смазки(50% / до 5 кг)"
    ],
    "parameters": [
      {
        "name": "номер_полки", 
        "type": "integer", 
        "required": true, 
        "description": "Номер полки для установки правил."
      },
      {
        "name": "правила_категорий", 
        "type": "list", 
        "required": true, 
        "description": "Список правил для категорий. Каждое правило содержит имя категории и параметры в скобках, разделенные '/'. Процент является обязательным параметром."
      }
    ]
  },
  {
    "command": "УСТАНОВИ СТЕЛЛАЖ",
    "description": "Выбирает конкретный стеллаж для всех последующих операций. Все команды по размещению и настройке полок будут применяться к этому стеллажу, если не указано иное.",
    "syntax": "УСТАНОВИ СТЕЛЛАЖ <номер_стеллажа>",
    "examples": [
      "УСТАНОВИ СТЕЛЛАЖ 1",
      "УСТАНОВИ СТЕЛЛАЖ 5"
    ],
    "parameters": [
      {"name": "номер_стеллажа", "type": "integer", "required": true, "description": "Уникальный номер стеллажа."}
    ]
  },
  {
    "command": "РАЗМЕСТИ КАТЕГОРИЮ",
    "description": "Назначает категорию товаров на указанную полку. Можно задать желаемую долю пространства, которую должна занять категория на полке, а также указать ограничения по весу для товаров из этой категории. Ограничения по весу могут включать минимальный вес, максимальный вес или оба значения.",
    "syntax": "РАЗМЕСТИ КАТЕГОРИЮ '<название_категории>' НА ПОЛКЕ <номер_полки> [ЗАНЯВ <доля_процентов>% МЕСТА] [ВЕС [ОТ <минимальный_вес> КГ] [ДО <максимальный_вес> КГ]]",
    "examples": [
      "РАЗМЕСТИ КАТЕГОРИЮ 'Молочные продукты' НА ПОЛКЕ 1 ЗАНЯВ 70% МЕСТА",
      "РАЗМЕСТИ КАТЕГОРИЮ 'Напитки' НА ПОЛКЕ 2",
      "РАЗМЕСТИ КАТЕГОРИЮ 'Фрукты' НА ПОЛКЕ 3 ВЕС ОТ 0.5 КГ ДО 2 КГ",
      "РАЗМЕСТИ КАТЕГОРИЮ 'Крупы' НА ПОЛКЕ 1 ВЕС ОТ 0.8 КГ",
      "РАЗМЕСТИ КАТЕГОРИЮ 'Консервы' НА ПОЛКЕ 5 ВЕС ДО 1.5 КГ",
      "РАЗМЕСТИ КАТЕГОРИЮ 'Овощи' НА ПОЛКЕ 4 ЗАНЯВ 50% МЕСТА ВЕС ОТ 0.1 КГ ДО 1 КГ"
    ],
    "parameters": [
      {
        "name": "название_категории",
        "type": "string",
        "required": true,
        "description": "Название категории, товары которой будут размещаться. Должно быть заключено в одинарные кавычки (например, 'Молочные продукты')."
      },
      {
        "name": "номер_полки",
        "type": "integer",
        "required": true,
        "description": "Номер полки, на которую назначается категория."
      },
      {
        "name": "доля_процентов",
        "type": "float",
        "required": false,
        "min": 0,
        "max": 100,
        "description": "Желаемая доля пространства на полке в процентах (без знака '%'), которую должна занять категория."
      },
      {
        "name": "минимальный_вес",
        "type": "float",
        "required": false,
        "min": 0,
        "description": "Минимальный вес продукта (в килограммах), который может быть размещен. Указывается после ключевого слова 'ОТ'."
      },
      {
        "name": "максимальный_вес",
        "type": "float",
        "required": false,
        "min": 0,
        "description": "Максимальный вес продукта (в килограммах), который может быть размещен. Указывается после ключевого слова 'ДО'."
      }
    ]
  },
  {
    "command": "ЗАПОЛНИ ОСТАТОК ПОЛКИ",
    "description": "Заполняет оставшееся свободное пространство на полке товарами указанной категории после выполнения всех других команд.",
    "syntax": "ЗАПОЛНИ ОСТАТОК ПОЛКИ <номер_полки> КАТЕГОРИЕЙ '<название_категории>'",
    "examples": [
      "ЗАПОЛНИ ОСТАТОК ПОЛКИ 2 КАТЕГОРИЕЙ 'Снеки'"
    ],
    "parameters": [
      {"name": "номер_полки", "type": "integer", "required": true, "description": "Номер полки для заполнения."},
      {"name": "название_категории", "type": "string", "required": true, "description": "Название категории, товары которой будут использованы для заполнения. Должно быть в кавычках."}
    ]
  },
  {
    "command": "СОРТИРОВКА БРЕНДОВ",
    "description": "Устанавливает глобальное правило для сортировки брендов внутри категорий.",
    "syntax": "СОРТИРОВКА БРЕНДОВ '<тип_сортировки>'",
    "examples": [
      "СОРТИРОВКА БРЕНДОВ 'Название бренда (А-Я)'",
      "СОРТИРОВКА БРЕНДОВ 'Рейтинг бренда (по убыванию)'"
    ],
    "parameters": [
      {
        "name": "тип_сортировки", 
        "type": "string", 
        "required": true, 
        "description": "Тип сортировки для брендов. Должен быть в кавычках и соответствовать одному из доступных вариантов."
      }
    ]
  },
  {
    "command": "СОРТИРОВКА ТОВАРОВ",
    "description": "Устанавливает глобальное правило для сортировки товаров внутри брендов.",
    "syntax": "СОРТИРОВКА ТОВАРОВ '<тип_сортировки>'",
    "examples": [
      "СОРТИРОВКА ТОВАРОВ 'Цена по возрастанию'",
      "СОРТИРОВКА ТОВАРОВ 'Название (А-Я)'"
    ],
    "parameters": [
      {
        "name": "тип_сортировки", 
        "type": "string", 
        "required": true, 
        "description": "Тип сортировки для товаров. Должен быть в кавычках и соответствовать одному из доступных вариантов."
      }
    ]
  },
  {
    "command": "ГОРИЗОНТАЛЬНЫЙ ПРОМЕЖУТОК МЕЖДУ ТОВАРАМИ",
    "description": "Устанавливает глобальное правило для стандартного отступа между продуктами на полке.",
    "syntax": "ГОРИЗОНТАЛЬНЫЙ ПРОМЕЖУТОК МЕЖДУ ТОВАРАМИ <размер_см>",
    "examples": [
      "ГОРИЗОНТАЛЬНЫЙ ПРОМЕЖУТОК МЕЖДУ ТОВАРАМИ 0.5",
      "ГОРИЗОНТАЛЬНЫЙ ПРОМЕЖУТОК МЕЖДУ ТОВАРАМИ 2"
    ],
    "parameters": [
      {
        "name": "размер_см", 
        "type": "float", 
        "required": true,
        "min": 0,
        "description": "Размер отступа между товарами в сантиметрах. Может быть целым или дробным числом."
      }
    ]
  }
]
"""
parser = CommandParser(COMANDS_EXAMPLE)


def fill_free_space_on_shelf(parameters, reply, planogram):
    category_name = parameters['название_категории']
    shelf_number = parameters['номер_полки']

    shelf_unit_id = planogram['shelf_unit_id']
     
    category = CategoryDAO.get_one(Cat(name=category_name))
    if category and shelf_unit_id:
        shelf_unit = ShelfUnitDAO.get_by_id(shelf_unit_id)
        shelf = shelf_unit.get_shelf_by_number(shelf_number)
        if shelf:
            free_share = get_free_percentage(category_name, reply, shelf_number, shelf.id)   
            
            c_rule = category_rule(category_name, category.id, free_share)

            reply.rules.delete_category_rule(shelf_number, shelf.id, c_rule)
            reply.rules.add_category_rule(shelf_number, shelf.id, c_rule)

            reply.message = f'Категория {category_name} добавлена к правилам полки и будет занимать {free_share}% от общего пространтва полки'
        else:
            reply.message = f"Не найдена полка {shelf_number}"
    else:
        reply.message = f"Не найдена категория {category_name} или рабочий стеллаж."

#INFO Меняет стеллаж и обнуляет правила
def place_shelf_unit_handler(parameters):
    """Устанавливает стеллаж. В случае успеха возвращает новый planogram_data."""
    shelf_unit_number = parameters['номер_стеллажа']
    shelf_unit = ShelfUnitDAO.get_one(SU(shelf_unit_number=shelf_unit_number))

    if not shelf_unit:
        raise CommandError(f"Стеллаж с номером {shelf_unit_number} не найден.")
    
    new_planogram = planogram_data(shelf_unit=shelf_unit)
    success_message = f"Стеллаж {shelf_unit_number} установлен. Все предыдущие правила и расстановка сброшены."
    return success_message, new_planogram, rules_data()

#INFO Перебивает текущие рправила для категории и заменяет их
def place_category_handler(parameters, current_rules: rules_data, planogram: dict):
    """Добавляет правило для категории. Возвращает измененные правила."""
    category_name = parameters['название_категории']
    shelf_number = parameters['номер_полки']
    share = parameters.get('доля_процентов')
    min_weight = parameters.get('минимальный_вес')
    max_weight = parameters.get('максимальный_вес')
    shelf_unit_id = planogram.get('shelf_unit_id')

    if not shelf_unit_id:
        raise CommandError("Сначала нужно установить стеллаж командой 'УСТАНОВИ СТЕЛЛАЖ' или при помощи графического интерфейса.")

    category = CategoryDAO.get_one(Cat(name=category_name))
    if not category:
        raise CommandError(f"Категория '{category_name}' не найдена.")

    shelf_unit = ShelfUnitDAO.get_by_id(shelf_unit_id)
    shelf = shelf_unit.get_shelf_by_number(shelf_number)
    if not shelf:
        raise CommandError(f"Полка с номером {shelf_number} не найдена на текущем стеллаже.")

    if share is not None and not check_total_percentage(category_name, share, current_rules, shelf_number, shelf.id):
        free_percentage = get_free_percentage(category_name, current_rules, shelf_number, shelf.id)
        raise CommandError(f"Невозможно выделить {share}% для категории '{category_name}'. "
                         f"Сумма процентов превысит 100%. Доступно: {free_percentage}%.")

    c_rule = category_rule(
        category_name, 
        category.id, 
        share, 
        min_weight if min_weight is not None else None, 
        max_weight if max_weight is not None else None
    )

    current_rules.delete_category_rule(shelf_number, shelf.id, c_rule)
    current_rules.add_category_rule(shelf_number, shelf.id, c_rule)
    
    success_message = f"Правило для категории '{category_name}' на полке №{shelf_number} успешно добавлено/обновлено."
    return success_message, current_rules

#INFO Заменяет все правила (категории) для полки на указанные
def define_shelf_rules_handler(parameters, current_rules: rules_data, planogram: dict):
    """Полностью определяет правила для одной полки."""
    shelf_number = parameters['номер_полки']
    category_rules_payload = parameters['правила_категорий']
    shelf_unit_id = planogram.get('shelf_unit_id')
    
    if not shelf_unit_id:
        raise CommandError("Ошибка: Сначала необходимо установить стеллаж.")
        
    shelf_unit = ShelfUnitDAO.get_by_id(shelf_unit_id)
    if not shelf_unit:
        raise CommandError(f"Ошибка: Стеллаж не найден в базе данных.")

    shelf = shelf_unit.get_shelf_by_number(shelf_number)
    if not shelf:
        raise CommandError(f"Ошибка: Полка с номером {shelf_number} не найдена на стеллаже {shelf_unit.shelf_unit_number}.")

    new_category_rules = []
    errors = []
    total_percentage = sum(rule.get('percentage', 0) or 0 for rule in category_rules_payload)

    if total_percentage > 100:
        errors.append(f"Сумма процентов ({total_percentage}%) не может превышать 100%.")

    for rule_payload in category_rules_payload:
        category = CategoryDAO.get_one(Cat(name=rule_payload['categoryName']))
        if not category:
            errors.append(f"Категория '{rule_payload['categoryName']}' не найдена.")
            continue
        
        if rule_payload.get('percentage') is None:
            errors.append(f"Для категории '{rule_payload['categoryName']}' не указан процент.")
            continue

        new_rule = category_rule(
            category_name=category.name, category_id=category.id,
            percentage=rule_payload['percentage'],
            min_weight=rule_payload.get('minWeight'),
            max_weight=rule_payload.get('maxWeight')
        )
        new_category_rules.append(new_rule)
        
    if errors:
        raise CommandError("Не удалось применить правила. Ошибки:\n" + ";\n ".join(errors))

    current_rules.set_rules_for_shelf(shelf.shelf_number, shelf.id, new_category_rules)
    
    success_message = f"Правила для полки №{shelf_number} успешно обновлены. Всего правил: {len(new_category_rules)}."
    return success_message, current_rules

#INFO Добавляет новое правило / Изменяет процентаж уже существующего правила
def fill_free_space_handler(parameters, current_rules: rules_data, planogram: dict):
    """
    Находит существующее правило для категории и добавляет к его проценту все оставшееся место.
    Если правила нет, создает новое.
    """
    category_name = parameters['название_категории']
    shelf_number = parameters['номер_полки']
    shelf_unit_id = planogram.get('shelf_unit_id') if isinstance(planogram, dict) else getattr(planogram, 'id', None)

    if not shelf_unit_id:
        raise CommandError("Сначала нужно установить стеллаж.")

    category = CategoryDAO.get_one(Cat(name=category_name))
    if not category:
        raise CommandError(f"Категория '{category_name}' не найдена.")

    shelf_unit = ShelfUnitDAO.get_by_id(shelf_unit_id)
    shelf = shelf_unit.get_shelf_by_number(shelf_number)
    if not shelf:
        raise CommandError(f"Полка с номером {shelf_number} не найдена на текущем стеллаже.")

    free_share = get_free_percentage(category_name, current_rules, shelf_number, shelf.id)

    if free_share <= 0:
        raise CommandError(f"На полке №{shelf_number} нет свободного места для заполнения.")
        
    existing_rule = current_rules.get_category_rule_on_shelf(shelf_number, category.id)

    if existing_rule:
        current_percentage = existing_rule.percentage if existing_rule.percentage is not None else 0
        new_percentage = current_percentage + free_share
        
        existing_rule.percentage = min(new_percentage, 100.0)

        success_message = (f"Для категории '{category_name}' на полке №{shelf_number} выделено дополнительное место. "
                         f"Итоговый процент: {existing_rule.percentage:.2f}%.")
    else:
        c_rule = category_rule(category.name, category.id, free_share)
        current_rules.add_category_rule(shelf_number, shelf.id, c_rule)
        
        success_message = f"Категории '{category_name}' выделено оставшееся место на полке №{shelf_number} ({free_share:.2f}%)."
        
    
    return success_message, current_rules

#INFO Заменяет правило сортировки брендов на новое
def set_brand_sorting_handler(parameters, current_rules: rules_data):
    """Устанавливает глобальное правило сортировки для брендов."""
    sort_type_str = parameters['тип_сортировки']
    
    if sort_type_str not in REVERSE_BRAND_SORT_MAP:
        available_options = ",\n- ".join(f"'{opt}'" for opt in REVERSE_BRAND_SORT_MAP.keys())
        raise CommandError(
            f"Неверный тип сортировки: '{sort_type_str}'.\n"
            f"Доступные варианты для брендов:\n- {available_options}"
        )
        
    sort_enum_value = REVERSE_BRAND_SORT_MAP[sort_type_str]
    current_rules.brand_sort = sort_enum_value.value
    
    success_message = f"Правило сортировки брендов установлено на: '{sort_type_str}'."
    return success_message, current_rules

#INFO Заменяет правило сортировки товаров на новое
def set_product_sorting_handler(parameters, current_rules: rules_data):
    """Устанавливает глобальное правило сортировки для товаров."""
    sort_type_str = parameters['тип_сортировки']
    
    if sort_type_str not in REVERSE_PRODUCT_SORT_MAP:
        available_options = ",\n- ".join(f"'{opt}'" for opt in REVERSE_PRODUCT_SORT_MAP.keys())
        raise CommandError(
            f"Неверный тип сортировки: '{sort_type_str}'.\n"
            f"Доступные варианты для товаров:\n- {available_options}"
        )
        
    sort_enum_value = REVERSE_PRODUCT_SORT_MAP[sort_type_str]
    current_rules.product_sort = sort_enum_value.value
    
    success_message = f"Правило сортировки товаров установлено на: '{sort_type_str}'."
    return success_message, current_rules

#INFO Заменяет промежуток на указанный
def set_spacing_handler(parameters, current_rules: rules_data):
    """Устанавливает глобальное правило для отступа между товарами."""
    spacing_size = parameters['размер_см']
    
    if spacing_size < 0:
        raise CommandError("Размер промежутка не может быть отрицательным.")
        
    current_rules.spacing = spacing_size
    
    success_message = f"Горизонтальный промежуток между товарами установлен на: {spacing_size} см."
    return success_message, current_rules

def commands_handler(user_message: str, planogram_dict: dict, rules_dict: dict) -> server_message:
    """
    Главный обработчик команд.
    """
    try:
        command_name, parameters = parser.parse(user_message)
    except ParsingError as e:
        raise CommandError(str(e))

    current_rules = rules_data.from_dict(rules_dict)
    
    planogram_to_return = planogram_dict
    rules_to_return = current_rules
    message_to_return = ""

    if command_name.upper() == "УСТАНОВИ СТЕЛЛАЖ":
        message_to_return, planogram_to_return, rules_to_return = place_shelf_unit_handler(parameters)
    elif command_name.upper() == "РАЗМЕСТИ КАТЕГОРИЮ":
        message_to_return, rules_to_return = place_category_handler(parameters, current_rules, planogram_dict)
    elif command_name.upper() == "ОПРЕДЕЛИ ПРАВИЛА ДЛЯ ПОЛКИ":
        message_to_return, rules_to_return = define_shelf_rules_handler(parameters, current_rules, planogram_dict)
    elif command_name.upper() == "ЗАПОЛНИ ОСТАТОК ПОЛКИ":
        message_to_return, rules_to_return = fill_free_space_handler(parameters, current_rules, planogram_dict)
    elif command_name.upper() == "СОРТИРОВКА БРЕНДОВ":
        message_to_return, rules_to_return = set_brand_sorting_handler(parameters, current_rules)
    elif command_name.upper() == "СОРТИРОВКА ТОВАРОВ":
        message_to_return, rules_to_return = set_product_sorting_handler(parameters, current_rules)
    elif command_name.upper() == "ГОРИЗОНТАЛЬНЫЙ ПРОМЕЖУТОК МЕЖДУ ТОВАРАМИ":
        message_to_return, rules_to_return = set_spacing_handler(parameters, current_rules)
    else:
        raise CommandError(f"Команда '{command_name}' распознана, но ее обработка пока не реализована.")

    return server_message(
        message=message_to_return,
        data=planogram_to_return,
        rules=rules_to_return
    )