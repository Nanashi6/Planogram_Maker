from DataLayer.models import ShelfUnit

class planogram_data():
    """
    Данные о планограмме.
    """
    def __init__(self, id : int = None, name : str = None, shelf_unit : ShelfUnit = None, placed_products : dict = None):
        self.name = name
        self.id = id
        self.shelf_unit = shelf_unit
        self.placed_products = placed_products

    def to_json(self):
        """
        Преобразует объект planogram_data в словарь для JSON-сериализации.
        """
        shelf_unit_json = None
        if self.shelf_unit:
            shelf_unit_json = self.shelf_unit.to_dict()

        return {
            "id": self.id,
            "name": self.name,
            "shelf_unit": shelf_unit_json,
            "placed_products": self.placed_products
        }

class server_message():
    """
    Серверное сообщение клиенту.
    """
    def __init__(self, message = "", parsed_command = None, data : planogram_data = None):
        self.message = message
        self.parsed_command = parsed_command
        self.data = data

    def to_json(self):
        """
        Преобразует объект server_message в словарь для JSON-сериализации.
        """
        data_json = None
        if self.data:
            data_json = self.data.to_json()

        return {
            "message": self.message,
            "parsed_command": self.parsed_command,
            "data": data_json
        }