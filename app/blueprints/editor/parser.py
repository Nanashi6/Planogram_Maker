import json
import re

class CommandParser:
    def __init__(self, ex_comands_json_string):
        self.commands_meta = json.loads(ex_comands_json_string)
        self._prepare_commands()

    def _prepare_commands(self):
        for cmd_def in self.commands_meta:
            cmd_def['param_meta_dict'] = {p['name']: p for p in cmd_def.get('parameters', [])}
            
            command_name = cmd_def['command']

            if command_name == "УСТАНОВИ СТЕЛЛАЖ":
                cmd_def['regex'] = re.compile(r"^УСТАНОВИ\s+СТЕЛЛАЖ\s+(\d+)$", re.IGNORECASE | re.UNICODE)
                cmd_def['param_names_from_groups'] = ["номер_стеллажа"]
            elif command_name == "РАЗМЕСТИ ПРОДУКТ":
                cmd_def['regex'] = re.compile(
                    r"^РАЗМЕСТИ\s+ПРОДУКТ\s+(\d+)\s+НА\s+ПОЛКЕ\s+(\d+)"
                    r"(?:\s+В\s+КОЛИЧЕСТВЕ\s+(\d+)\s+ФЕЙСИНГОВ)?$", 
                    re.IGNORECASE | re.UNICODE
                )
                cmd_def['param_names_from_groups'] = ["штрихкод_продукта", "номер_полки", "количество_фейсингов"]
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
                    r"^РАЗМЕСТИ\s+КАТЕГОРИЮ\s+'([^']+)'\s+НА\s+ПОЛКЕ\s+(\d+)"
                    r"(?:\s+ЗАНЯВ\s+(\d+)\s*%\s*МЕСТА)?"                      
                    r"(?:\s+ВЕС\s+ОТ\s+(\d+(?:\.\d+)?)\s*КГ\s+ДО\s+(\d+(?:\.\d+)?)\s*КГ)?$",
                    re.IGNORECASE | re.UNICODE
                )
                cmd_def['param_names_from_groups'] = [
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
                            r"^ОГРАНИЧЬ\s+ПОЛКУ\s+(\d+)\s+ТОЛЬКО\s+ДЛЯ\s+КАТЕГОРИИ\s+'([^']+)'$",
                            re.IGNORECASE | re.UNICODE
                        ),
                        "param_names_from_groups": ["номер_полки", "название_категории"]
                    },
                    {
                        "regex": re.compile(
                            r"^ОГРАНИЧЬ\s+ПОЛКУ\s+(\d+)\s+ТОЛЬКО\s+ДЛЯ\s+БРЕНДА\s+'([^']+)'\s+ИЗ\s+КАТЕГОРИИ\s+'([^']+)'$",
                            re.IGNORECASE | re.UNICODE
                        ),
                        "param_names_from_groups": ["номер_полки", "название_бренда", "название_категории"]
                    }
                ]
            elif command_name == "РАЗМЕСТИ АВТОМАТИЧЕСКИ":
                cmd_def['regex'] = re.compile(
                    r"^РАЗМЕСТИ\s+АВТОМАТИЧЕСКИ\s+КАТЕГОРИЮ\s+'([^']+)'\s+НА\s+ПОЛКЕ\s+(\d+)"
                    r"(?:\s+СОРТИРУЯ\s+ПО\s+(ЦЕНЕ|РЕЙТИНГУ_SKU|ДЛИНЕ)"
                    r"(?:\s+(ПО\s+ВОЗРАСТАНИЮ|ПО\s+УБЫВАНИЮ))?)?$", 
                    re.IGNORECASE | re.UNICODE
                )
                cmd_def['param_names_from_groups'] = [
                    "название_категории", 
                    "номер_полки", 
                    "атрибут_сортировки", 
                    "порядок_сортировки"
                ]
            elif command_name == "ЗАПОЛНИ ОСТАТОК ПОЛКИ":
                cmd_def['regex'] = re.compile(
                    r"^ЗАПОЛНИ\s+ОСТАТОК\s+ПОЛКИ\s+(\d+)\s+КАТЕГОРИЕЙ\s+'([^']+)'$",
                    re.IGNORECASE | re.UNICODE
                )
                cmd_def['param_names_from_groups'] = ["номер_полки", "название_категории"]
            elif command_name == "РАЗМЕСТИ БРЕНД":
                cmd_def['regex'] = re.compile(
                    r"^РАЗМЕСТИ\s+БРЕНД\s+'([^']+)'\s+ИЗ\s+КАТЕГОРИИ\s+'([^']+)'\s+НА\s+ПОЛКЕ\s+(\d+)"
                    r"(?:\s+ЗАНЯВ\s+(\d+)\s*%\s*МЕСТА)?$", 
                    re.IGNORECASE | re.UNICODE
                )
                cmd_def['param_names_from_groups'] = [
                    "название_бренда", 
                    "название_категории", 
                    "номер_полки", 
                    "доля_процентов"
                ]

    def _parse_parameters(self, cmd_def, groups, param_names_from_groups):
        parsed_params = {}
        errors = []
        param_meta_dict = cmd_def['param_meta_dict']

        for i, group_value in enumerate(groups):
            if i >= len(param_names_from_groups): 
                errors.append(f"Внутренняя ошибка: несоответствие количества групп и имен параметров для команды '{cmd_def['command']}'.")
                continue
            
            param_name = param_names_from_groups[i]
            param_info = param_meta_dict.get(param_name)

            if param_info is None:
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
                    value_to_store = float(group_value.replace(',', '.'))
                elif param_type == 'string':
                    value_to_store = str(group_value)
                else:
                    errors.append(f"Неподдерживаемый тип параметра '{param_type}' для '{param_name}'.")
                    continue
            except ValueError:
                errors.append(f"Неверное значение для '{param_name}' ('{group_value}'). Ожидался тип: {param_type}.")
                continue
            
            # Валидация значения
            if 'min' in param_info and value_to_store < param_info['min']:
                errors.append(f"Значение параметра '{param_name}' ({value_to_store}) меньше минимально допустимого ({param_info['min']}).")
            if 'max' in param_info and value_to_store > param_info['max']:
                errors.append(f"Значение параметра '{param_name}' ({value_to_store}) больше максимально допустимого ({param_info['max']}).")
            if 'enum' in param_info:
                compare_value = group_value if param_type == 'string' else value_to_store
                if compare_value not in param_info['enum']:
                    errors.append(f"Значение параметра '{param_name}' ('{compare_value}') не является одним из допустимых: {', '.join(map(str, param_info['enum']))}.")
            
            parsed_params[param_name] = value_to_store

        # Проверка всех обязательных параметров команды
        for p_name_meta, p_info_meta in param_meta_dict.items():
            is_present_and_not_none = p_name_meta in parsed_params and parsed_params[p_name_meta] is not None
            
            if p_info_meta['required'] and not is_present_and_not_none:
                if p_name_meta not in param_names_from_groups:
                     errors.append(f"Внутренняя ошибка: обязательный параметр '{p_name_meta}' не определен для извлечения из текста команды '{cmd_def['command']}'.")
                else:
                    errors.append(f"Обязательный параметр '{p_name_meta}' отсутствует или не имеет значения в команде '{cmd_def['command']}'.")
        
        if errors:
            return None, errors
        return parsed_params, []

    def parse(self, text: str):
        text = text.strip()
        for cmd_def in self.commands_meta:
            if 'regex_variants' in cmd_def:
                for variant in cmd_def['regex_variants']:
                    match = variant['regex'].match(text)
                    if match:
                        groups = match.groups()
                        parsed_params, errors = self._parse_parameters(cmd_def, groups, variant['param_names_from_groups'])
                        if errors:
                            return {"error": f"Ошибка валидации параметров для команды '{cmd_def['command']}': {'; '.join(errors)}"}
                        return {"command": cmd_def['command'], "parameters": parsed_params, "description": cmd_def.get("description", "")}
            elif 'regex' in cmd_def:
                match = cmd_def['regex'].match(text)
                if match:
                    groups = match.groups()
                    parsed_params, errors = self._parse_parameters(cmd_def, groups, cmd_def['param_names_from_groups'])
                    if errors:
                         return {"error": f"Ошибка валидации параметров для команды '{cmd_def['command']}': {'; '.join(errors)}"}
                    return {"command": cmd_def['command'], "parameters": parsed_params, "description": cmd_def.get("description", "")}

        return {"error": "Неизвестная команда или неверный синтаксис."}