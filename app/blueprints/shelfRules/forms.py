from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired
from DataLayer.dao import RuleDAO, ShelfDAO 

class CreateShelfRule(FlaskForm):
    rule_id = SelectField(
        'Общее правило выкладки',
        validators=[DataRequired(message="Пожалуйста, выберите общее правило.")],
        choices=[],
        coerce=int
    )
    shelf_id = SelectField(
        'Полка',
        validators=[DataRequired(message="Пожалуйста, выберите полку.")],
        choices=[],
        coerce=int
    )
    submit = SubmitField('Создать правило для полки')

    def __init__(self, *args, **kwargs):
        super(CreateShelfRule, self).__init__(*args, **kwargs)
        # Загрузка общих правил
        try:
            rules = RuleDAO.get_all() 
            self.rule_id.choices = [
                (r.id, f"Правило ID {r.id} (Б: {r.brand_sorting.name if r.brand_sorting else '-'}, П: {r.product_sorting.name if r.product_sorting else '-'})")
                for r in rules
            ]
            if not self.rule_id.choices:
                self.rule_id.choices = [(0, "Нет доступных общих правил")]
        except Exception as e:
            print(f"Ошибка загрузки общих правил для формы ShelfRule: {e}")
            self.rule_id.choices = [(0, "Ошибка загрузки общих правил")]

        # Загрузка полок
        try:
            shelves = ShelfDAO.get_all() 
            self.shelf_id.choices = [
                (s.id, f"Стеллаж №{s.shelf_unit.shelf_unit_number if s.shelf_unit else '?'}, Полка №{s.shelf_number} (ID: {s.id})")
                for s in shelves
            ]
            if not self.shelf_id.choices:
                self.shelf_id.choices = [(0, "Нет доступных полок")]
        except Exception as e:
            print(f"Ошибка загрузки полок для формы ShelfRule: {e}")
            self.shelf_id.choices = [(0, "Ошибка загрузки полок")]


class UpdateShelfRule(CreateShelfRule):
    id = IntegerField('ID', render_kw={'readonly': True})
    submit = SubmitField('Сохранить изменения')