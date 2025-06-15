import json
import re
from .exceptions import ParsingError # <-- Импортируем наше новое исключение

class CommandParser:
    """
    Класс для разбора текстовых команд пользователя.
    В случае успеха возвращает {"command": "...", "parameters": {...}}.
    В случае ошибки выбрасывает исключение ParsingError.
    """
    
    def __init__(self, ex_comands_json_string: str):
        self.commands_meta = json.loads(ex_comands_json_string)
        self._prepare_commands()

    def _parse_shelf_command_params(self, cmd_def: dict, match_object) -> dict:
        """
        Кастомный парсер для команды 'ОПРЕДЕЛИ ПРАВИЛА ДЛЯ ПОЛКИ'.
        В случае успеха возвращает словарь с параметрами.
        В случае ошибки выбрасывает ParsingError.
        """
        try:
            shelf_number = int(match_object.group('номер_полки'))
            categories_string = match_object.group('правила_категорий').strip()
        except (ValueError, IndexError, AttributeError):
            raise ParsingError("Не удалось извлечь номер полки или список категорий из команды.")

        all_percentages = re.findall(r'(\d+(?:[.,]\d+)?)\s*%', categories_string)
        total_percentage = sum(float(p.replace(',', '.')) for p in all_percentages)
        
        if total_percentage > 100:
            raise ParsingError(f"Суммарный процент ({total_percentage}%) для полки не может превышать 100%.")

        category_parts = re.split(r',\s*(?![^()]*\))', categories_string)
        
        parsed_rules = []
        errors = []

        for part in category_parts:
            part = part.strip()
            if not part: continue
            
            match = re.match(r'^(?P<category_name>.+?)\s*\((?P<params>[^)]*)\)$', part)
            if not match:
                errors.append(f"Неверный формат для '{part}'. Ожидалось 'имя (параметры)'.")
                continue

            category_name = match.group('category_name').strip()
            params_str = match.group('params')
            
            rule = {"categoryName": category_name, "percentage": None, "minWeight": None, "maxWeight": None}

            params = [p.strip() for p in params_str.split('/')]
            found_percentage = False

            for param in params:
                if not param: continue
                
                if p_match := re.match(r'^(\d+(?:[.,]\d+)?)\s*%$', param):
                    rule['percentage'] = float(p_match.group(1).replace(',', '.'))
                    found_percentage = True
                elif min_w_match := re.match(r'^от\s+(\d+(?:[.,]\d+)?)\s*кг$', param, re.IGNORECASE):
                    rule['minWeight'] = float(min_w_match.group(1).replace(',', '.'))
                elif max_w_match := re.match(r'^до\s+(\d+(?:[.,]\d+)?)\s*кг$', param, re.IGNORECASE):
                    rule['maxWeight'] = float(max_w_match.group(1).replace(',', '.'))
            
            if not found_percentage:
                errors.append(f"Для категории '{category_name}' не указан обязательный процент.")
            
            parsed_rules.append(rule)

        if errors:
            raise ParsingError("Ошибки в параметрах: " + "; ".join(errors))
        
        return {
            "номер_полки": shelf_number,
            "правила_категорий": parsed_rules
        }

    def _prepare_commands(self):
        """Готовит определения команд, компилирует Regex."""
        for cmd_def in self.commands_meta:
            cmd_def['param_meta_dict'] = {p['name']: p for p in cmd_def.get('parameters', [])}
            command_name = cmd_def['command'].upper()

            if command_name == "ОПРЕДЕЛИ ПРАВИЛА ДЛЯ ПОЛКИ":
                cmd_def['regex'] = re.compile(
                    r"^ПОЛКА\s+(?P<номер_полки>\d+)\s*:\s*(?P<правила_категорий>.+)$",
                    re.IGNORECASE | re.UNICODE
                )
                cmd_def['custom_params_parser'] = self._parse_shelf_command_params
            
            elif command_name == "УСТАНОВИ СТЕЛЛАЖ":
                cmd_def['regex'] = re.compile(r"^УСТАНОВИ\s+СТЕЛЛАЖ\s+(\d+)$", re.IGNORECASE | re.UNICODE)
                cmd_def['param_names_from_groups'] = ["номер_стеллажа"]

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
                    "название_категории", "номер_полки", "доля_процентов",
                    "минимальный_вес", "максимальный_вес"
                ]
            
            elif command_name == "ЗАПОЛНИ ОСТАТОК ПОЛКИ":
                cmd_def['regex'] = re.compile(
                    r"^ЗАПОЛНИ\s+ОСТАТОК\s+ПОЛКИ\s+(?P<номер_полки>\d+)\s+КАТЕГОРИЕЙ\s+'(?P<название_категории>[^']+)'$",
                    re.IGNORECASE | re.UNICODE
                )

            elif command_name == "СОРТИРОВКА БРЕНДОВ":
                cmd_def['regex'] = re.compile(
                    r"^СОРТИРОВКА\s+БРЕНДОВ\s+'(?P<тип_сортировки>[^']+)'$",
                    re.IGNORECASE | re.UNICODE
                )

            elif command_name == "СОРТИРОВКА ТОВАРОВ":
                cmd_def['regex'] = re.compile(
                    r"^СОРТИРОВКА\s+ТОВАРОВ\s+'(?P<тип_сортировки>[^']+)'$",
                    re.IGNORECASE | re.UNICODE
                )

            elif command_name == "ГОРИЗОНТАЛЬНЫЙ ПРОМЕЖУТОК МЕЖДУ ТОВАРАМИ":
                cmd_def['regex'] = re.compile(
                    r"^\s*ГОРИЗОНТАЛЬНЫЙ\s+ПРОМЕЖУТОК\s+МЕЖДУ\s+ТОВАРАМИ\s+(?P<размер_см>\d+(?:[.,]\d+)?)\s*$",
                    re.IGNORECASE | re.UNICODE
                )

    def _parse_parameters(self, cmd_def: dict, match_object, group_names_ordered=None, param_names_from_groups_legacy=None) -> dict:
        """
        Стандартный парсер параметров.
        В случае успеха возвращает словарь с параметрами.
        В случае ошибки выбрасывает ParsingError.
        """
        parsed_params = {}
        errors = []
        param_meta_dict = cmd_def['param_meta_dict']
        params_to_iterate = {}

        if param_names_from_groups_legacy:
            groups = match_object.groups()
            for i, param_name in enumerate(param_names_from_groups_legacy):
                params_to_iterate[param_name] = groups[i] if i < len(groups) else None
        elif group_names_ordered:
            for param_name in group_names_ordered:
                params_to_iterate[param_name] = match_object.group(param_name) if param_name in match_object.groupdict() and match_object.group(param_name) is not None else None
        else:
             params_to_iterate = {k: v for k, v in match_object.groupdict().items()}

        if cmd_def['command'] == "РАЗМЕСТИ КАТЕГОРИЮ":
            if "ВЕС" in match_object.group(0).upper() and params_to_iterate.get("минимальный_вес") is None and params_to_iterate.get("максимальный_вес") is None:
                errors.append(f"После 'ВЕС' необходимо указать 'ОТ ...' и/или 'ДО ...'.")

        for param_name, group_value in params_to_iterate.items():
            param_info = param_meta_dict.get(param_name)
            if not param_info: continue
            
            if group_value is None:
                parsed_params[param_name] = None
                continue

            param_type = param_info['type']
            try:
                if param_type == 'integer': value_to_store = int(group_value)
                elif param_type == 'float': value_to_store = float(str(group_value).replace(',', '.'))
                else: value_to_store = str(group_value)
            except (ValueError, TypeError):
                errors.append(f"Неверное значение для '{param_name}' ('{group_value}'). Ожидался тип: {param_type}.")
                continue
            
            if 'min' in param_info and value_to_store < param_info['min']: errors.append(f"Значение '{param_name}' ({value_to_store}) меньше минимума ({param_info['min']}).")
            if 'max' in param_info and value_to_store > param_info['max']: errors.append(f"Значение '{param_name}' ({value_to_store}) больше максимума ({param_info['max']}).")
            if 'enum' in param_info and value_to_store not in param_info['enum']: errors.append(f"Значение '{param_name}' ('{value_to_store}') не из списка допустимых: {param_info['enum']}.")
            
            parsed_params[param_name] = value_to_store
        
        for p_name, p_info in param_meta_dict.items():
            if p_info.get('required') and (p_name not in parsed_params or parsed_params[p_name] is None):
                errors.append(f"Обязательный параметр '{p_name}' отсутствует.")

        if errors:
            raise ParsingError(f"Ошибки в параметрах для команды '{cmd_def['command']}': {'; '.join(errors)}")
        
        return parsed_params

    def parse(self, text: str) -> dict:
        """
        Главный метод, который разбирает входящую текстовую команду.
        """
        text = text.strip()

        for cmd_def in self.commands_meta:
            if 'regex_variants' in cmd_def:
                for variant in cmd_def['regex_variants']:
                    if match := variant['regex'].match(text):
                        parsed_params = self._parse_parameters(cmd_def, match, variant.get('group_names_ordered'), variant.get('param_names_from_groups'))
                        return cmd_def['command'], parsed_params
            
            elif 'regex' in cmd_def:
                if match := cmd_def['regex'].match(text):
                    if 'custom_params_parser' in cmd_def:
                        parsed_params = cmd_def['custom_params_parser'](cmd_def, match)
                    else:
                        parsed_params = self._parse_parameters(cmd_def, match, cmd_def.get('group_names_ordered'), cmd_def.get('param_names_from_groups'))
                    
                    return cmd_def['command'], parsed_params

        raise ParsingError("Неизвестная команда или неверный синтаксис.")