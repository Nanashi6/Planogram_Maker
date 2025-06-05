from DataLayer.dao import ShelfDAO, ProductDAO, PlanogramDAO
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange, Optional

class CreatePlacedProduct(FlaskForm):
    planogram_id = SelectField(
        'Планограмма',
        validators=[DataRequired(message="Пожалуйста, выберите планограмму.")],
        choices=[],
        coerce=int
    )
    shelf_id = SelectField(
        'Полка',
        validators=[DataRequired(message="Пожалуйста, выберите полку.")],
        choices=[],
        coerce=int
    )
    product_id = SelectField(
        'Продукт',
        validators=[DataRequired(message="Пожалуйста, выберите продукт.")],
        choices=[],
        coerce=int
    )
    position = IntegerField(
        'Позиция',
        validators=[DataRequired(message="Пожалуйста, укажите позицию."), NumberRange(min=0, message="Позиция не может быть отрицательной.")]
    )
    submit = SubmitField('Создать')

    def __init__(self, *args, **kwargs):
        super(CreatePlacedProduct, self).__init__(*args, **kwargs)
        # Загрузка вариантов для планограмм
        try:
            self.planogram_id.choices = [(p.id, p.name) for p in PlanogramDAO.get_all()]
            if not self.planogram_id.choices:
                self.planogram_id.choices = [(0, "Нет доступных планограмм")]
        except Exception as e:
            print(f"Ошибка загрузки планограмм: {e}")
            self.planogram_id.choices = [(0, "Ошибка загрузки планограмм")]

        # Загрузка вариантов для полок
        try:
            shelves_data = ShelfDAO.get_all()
            self.shelf_id.choices = [
                (s.id, f"Стеллаж №{s.shelf_unit.shelf_unit_number if s.shelf_unit else '?'}, Полка №{s.shelf_number} (ID: {s.id})")
                for s in shelves_data
            ]
            if not self.shelf_id.choices:
                self.shelf_id.choices = [(0, "Нет доступных полок")]
        except Exception as e:
            print(f"Ошибка загрузки полок: {e}")
            self.shelf_id.choices = [(0, "Ошибка загрузки полок")]

        # Загрузка вариантов для продуктов
        try:
            self.product_id.choices = [(p.id, p.name) for p in ProductDAO.get_all()]
            if not self.product_id.choices:
                self.product_id.choices = [(0, "Нет доступных продуктов")]
        except Exception as e:
            print(f"Ошибка загрузки продуктов: {e}")
            self.product_id.choices = [(0, "Ошибка загрузки продуктов")]


class UpdatePlacedProduct(CreatePlacedProduct):
    id = IntegerField('ID', render_kw={'readonly': True}) 
    submit = SubmitField('Сохранить изменения') 