import json
import re

class CommandParser:
    def __init__(self, ex_comands):
        self.commands_meta = json.loads(ex_comands)
        self._prepare_commands()

    def _prepare_commands(self):
        for cmd_def in self.commands_meta:
            cmd_def['param_meta_dict'] = {p['name']: p for p in cmd_def.get('parameters', [])}
            
            # Определяем регулярные выражения и порядок имен параметров из групп
            if cmd_def['command'] == "УСТАНОВИ СТЕЛЛАЖ":
                cmd_def['regex'] = re.compile(r"^УСТАНОВИ\s+СТЕЛЛАЖ\s+(\d+)$", re.IGNORECASE | re.UNICODE)
                cmd_def['param_names_from_groups'] = ["номер_стеллажа"]
            elif cmd_def['command'] == "РАЗМЕСТИ ПРОДУКТ":
                cmd_def['regex'] = re.compile(r"^РАЗМЕСТИ\s+ПРОДУКТ\s+(\d+)\s+НА\s+ПОЛКЕ\s+(\d+)(?:\s+В\s+КОЛИЧЕСТВЕ\s+(\d+)\s+ФЕЙСИНГОВ)?$", re.IGNORECASE | re.UNICODE)
                cmd_def['param_names_from_groups'] = ["штрихкод_продукта", "номер_полки", "количество_фейсингов"]
            elif cmd_def['command'] == "УДАЛИ ПРОДУКТ":
                cmd_def['regex'] = re.compile(r"^УДАЛИ\s+ПРОДУКТ\s+(\d+)\s+С\s+ПОЛКИ\s+(\d+)$", re.IGNORECASE | re.UNICODE)
                cmd_def['param_names_from_groups'] = ["штрихкод_продукта", "номер_полки"]
            elif cmd_def['command'] == "ПЕРЕМЕСТИ ПРОДУКТ":
                cmd_def['regex'] = re.compile(r"^ПЕРЕМЕСТИ\s+ПРОДУКТ\s+(\d+)\s+С\s+ПОЛКИ\s+(\d+)\s+НА\s+ПОЛКУ\s+(\d+)$", re.IGNORECASE | re.UNICODE)
                cmd_def['param_names_from_groups'] = ["штрихкод_продукта", "источник_полка", "цель_полка"]
            elif cmd_def['command'] == "РАЗМЕСТИ КАТЕГОРИЮ":
                cmd_def['regex'] = re.compile(r'^РАЗМЕСТИ\s+КАТЕГОРИЮ\s+"([^"]+)"\s+НА\s+ПОЛКЕ\s+(\d+)(?:\s+ЗАНЯВ\s+(\d+)\s*%\s+МЕСТА)?$', re.IGNORECASE | re.UNICODE)
                cmd_def['param_names_from_groups'] = ["название_категории", "номер_полки", "доля_процентов"]
            elif cmd_def['command'] == "ОГРАНИЧЬ ПОЛКУ":
                cmd_def['regex_variants'] = [
                    {
                        "regex": re.compile(r'^ОГРАНИЧЬ\s+ПОЛКУ\s+(\d+)\s+ТОЛЬКО\s+ДЛЯ\s+КАТЕГОРИИ\s+"([^"]+)"$', re.IGNORECASE | re.UNICODE),
                        "param_names_from_groups": ["номер_полки", "название_категории"]
                    },
                    {
                        "regex": re.compile(r'^ОГРАНИЧЬ\s+ПОЛКУ\s+(\d+)\s+ТОЛЬКО\s+ДЛЯ\s+БРЕНДА\s+"([^"]+)"\s+ИЗ\s+КАТЕГОРИИ\s+"([^"]+)"$', re.IGNORECASE | re.UNICODE),
                        "param_names_from_groups": ["номер_полки", "название_бренда", "название_категории"]
                    }
                ]
            elif cmd_def['command'] == "РАЗМЕСТИ АВТОМАТИЧЕСКИ":
                cmd_def['regex'] = re.compile(r'^РАЗМЕСТИ\s+АВТОМАТИЧЕСКИ\s+КАТЕГОРИЮ\s+"([^"]+)"\s+НА\s+ПОЛКЕ\s+(\d+)(?:\s+СОРТИРУЯ\s+ПО\s+(ЦЕНЕ|РЕЙТИНГУ_SKU|ДЛИНЕ)(?:\s+(ПО\s+ВОЗРАСТАНИЮ|ПО\s+УБЫВАНИЮ))?)?$', re.IGNORECASE | re.UNICODE)
                cmd_def['param_names_from_groups'] = ["название_категории", "номер_полки", "атрибут_сортировки", "порядок_сортировки"]
            elif cmd_def['command'] == "ЗАПОЛНИ ОСТАТОК ПОЛКИ":
                cmd_def['regex'] = re.compile(r'^ЗАПОЛНИ\s+ОСТАТОК\s+ПОЛКИ\s+(\d+)\s+КАТЕГОРИЕЙ\s+"([^"]+)"$', re.IGNORECASE | re.UNICODE)
                cmd_def['param_names_from_groups'] = ["номер_полки", "название_категории"]
            elif cmd_def['command'] == "РАЗМЕСТИ БРЕНД":
                cmd_def['regex'] = re.compile(r'^РАЗМЕСТИ\s+БРЕНД\s+"([^"]+)"\s+ИЗ\s+КАТЕГОРИИ\s+"([^"]+)"\s+НА\s+ПОЛКЕ\s+(\d+)(?:\s+ЗАНЯВ\s+(\d+)\s*%\s+МЕСТА)?$', re.IGNORECASE | re.UNICODE)
                cmd_def['param_names_from_groups'] = ["название_бренда", "название_категории", "номер_полки", "доля_процентов"]

    def _parse_parameters(self, cmd_def, groups, param_names_from_groups):
        parsed_params = {}
        errors = []
        param_meta_dict = cmd_def['param_meta_dict']

        for i, group_value in enumerate(groups):
            if i >= len(param_names_from_groups):
                continue
            
            param_name = param_names_from_groups[i]
            param_info = param_meta_dict.get(param_name)

            if param_info is None:
                errors.append(f"Внутренняя ошибка: Не найдено определение для параметра '{param_name}'.")
                continue
            
            if group_value is None: # Необязательный параметр не предоставлен
                parsed_params[param_name] = None
                continue

            param_type = param_info['type']
            value_to_store = None
            try:
                if param_type == 'integer':
                    value_to_store = int(group_value)
                elif param_type == 'string':
                    value_to_store = str(group_value)
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
                # Значения enum извлекаются из regex в верхнем регистре (как они определены в regex)
                # Предполагаем, что enum в JSON также в верхнем регистре
                if value_to_store not in param_info['enum']:
                    errors.append(f"Значение параметра '{param_name}' ('{value_to_store}') не является одним из допустимых: {param_info['enum']}.")
            
            parsed_params[param_name] = value_to_store

        # Проверка всех обязательных параметров команды
        for p_name_meta, p_info_meta in param_meta_dict.items():
            if p_info_meta['required'] and (p_name_meta not in parsed_params or parsed_params[p_name_meta] is None):
                errors.append(f"Обязательный параметр '{p_name_meta}' отсутствует или не имеет значения.")
        
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
                            return {"error": f"Ошибка синтаксиса для команды '{cmd_def['command']}': {'; '.join(errors)}"}
                        return {"command": cmd_def['command'], "parameters": parsed_params}
            elif 'regex' in cmd_def:
                match = cmd_def['regex'].match(text)
                if match:
                    groups = match.groups()
                    parsed_params, errors = self._parse_parameters(cmd_def, groups, cmd_def['param_names_from_groups'])
                    if errors:
                         return {"error": f"Ошибка синтаксиса для команды '{cmd_def['command']}': {'; '.join(errors)}"}
                    return {"command": cmd_def['command'], "parameters": parsed_params}
        
        return {"error": "Неизвестная команда или неверный синтаксис."}
