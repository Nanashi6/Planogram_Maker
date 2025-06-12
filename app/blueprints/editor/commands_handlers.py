from .models import server_message, planogram_data, rules_data
from .parser import CommandParser
from DataLayer.dao import ShelfUnitDAO, CategoryDAO, ProductDAO, BrandDAO
from DataLayer.shemas import ShelfUnit as SU, Category as Cat, Product as P, Brand as B
from .models import category_rule, shelf_rule, rules_data
from .check_rules import can_place_product, get_all_categories_for_shelf, check_total_percentage, get_free_percentage

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
    "command": "РАЗМЕСТИ ТОВАР",
    "description": "Размещает конкретный товар на указанной полке. Можно задать количество фейсингов.",
    "syntax": "РАЗМЕСТИ ТОВАР <штрихкод_товара> НА ПОЛКЕ <номер_полки> [В КОЛИЧЕСТВЕ <количество_фейсингов> ФЕЙСИНГОВ]",
    "examples": [
      "РАЗМЕСТИ ТОВАР 4607123456789 НА ПОЛКЕ 2 В КОЛИЧЕСТВЕ 3 ФЕЙСИНГОВ",
      "РАЗМЕСТИ ТОВАР 1234567890123 НА ПОЛКЕ 1"
    ],
    "parameters": [
      {"name": "штрихкод_товара", "type": "integer", "required": true, "description": "Уникальный штрихкод товара (barcode)."},
      {"name": "номер_полки", "type": "integer", "required": true, "description": "Номер полки, на которую нужно разместить продукт."},
      {"name": "количество_фейсингов", "type": "integer", "required": false, "description": "Количество единиц продукта, стоящих лицом к покупателю."}
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
    "command": "ОГРАНИЧЬ ПОЛКУ",
    "description": "Указывает, что на данной полке могут находиться только товары указанной категории или бренда. Если указан бренд, то должна быть указана и категория.",
    "syntax": "ОГРАНИЧЬ ПОЛКУ <номер_полки> ТОЛЬКО ДЛЯ КАТЕГОРИИ '<название_категории>' | ТОЛЬКО ДЛЯ БРЕНДА '<название_бренда>' ИЗ КАТЕГОРИИ '<название_категории>'",
    "examples": [
      "ОГРАНИЧЬ ПОЛКУ 3 ТОЛЬКО ДЛЯ КАТЕГОРИИ 'Хлебобулочные изделия'",
      "ОГРАНИЧЬ ПОЛКУ 4 ТОЛЬКО ДЛЯ БРЕНДА 'Mars' ИЗ КАТЕГОРИИ 'Шоколадные батончики'"
    ],
    "parameters": [
      {"name": "номер_полки", "type": "integer", "required": true, "description": "Номер полки для ограничения."},
      {"name": "название_категории", "type": "string", "required": true, "description": "Название категории, если ограничение по категории или бренду. Должно быть в кавычках."},
      {"name": "название_бренда", "type": "string", "required": false, "description": "Название бренда, если ограничение по бренду. Должно быть в кавычках."}
    ]
  },
  {
    "command": "РАЗМЕСТИ АВТОМАТИЧЕСКИ",
    "description": "Автоматически размещает доступные товары указанной категории на полке, сортируя их по заданному атрибуту.",
    "syntax": "РАЗМЕСТИ АВТОМАТИЧЕСКИ КАТЕГОРИЮ '<название_категории>' НА ПОЛКЕ <номер_полки> [СОРТИРУЯ ПО <атрибут_сортировки>] [ПО ВОЗРАСТАНИЮ|ПО УБЫВАНИЮ]",
    "examples": [
      "РАЗМЕСТИ АВТОМАТИЧЕСКИ КАТЕГОРИЮ 'Соки' НА ПОЛКЕ 5 СОРТИРУЯ ПО ЦЕНЕ ПО УБЫВАНИЮ",
      "РАЗМЕСТИ АВТОМАТИЧЕСКИ КАТЕГОРИЮ 'Печенье' НА ПОЛКЕ 4 СОРТИРУЯ ПО РЕЙТИНГУ_SKU ПО ВОЗРАСТАНИЮ"
    ],
    "parameters": [
      {"name": "название_категории", "type": "string", "required": true, "description": "Название категории, товары которой будут размещены. Должно быть в кавычках."},
      {"name": "номер_полки", "type": "integer", "required": true, "description": "Номер полки для автоматического размещения."},
      {"name": "атрибут_сортировки", "type": "string", "required": false, "enum": ["ЦЕНЕ", "РЕЙТИНГУ_SKU", "ДЛИНЕ"], "description": "Атрибут товара для сортировки (price, SKU_rating, length)."},
      {"name": "порядок_сортировки", "type": "string", "required": false, "enum": ["ПО ВОЗРАСТАНИЮ", "ПО УБЫВАНИЮ"], "description": "Порядок сортировки."}
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
    "command": "РАЗМЕСТИ БРЕНД",
    "description": "Назначает конкретный бренд из определённой категории на указанную полку. Можно задать желаемую долю пространства внутри этой категории.",
    "syntax": "РАЗМЕСТИ БРЕНД '<название_бренда>' ИЗ КАТЕГОРИИ '<название_категории>' НА ПОЛКЕ <номер_полки> [ЗАНЯВ <доля_процентов>% МЕСТА]",
    "examples": [
      "РАЗМЕСТИ БРЕНД 'Простоквашино' ИЗ КАТЕГОРИИ 'Молочные продукты' НА ПОЛКЕ 1 ЗАНЯВ 40% МЕСТА"
    ],
    "parameters": [
      {"name": "название_бренда", "type": "string", "required": true, "description": "Название бренда, должно быть в кавычках."},
      {"name": "название_категории", "type": "string", "required": true, "description": "Название категории, к которой относится бренд, должно быть в кавычках."},
      {"name": "номер_полки", "type": "integer", "required": true, "description": "Номер полки для размещения бренда."},
      {"name": "доля_процентов", "type": "integer", "required": false, "min": 0, "max": 100, "description": "Желаемая доля пространства, которую должен занять бренд (от общего пространства, выделенного для категории на этой полке)."}
    ]
  },


  


  {
    "command": "УДАЛИ ПРОДУКТ",
    "description": "Удаляет конкретный продукт с указанной полки.",
    "syntax": "УДАЛИ ПРОДУКТ <штрихкод_продукта> С ПОЛКИ <номер_полки>",
    "examples": [
      "УДАЛИ ПРОДУКТ 4607123456789 С ПОЛКИ 2"
    ],
    "parameters": [
      {"name": "штрихкод_продукта", "type": "integer", "required": true, "description": "Уникальный штрихкод продукта."},
      {"name": "номер_полки", "type": "integer", "required": true, "description": "Номер полки, с которой нужно удалить продукт."}
    ]
  },
  {
    "command": "ПЕРЕМЕСТИ ПРОДУКТ",
    "description": "Перемещает продукт с одной полки на другую.",
    "syntax": "ПЕРЕМЕСТИ ПРОДУКТ <штрихкод_продукта> С ПОЛКИ <источник_полка> НА ПОЛКУ <цель_полка>",
    "examples": [
      "ПЕРЕМЕСТИ ПРОДУКТ 1234567890123 С ПОЛКИ 1 НА ПОЛКУ 3"
    ],
    "parameters": [
      {"name": "штрихкод_продукта", "type": "integer", "required": true, "description": "Уникальный штрихкод продукта."},
      {"name": "источник_полка", "type": "integer", "required": true, "description": "Номер полки, с которой перемещается продукт."},
      {"name": "цель_полка", "type": "integer", "required": true, "description": "Номер полки, на которую перемещается продукт."}
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

def shelf_constrain(parameters, reply, planogram_data):
    category_name = parameters.get('название_категории', parameters.get('название_категории_бренда', None))
    shelf_number = parameters['номер_полки']
    brand_name = parameters.get('название_бренда', None)

    shelf_unit_id = planogram_data['shelf_unit_id']
    
    brand = None
    if brand_name:
        brand = BrandDAO.get_one(B(name=brand_name))
        if not brand:
            reply.message = f"Не найден бренд {brand_name}."
            return

    category = CategoryDAO.get_one(Cat(name=category_name))
    if category and shelf_unit_id:
        shelf_unit = ShelfUnitDAO.get_by_id(shelf_unit_id)
        shelf = shelf_unit.get_shelf_by_number(shelf_number)
        if shelf:
            reply.message = f'{category.name}, {brand.name if brand else None}, {shelf_number}'
        else:
            reply.message = f"Не найдена полка {shelf_number}"
    else:
        reply.message = f"Не найдена категория {category_name} или рабочий стеллаж."

def place_product(parameters, reply, planogram):
    barcode = parameters['штрихкод_товара']
    shelf_number = parameters['номер_полки']
    facings_count = parameters['количество_фейсингов'] if parameters['количество_фейсингов'] else 1

    shelf_unit_id = planogram['shelf_unit_id']
    
    if shelf_unit_id:
        shelf_unit = ShelfUnitDAO.get_by_id(shelf_unit_id)
        shelf = shelf_unit.get_shelf_by_number(shelf_number)
        if shelf:
            product = ProductDAO.get_one(P(barcode=barcode))
            if product and product.category.name in get_all_categories_for_shelf(reply, shelf_number, shelf.id) and product.height <= shelf.height:
                total_placed = 0

                max_position_on_shelf = 0
                products_on_shelf_depths = []
                pps = []

                for pp in planogram['placed_products']:
                    pproduct = ProductDAO.get_by_id(pp['product_id'])
                    pps.append({
                        'shelf_id': pp['shelf_id'],
                        'product_id': pproduct.id,
                        'position': pp['position'],
                        'product': pproduct.to_dict()
                    })
                    if pp['shelf_id'] == shelf.id:
                        products_on_shelf_depths.append(pproduct.depth + 0.5)
                        if pp['position'] > max_position_on_shelf:
                            max_position_on_shelf = pp['position']

                # free_length = shelf.length - sum(products_on_shelf_depths)                    # 0.5
                while can_place_product(product, reply, shelf_number, shelf.id, shelf.length, pps) and facings_count > 0:                 # BUG ВЕС
                    max_position_on_shelf += 1
                    # free_length -= product.depth + 0.5                                        # 0.5
                    facings_count -= 1
                    total_placed += 1
                    pps.append({
                        'shelf_id': shelf.id,
                        'product_id': product.id,
                        'position': max_position_on_shelf,
                        'product': product.to_dict()
                    })
                reply.data = planogram_data(planogram['id'], 'Пример', shelf_unit, pps)
                reply.message = f'Установлено {total_placed} фейсингов исходя из свободного места для категории "{product.category_brand_placement.category.name}" на полке'
                # BUG Размер расстояния между товарами неизвестен, надо как-то его инициализировать (пока берётся 0.5)
            else:
                reply.message = f'Не найден указанный товар {barcode}, товар не подходит по высоте или категория товара не может размещаться на полке'
                reply.data = None
        else:
            reply.message = f"Не найдена полка {shelf_number}"
    else:
        reply.message = f"Не найден рабочий стеллаж."

def place_category(parameters, reply, planogram):
    category_name = parameters['название_категории']
    shelf_number = parameters['номер_полки']
    share = parameters.get('доля_процентов', 100)
    min_weight = parameters.get('минимальный_вес', 0)
    max_weight = parameters.get('максимальный_вес', float('inf'))

    shelf_unit_id = planogram['shelf_unit_id']
     
    category = CategoryDAO.get_one(Cat(name=category_name))
    if category and shelf_unit_id:
        shelf_unit = ShelfUnitDAO.get_by_id(shelf_unit_id)
        shelf = shelf_unit.get_shelf_by_number(shelf_number)
        if shelf and check_total_percentage(category_name, share, reply, shelf_number, shelf.id):
            reply.message = f'Категория {category_name} добавлена к правилам полки'

            c_rule = category_rule(category_name, category.id, share, min_weight if min_weight else None, max_weight if max_weight else None)

            reply.rules.delete_category_rule(shelf_number, shelf.id, c_rule)
            reply.rules.add_category_rule(shelf_number, shelf.id, c_rule)
        else:
            if not shelf:
              reply.message = f"Не найдена полка {shelf_number} или нет доступного  свободного пространства."
            else:
              reply.message = f"Без учёта указанной категории доступно {get_free_percentage(category_name, reply, shelf_number, shelf.id)}%"
              reply.data = None
    else:
        reply.message = f"Не найдена категория {category_name} или рабочий стеллаж."
        
def place_shelf_unit(parameters, reply):
    shelf_unit_number = parameters['номер_стеллажа']
    shelf_unit = ShelfUnitDAO.get_one(SU(shelf_unit_number=shelf_unit_number))

    if shelf_unit:
        reply.message = f"Стеллаж {shelf_unit_number} установлен."
        reply.data = planogram_data(shelf_unit=shelf_unit)
        reply.rules = rules_data()
    else:
        reply.message = f"Стеллаж с номером {shelf_unit_number} не найден."

def define_shelf_rules(parameters, reply, planogram):
    """
    Обрабатывает команду 'ОПРЕДЕЛИ ПРАВИЛА ДЛЯ ПОЛКИ'.
    """
    shelf_number = parameters['номер_полки']
    category_rules_payload = parameters['правила_категорий']
    print(len(category_rules_payload))

    shelf_unit_id = planogram.get('shelf_unit_id')
    if not shelf_unit_id:
        reply.message = "Ошибка: Сначала необходимо установить стеллаж с помощью команды 'УСТАНОВИ СТЕЛЛАЖ'."
        return
        
    shelf_unit = ShelfUnitDAO.get_by_id(shelf_unit_id)
    if not shelf_unit:
        reply.message = f"Ошибка: Стеллаж с ID {shelf_unit_id} не найден в базе данных."
        return

    shelf = shelf_unit.get_shelf_by_number(shelf_number)
    if not shelf:
        reply.message = f"Ошибка: Полка с номером {shelf_number} не найдена в стеллаже {shelf_unit.shelf_unit_number}."
        return

    new_category_rules = []
    errors = []
    total_percentage = sum(rule['percentage'] for rule in category_rules_payload)

    if total_percentage > 100:
        errors.append(f"Сумма процентов ({total_percentage}%) превышает 100%.")

    for rule_payload in category_rules_payload:
        category = CategoryDAO.get_one(Cat(name=rule_payload['categoryName']))
        if not category:
            errors.append(f"Категория '{rule_payload['categoryName']}' не найдена.")
            continue
        
        new_rule = category_rule(
            category_name=category.name,
            category_id=category.id,
            percentage=rule_payload['percentage'],
            min_weight=rule_payload['minWeight'],
            max_weight=rule_payload['maxWeight']
        )
        new_category_rules.append(new_rule)
        
    if errors:
        reply.message = "Не удалось применить правила. Ошибки: " + "; ".join(errors)
        return

    reply.rules.set_rules_for_shelf(shelf.shelf_number, shelf.id, new_category_rules)
    
    reply.message = f"Правила для полки №{shelf_number} успешно обновлены. Всего правил: {len(new_category_rules)}."

def parse_command(command: str):
    parsed_result = parser.parse(command)

    if "error" in parsed_result:
        raise Exception(f"Ошибка разбора команды: {parsed_result['error']}")

    return parsed_result['command'], parsed_result['parameters']

def commands_handler(user_message: str, planogram_data, rules) -> server_message:
    try:
        command_name, parameters = parse_command(user_message)
    except Exception as e:
        if "command" in e.args[0] and e.args[0]["command"] == "ОПРЕДЕЛИ ПРАВИЛА ДЛЯ ПОЛКИ":
            command_name = e.args[0]["command"]
            parameters = e.args[0]["parameters"]
        
        return server_message(message=f"Ошибка: {e}", rules = rules_data.from_dict(rules))

    reply = server_message()
    reply.rules = rules_data.from_dict(rules)

    if command_name == "УСТАНОВИ СТЕЛЛАЖ": ### стирает правила
        place_shelf_unit(parameters, reply)
    elif command_name == "РАЗМЕСТИ КАТЕГОРИЮ": ### изменяет правила (добавляет категорию к полке), коллизия правил с процентом размещения
        place_category(parameters, reply, planogram_data)
    elif command_name == "РАЗМЕСТИ ТОВАР": ### коллизия правил для процента занимаемого места товарами категории, коллизия с отсутствием категории товара на полке 
        place_product(parameters, reply, planogram_data)
    elif command_name == "ОГРАНИЧЬ ПОЛКУ": #
        shelf_constrain(parameters, reply, planogram_data)
    elif command_name == "ОПРЕДЕЛИ ПРАВИЛА ДЛЯ ПОЛКИ":
        define_shelf_rules(parameters, reply, planogram_data)
    elif command_name == "ЗАПОЛНИ ОСТАТОК ПОЛКИ": ### изменяет правила (добавляет категорию или процент к ней) ------------------
        fill_free_space_on_shelf(parameters, reply, planogram_data)

    return reply