from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, NumberRange, Optional, ValidationError
from DataLayer.dao import ShelfRuleDAO, CategoryDAO

class CreateCategoryRule(FlaskForm):
    shelf_rule_id = SelectField(
        'Правило полки',
        validators=[DataRequired(message="Пожалуйста, выберите правило полки.")],
        choices=[],
        coerce=int
    )
    category_id = SelectField(
        'Категория',
        validators=[DataRequired(message="Пожалуйста, выберите категорию.")],
        choices=[],
        coerce=int
    )
    share = FloatField(
        'Доля (%)',
        validators=[
            DataRequired(message="Доля обязательна."),
            NumberRange(min=0.0, max=100.0, message="Доля должна быть от 0 до 100.")
        ],
        default=0.0
    )
    min_weight = FloatField(
        'Минимальный вес (кг)',
        validators=[Optional(), NumberRange(min=0.0, message="Вес не может быть отрицательным.")],
        default=0.0, 
        render_kw={"placeholder": "0.000"}
    )
    max_weight = FloatField(
        'Максимальный вес (кг)',
        validators=[Optional(), NumberRange(min=0.0, message="Вес не может быть отрицательным.")],
        render_kw={"placeholder": "Неограниченно"}
    )
    submit = SubmitField('Создать правило категории')

    def __init__(self, *args, **kwargs):
        super(CreateCategoryRule, self).__init__(*args, **kwargs)

    def populate_choices(self, shelf_rule_id_to_select=None, category_id_to_select=None):
        # Загрузка правил полок
        try:
            shelf_rules = ShelfRuleDAO.get_all()
            self.shelf_rule_id.choices = [
                (sr.id, f"ID {sr.id} (Полка: {sr.shelf.shelf_number if sr.shelf else 'N/A'}, Общее правило ID: {sr.rule_id})")
                for sr in shelf_rules
            ]
            if not self.shelf_rule_id.choices:
                self.shelf_rule_id.choices = [(0, "Нет доступных правил полок")]
        except Exception as e:
            print(f"Ошибка загрузки правил полок для формы CategoryRule: {e}") 
            self.shelf_rule_id.choices = [(0, "Ошибка загрузки правил полок")]

        # Загрузка категорий
        try:
            categories = CategoryDAO.get_all() 
            self.category_id.choices = [(c.id, f"{c.name} (ID: {c.id})") for c in categories]
            if not self.category_id.choices:
                self.category_id.choices = [(0, "Нет доступных категорий")]
        except Exception as e:
            print(f"Ошибка загрузки категорий для формы CategoryRule: {e}")
            self.category_id.choices = [(0, "Ошибка загрузки категорий")]

    def validate_max_weight(self, field):
        if self.min_weight.data is not None and field.data is not None:
            if self.min_weight.data > field.data:
                raise ValidationError("Максимальный вес не может быть меньше минимального.")

class UpdateCategoryRule(CreateCategoryRule):
    id = IntegerField('ID', render_kw={'readonly': True})
    submit = SubmitField('Сохранить изменения')

    def __init__(self, *args, **kwargs):
        super(UpdateCategoryRule, self).__init__(*args, **kwargs)
        if 'obj' in kwargs and kwargs['obj']:
            self.shelf_rule_id.render_kw = {'disabled': True} 