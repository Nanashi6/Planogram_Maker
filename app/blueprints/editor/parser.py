import json
import re

class CommandParser:
    def __init__(self, ex_comands_json_string):
        self.commands_meta = json.loads(ex_comands_json_string)
        self._prepare_commands()

    def _parse_shelf_categories_command(self, cmd_def, match_object):
        """
        Для команды 'ПОЛКА X: ...'.
        """
        try:
            shelf_number = int(match_object.group('номер_полки'))
            categories_string = match_object.group('categories_string').strip()
        except (ValueError, IndexError):
            return None, ["Не удалось извлечь номер полки или список категорий."]

        # Процент выше 100
        total_percentage = 0
        all_percentages = re.findall(r'(\d+)\s*%', categories_string)
        for p_str in all_percentages:
            total_percentage += int(p_str)
        
        if total_percentage > 100:
                return None, [f"Ошибка: Суммарный процент ({total_percentage}%) для полки превышает 100%."]

        category_parts = re.split(r',\s*(?![^()]*\))', categories_string)
        
        parsed_rules = []
        errors = []

        for part in category_parts:
            part = part.strip()
            if not part:
                continue

            match = re.match(r'^(?P<category_name>.+?)(?:\s*\((?P<params>[^)]*)\))?$', part)
            if not match:
                errors.append(f"Неверный формат для '{part}'. Ожидалось 'имя' или 'имя (параметры)'.")
                continue

            category_name = match.group('category_name').strip()
            params_str = match.group('params')
            
            rule = {
                "categoryName": category_name,
                "percentage": None,
                "minWeight": None,
                "maxWeight": None
            }

            # Если параметров в скобках нет, то правило все равно создается, но с пустыми значениями
            if params_str is None:
                errors.append(f"Для категории '{category_name}' не указаны параметры в скобках, включая обязательный процент.")
                parsed_rules.append(rule)
                continue

            # Извлекаем параметры из строки внутри скобок
            params = [p.strip() for p in params_str.split('/')]
            
            found_percentage = False
            for param in params:
                if not param: continue
                
                # Процент
                p_match = re.match(r'^(\d+(?:[.,]\d+)?)\s*%$', param)
                if p_match:
                    rule['percentage'] = float(p_match.group(1).replace(',', '.'))
                    found_percentage = True
                    continue
                
                # Мин. вес
                min_w_match = re.match(r'^от\s+(\d+(?:[.,]\d+)?)\s*кг$', param, re.IGNORECASE)
                if min_w_match:
                    rule['minWeight'] = float(min_w_match.group(1).replace(',', '.'))
                    continue

                # Макс. вес
                max_w_match = re.match(r'^до\s+(\d+(?:[.,]\d+)?)\s*кг$', param, re.IGNORECASE)
                if max_w_match:
                    rule['maxWeight'] = float(max_w_match.group(1).replace(',', '.'))
                    continue
            
            if not found_percentage:
                errors.append(f"Для категории '{category_name}' не указан обязательный процент.")
            
            parsed_rules.append(rule)

        if errors:
            return None, errors
        
        final_params = {
            "номер_полки": shelf_number,
            "правила_категорий": parsed_rules
        }
        return final_params, []

    def _prepare_commands(self):
        for cmd_def in self.commands_meta:
            cmd_def['param_meta_dict'] = {p['name']: p for p in cmd_def.get('parameters', [])}
            command_name = cmd_def['command']

            if command_name == "УСТАНОВИ СТЕЛЛАЖ":
                cmd_def['regex'] = re.compile(r"^УСТАНОВИ\s+СТЕЛЛАЖ\s+(\d+)$", re.IGNORECASE | re.UNICODE)
                cmd_def['param_names_from_groups'] = ["номер_стеллажа"] 
            elif command_name == "РАЗМЕСТИ ТОВАР":
                cmd_def['regex'] = re.compile(
                    r"^РАЗМЕСТИ\s+ТОВАР\s+(\d+)\s+НА\s+ПОЛКЕ\s+(\d+)"
                    r"(?:\s+В\s+КОЛИЧЕСТВЕ\s+(\d+)\s+ФЕЙСИНГОВ)?$", 
                    re.IGNORECASE | re.UNICODE
                )
                cmd_def['param_names_from_groups'] = ["штрихкод_товара", "номер_полки", "количество_фейсингов"]
            elif command_name == "УДАЛИ ПРОДУКТ":
                cmd_def['regex'] = re.compile(r"^УДАЛИ\s+ПРОДУКТ\s+(\d+)\s+С\s+ПОЛКИ\s+(\d+)$", re.IGNORECASE | re.UNICODE)
                cmd_def['param_names_from_groups'] = ["штрихкод_продукта", "номер_полки"]
            elif command_name == "ПЕРЕМЕСТИ ПРОДУКТ":
                cmd_def['regex'] = re.compile(
                    r"^ПЕРЕМЕСТИ\s+ПРОДУКТ\s+(\d+)\s+С\s+ПОЛКИ\s+(\d+)\s+НА\s+ПОЛКУ\s+(\d+)$", 
                    re.IGNORECASE | re.UNICODE
                )
                cmd_def['param_names_from_groups'] = ["штрихкод_продукта", "источник_полка", "цель_полка"]
            elif command_name == "РАЗМЕСТИ КАТЕГОРИЮ":
                cmd_def['regex'] = re.compile(
                    r"^РАЗМЕСТИ\s+КАТЕГОРИЮ\s+'(?P<название_категории>[^']+)'\s+НА\s+ПОЛКЕ\s+(?P<номер_полки>\d+)"
                    r"(?:\s+ЗАНЯВ\s+(?P<доля_процентов>\d+)\s*%\s*МЕСТА)?"
                    r"(?:\s+ВЕС"
                        r"(?:\s+ОТ\s+(?P<минимальный_вес>\d+(?:[.,]\d+)?)\s*КГ)?"  
                        r"(?:\s+ДО\s+(?P<максимальный_вес>\d+(?:[.,]\d+)?)\s*КГ)?" 
                    r")?$", 
                    re.IGNORECASE | re.UNICODE
                )
                cmd_def['group_names_ordered'] = [
                    "название_категории",
                    "номер_полки",
                    "доля_процентов",
                    "минимальный_вес",
                    "максимальный_вес"
                ]
            elif command_name == "ОГРАНИЧЬ ПОЛКУ":
                cmd_def['regex_variants'] = [
                    {
                        "regex": re.compile(
                            r"^ОГРАНИЧЬ\s+ПОЛКУ\s+(?P<номер_полки>\d+)\s+ТОЛЬКО\s+ДЛЯ\s+КАТЕГОРИИ\s+'(?P<название_категории>[^']+)'$",
                            re.IGNORECASE | re.UNICODE
                        ),
                        "group_names_ordered": ["номер_полки", "название_категории"]
                    },
                    {
                        "regex": re.compile(
                            r"^ОГРАНИЧЬ\s+ПОЛКУ\s+(?P<номер_полки>\d+)\s+ТОЛЬКО\s+ДЛЯ\s+БРЕНДА\s+'(?P<название_бренда>[^']+)'\s+ИЗ\s+КАТЕГОРИИ\s+'(?P<название_категории_бренда>[^']+)'$",
                            re.IGNORECASE | re.UNICODE
                        ),
                        "group_names_ordered": ["номер_полки", "название_бренда", "название_категории_бренда"]
                    }
                ]
            elif command_name == "РАЗМЕСТИ АВТОМАТИЧЕСКИ":
                cmd_def['regex'] = re.compile(
                    r"^РАЗМЕСТИ\s+АВТОМАТИЧЕСКИ\s+КАТЕГОРИЮ\s+'(?P<название_категории>[^']+)'\s+НА\s+ПОЛКЕ\s+(?P<номер_полки>\d+)"
                    r"(?:\s+СОРТИРУЯ\s+ПО\s+(?P<атрибут_сортировки>ЦЕНЕ|РЕЙТИНГУ_SKU|ДЛИНЕ)"
                    r"(?:\s+(?P<порядок_сортировки>ПО\s+ВОЗРАСТАНИЮ|ПО\s+УБЫВАНИЮ))?)?$",
                    re.IGNORECASE | re.UNICODE
                )
                cmd_def['group_names_ordered'] = [
                    "название_категории",
                    "номер_полки",
                    "атрибут_сортировки",
                    "порядок_сортировки"
                ]
            elif command_name == "ЗАПОЛНИ ОСТАТОК ПОЛКИ":
                cmd_def['regex'] = re.compile(
                    r"^ЗАПОЛНИ\s+ОСТАТОК\s+ПОЛКИ\s+(?P<номер_полки>\d+)\s+КАТЕГОРИЕЙ\s+'(?P<название_категории>[^']+)'$",
                    re.IGNORECASE | re.UNICODE
                )
                cmd_def['group_names_ordered'] = ["номер_полки", "название_категории"]
            elif command_name == "РАЗМЕСТИ БРЕНД":
                cmd_def['regex'] = re.compile(
                    r"^РАЗМЕСТИ\s+БРЕНД\s+'(?P<название_бренда>[^']+)'\s+ИЗ\s+КАТЕГОРИИ\s+'(?P<название_категории>[^']+)'\s+НА\s+ПОЛКЕ\s+(?P<номер_полки>\d+)"
                    r"(?:\s+ЗАНЯВ\s+(?P<доля_процентов>\d+)\s*%\s*МЕСТА)?$",
                    re.IGNORECASE | re.UNICODE
                )
                cmd_def['group_names_ordered'] = [
                    "название_бренда",
                    "название_категории",
                    "номер_полки",
                    "доля_процентов"
                ]

    def _parse_parameters(self, cmd_def, match_object, group_names_ordered=None, param_names_from_groups_legacy=None):
        parsed_params = {}
        errors = []
        param_meta_dict = cmd_def['param_meta_dict']
        
        params_to_iterate = {}

        if param_names_from_groups_legacy:
            groups = match_object.groups()
            for i, param_name in enumerate(param_names_from_groups_legacy):
                if i < len(groups):
                    params_to_iterate[param_name] = groups[i]
                else:
                    params_to_iterate[param_name] = None
        elif group_names_ordered:
            for param_name in group_names_ordered:
                params_to_iterate[param_name] = match_object.group(param_name) if param_name in match_object.groupdict() and match_object.group(param_name) is not None else None
        else:
             params_to_iterate = {k: v for k, v in match_object.groupdict().items()}


        if cmd_def['command'] == "РАЗМЕСТИ КАТЕГОРИЮ":
            min_w_val = params_to_iterate.get("минимальный_вес")
            max_w_val = params_to_iterate.get("максимальный_вес")

            full_match_text = match_object.group(0).upper()
            if "ВЕС" in full_match_text and min_w_val is None and max_w_val is None:
                errors.append(f"Для команды '{cmd_def['command']}' после 'ВЕС' необходимо указать 'ОТ <значение> КГ' и/или 'ДО <значение> КГ'.")

        for param_name, group_value in params_to_iterate.items():
            param_info = param_meta_dict.get(param_name)

            if param_info is None:
                if cmd_def['command'] == 'ОГРАНИЧЬ ПОЛКУ' and param_name == 'название_категории_бренда':
                    param_info = param_meta_dict.get('название_категории')
                    if param_info is None:
                         errors.append(f"Внутренняя ошибка: Не найдено определение для параметра 'название_категории' (для бренда) в команде '{cmd_def['command']}'.")
                         continue
                else:
                    errors.append(f"Внутренняя ошибка: Не найдено определение для параметра '{param_name}' в команде '{cmd_def['command']}'.")
                    continue
            
            if group_value is None:
                parsed_params[param_name] = None
                continue

            param_type = param_info['type']
            value_to_store = None
            try:
                if param_type == 'integer':
                    value_to_store = int(group_value)
                elif param_type == 'float':
                    value_to_store = float(str(group_value).replace(',', '.'))
                elif param_type == 'string':
                    value_to_store = str(group_value)
                    if param_name == 'порядок_сортировки':
                        value_to_store = ' '.join(value_to_store.split())
                else:
                    errors.append(f"Неподдерживаемый тип параметра '{param_type}' для '{param_name}'.")
                    continue
            except ValueError:
                errors.append(f"Неверное значение для '{param_name}' ('{group_value}'). Ожидался тип: {param_type}.")
                continue
            
            if 'min' in param_info and value_to_store < param_info['min']:
                errors.append(f"Значение параметра '{param_name}' ({value_to_store}) меньше минимально допустимого ({param_info['min']}).")
            if 'max' in param_info and value_to_store > param_info['max']:
                errors.append(f"Значение параметра '{param_name}' ({value_to_store}) больше максимально допустимого ({param_info['max']}).")
            if 'enum' in param_info:
                compare_value = value_to_store
                if compare_value not in param_info['enum']:
                    errors.append(f"Значение параметра '{param_name}' ('{value_to_store}') не является одним из допустимых: {', '.join(map(str, param_info['enum']))}.")
            
            parsed_params[param_name] = value_to_store

        for p_name_meta, p_info_meta in param_meta_dict.items():
            is_present_and_not_none = p_name_meta in parsed_params and parsed_params[p_name_meta] is not None
            is_brand_variant_ogranich_polku = cmd_def['command'] == 'ОГРАНИЧЬ ПОЛКУ' and \
                                            'название_бренда' in parsed_params and \
                                            parsed_params['название_бренда'] is not None

            if p_info_meta['required']:
                if not is_present_and_not_none:
                    if is_brand_variant_ogranich_polku and p_name_meta == 'название_категории':
                        if not ('название_категории_бренда' in parsed_params and parsed_params['название_категории_бренда'] is not None):
                             errors.append(f"Обязательный параметр 'название_категории' (для бренда) отсутствует в команде '{cmd_def['command']}'.")
                    else:
                        if p_name_meta not in params_to_iterate:
                             is_category_only_variant_ogranich = cmd_def['command'] == 'ОГРАНИЧЬ ПОЛКУ' and not is_brand_variant_ogranich_polku
                             if not (is_category_only_variant_ogranich and p_name_meta == 'название_бренда'):
                                errors.append(f"Внутренняя ошибка: обязательный параметр '{p_name_meta}' не определен для извлечения из текста команды '{cmd_def['command']}'.")
                        else:
                             errors.append(f"Обязательный параметр '{p_name_meta}' отсутствует или не имеет значения в команде '{cmd_def['command']}'.")
        
        if errors:
            return None, errors
        return parsed_params, []

    def parse(self, text: str):
        text = text.strip()

        shelf_cmd_regex = re.compile(r"^полка\s+(?P<номер_полки>\d+)\s*:\s*(?P<categories_string>.+)$", re.IGNORECASE | re.UNICODE)
        shelf_match = shelf_cmd_regex.match(text)
        if shelf_match:
            cmd_def = next((cmd for cmd in self.commands_meta if cmd['command'] == "ОПРЕДЕЛИ ПРАВИЛА ДЛЯ ПОЛКИ"), None)
            if not cmd_def:
                return {"error": "Внутренняя ошибка: не найдено определение для команды 'ОПРЕДЕЛИ ПРАВИЛА ДЛЯ ПОЛКИ'."}
            
            parsed_params, errors = self._parse_shelf_categories_command(cmd_def, shelf_match)
            if errors:
                return {"error": f"Ошибка валидации параметров: {'; '.join(errors)}"}
            return {"command": cmd_def['command'], "parameters": parsed_params}

        for cmd_def in self.commands_meta:
            group_names_ordered_for_cmd = cmd_def.get('group_names_ordered')
            param_names_legacy_for_cmd = cmd_def.get('param_names_from_groups')
            
            if 'regex_variants' in cmd_def:
                for variant in cmd_def['regex_variants']:
                    match = variant['regex'].match(text)
                    if match:
                        group_names_ordered_for_variant = variant.get('group_names_ordered')
                        param_names_legacy_for_variant = variant.get('param_names_from_groups')
                        
                        parsed_params, errors = self._parse_parameters(
                            cmd_def, 
                            match, 
                            group_names_ordered_for_variant, 
                            param_names_legacy_for_variant
                        )
                        if errors:
                            return {"error": f"Ошибка валидации параметров для команды '{cmd_def['command']}': {'; '.join(errors)}"}
                        return {"command": cmd_def['command'], "parameters": parsed_params, "description": cmd_def.get("description", "")}
            elif 'regex' in cmd_def:
                match = cmd_def['regex'].match(text)
                if match:
                    parsed_params, errors = self._parse_parameters(
                        cmd_def, 
                        match, 
                        group_names_ordered_for_cmd, 
                        param_names_legacy_for_cmd
                    )
                    if errors:
                         return {"error": f"Ошибка валидации параметров для команды '{cmd_def['command']}': {'; '.join(errors)}"}
                    return {"command": cmd_def['command'], "parameters": parsed_params, "description": cmd_def.get("description", "")}

        return {"error": "Неизвестная команда или неверный синтаксис."}