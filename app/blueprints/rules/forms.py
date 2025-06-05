from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, NumberRange, Optional
from DataLayer.enums import BrandSorting, ProductSorting
from DataLayer.dao import PlanogramDAO

p_sort_keys = {
    ProductSorting.PriceAsc:    "Цена по возрастанию",
    ProductSorting.PriceDesc:   "Цена по убыванию",
    ProductSorting.RatingAsc:   "Рейтинг по возрастанию",
    ProductSorting.RatingDesc:  "Рейтинг по убыванию",
    ProductSorting.NameAsc:     "Название (А-Я)",
    ProductSorting.NameDesc:    "Название (Я-А)",
}

b_sort_keys = {
    BrandSorting.NameAsc:    "Название бренда (А-Я)",
    BrandSorting.NameDesc:   "Название бренда (Я-А)",
    BrandSorting.RatingAsc:  "Рейтинг бренда (по возрастанию)",
    BrandSorting.RatingDesc: "Рейтинг бренда (по убыванию)",
}

class CreateRule(FlaskForm):
    brand_sorting = SelectField(
        'Сортировка брендов',
        validators=[DataRequired(message="Пожалуйста, выберите правило сортировки брендов.")],
        choices=[(bs.value, b_sort_keys[bs.name]) for bs in BrandSorting],
        coerce=str
    )
    product_sorting = SelectField(
        'Сортировка продуктов',
        validators=[DataRequired(message="Пожалуйста, выберите правило сортировки продуктов.")],
        choices=[(ps.value, p_sort_keys[ps.name]) for ps in ProductSorting],
        coerce=str 
    )
    spacing = FloatField(
        'Отступ между продуктами (см)',
        validators=[
            DataRequired(message="Пожалуйста, укажите отступ."),
            NumberRange(min=0, message="Отступ не может быть отрицательным.")
        ],
        default=0.5
    )
    planogram_id = SelectField(
        'Планограмма',
        validators=[DataRequired()], 
        choices=[], 
        coerce=int,
        default=''
    )
    submit = SubmitField('Создать правило')

    def __init__(self, *args, **kwargs):
        super(CreateRule, self).__init__(*args, **kwargs)
        # Загрузка вариантов для планограмм
        try:
            planograms = PlanogramDAO.get_all()
            if planograms:
                self.planogram_id.choices = [(p.id, p.name) for p in planograms]
            else:
                self.planogram_id.choices = [(0, "Нет доступных планограмм")]
        except Exception as e:
            print(f"Ошибка загрузки планограмм для формы Rule: {e}")
            self.planogram_id.choices = [('', 'Ошибка загрузки планограмм')]


class UpdateRule(CreateRule):
    id = IntegerField('ID', render_kw={'readonly': True})
    submit = SubmitField('Сохранить изменения')