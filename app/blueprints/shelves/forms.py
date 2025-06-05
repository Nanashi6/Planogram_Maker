from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, SelectField, DecimalField
from wtforms.validators import DataRequired, NumberRange
from DataLayer.dao import ShelfUnitDAO

class CreateShelf(FlaskForm):
    shelf_unit_id = SelectField(
        'Стеллаж',
        validators=[DataRequired(message="Пожалуйста, выберите стеллаж.")],
        choices=[], 
        coerce=int
    )
    shelf_number = IntegerField(
        'Номер полки',
        validators=[
            DataRequired(message="Пожалуйста, введите номер полки."),
            NumberRange(min=1, message="Номер полки должен быть положительным числом.")
        ]
    )
    length = DecimalField(
        'Длина (см)',
        validators=[
            DataRequired(message="Пожалуйста, укажите длину полки."),
            NumberRange(min=0, message="Длина не может быть отрицательной.")
        ],
        places=2 
    )
    depth = DecimalField(
        'Глубина (см)',
        validators=[
            DataRequired(message="Пожалуйста, укажите глубину полки."),
            NumberRange(min=0, message="Глубина не может быть отрицательной.")
        ],
        places=2
    )
    height = DecimalField(
        'Высота (см)',
        validators=[
            DataRequired(message="Пожалуйста, укажите высоту."),
            NumberRange(min=0, message="Высота не может быть отрицательной.")
        ],
        places=2
    )
    max_weight = DecimalField(
        'Макс. вес (кг)',
        validators=[
            DataRequired(message="Пожалуйста, укажите максимальную нагрузку."),
            NumberRange(min=0, message="Максимальная нагрузка не может быть отрицательной.")
        ],
        places=2
    )
    submit = SubmitField('Создать')

    def __init__(self, *args, **kwargs):
        super(CreateShelf, self).__init__(*args, **kwargs)
        try:
            shelf_units = ShelfUnitDAO.get_all()
            self.shelf_unit_id.choices = [
                (su.id, f"Стеллаж №{su.shelf_unit_number} (ID: {su.id})")
                for su in shelf_units
            ]
            if not self.shelf_unit_id.choices:
                self.shelf_unit_id.choices = [(0, "Нет доступных стеллажей")]
        except Exception as e:
            print(f"Ошибка загрузки стеллажей: {e}")
            self.shelf_unit_id.choices = [(0, "Ошибка загрузки стеллажей")]


class UpdateShelf(CreateShelf):
    id = IntegerField('ID', render_kw={'readonly': True}) 
    submit = SubmitField('Сохранить изменения') 