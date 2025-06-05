from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class CreateShelfUnit(FlaskForm):
    shelf_unit_number = IntegerField(
        'Номер стеллажа',
        validators=[
            DataRequired(message="Пожалуйста, введите номер стеллажа."),
            NumberRange(min=1, message="Номер стеллажа должен быть положительным числом.")
        ]
    )
    submit = SubmitField('Создать')

class UpdateShelfUnit(CreateShelfUnit): 
    id = IntegerField('ID', render_kw={'readonly': True}) 
    submit = SubmitField('Сохранить изменения') 