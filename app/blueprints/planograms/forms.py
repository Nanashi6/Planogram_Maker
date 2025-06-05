from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired
from DataLayer.dao import ShelfUnitDAO

class CreatePlanogram(FlaskForm):
    name = StringField('Название планограммы', validators=[DataRequired(message="Пожалуйста, введите название планограммы.")])
    shelf_unit_id = SelectField(
        'Стеллаж',
        validators=[DataRequired(message="Пожалуйста, выберите стеллаж.")],
        choices=[], 
        coerce=int  
    )
    submit = SubmitField('Создать')

    def __init__(self, *args, **kwargs):
        super(CreatePlanogram, self).__init__(*args, **kwargs)
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


class UpdatePlanogramForm(CreatePlanogram): 
    id = IntegerField('ID', render_kw={'readonly': True})
    submit = SubmitField('Сохранить изменения') 