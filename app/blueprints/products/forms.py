from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField, DecimalField
from wtforms.validators import DataRequired, NumberRange
from DataLayer.enums import RatingEnum, SegmentEnum
from DataLayer.dao import BrandDAO, CategoryDAO 

class CreateProduct(FlaskForm): # Переименовано для ясности, т.к. CreateProduct может быть именем модели
    segment = SelectField(
        'Сегмент',
        validators=[DataRequired(message="Пожалуйста, выберите сегмент.")],
        choices=[(s.value, s.value) for s in SegmentEnum],
        coerce=str 
    )
    name = StringField('Название продукта', validators=[DataRequired(message="Пожалуйста, введите название продукта.")])
    
    barcode = StringField('Штрихкод', validators=[DataRequired()]) 

    SKU_rating = SelectField(
        'Рейтинг SKU',
        validators=[DataRequired(message="Пожалуйста, выберите рейтинг SKU.")],
        choices=[(r.value, r.value) for r in RatingEnum], 
        coerce=str 
    )

    length = DecimalField('Длина (см)', validators=[DataRequired(message="Укажите длину."), NumberRange(min=0, message="Длина не может быть отрицательной.")], places=2)
    depth = DecimalField('Глубина (см)', validators=[DataRequired(message="Укажите глубину."), NumberRange(min=0, message="Глубина не может быть отрицательной.")], places=2)
    height = DecimalField('Высота (см)', validators=[DataRequired(message="Укажите высоту."), NumberRange(min=0, message="Высота не может быть отрицательной.")], places=2)
    weight = DecimalField('Вес (кг)', validators=[DataRequired(message="Укажите вес."), NumberRange(min=0, message="Вес не может быть отрицательным.")], places=3)
    price = DecimalField('Цена', validators=[DataRequired(message="Пожалуйста, укажите цену."), NumberRange(min=0, message="Цена не может быть отрицательной.")], places=2)

    brand_id = SelectField(
        'Бренд',
        validators=[DataRequired(message="Пожалуйста, выберите бренд.")],
        choices=[], 
        coerce=int
    )

    category_id = SelectField(
        'Категория',
        validators=[DataRequired(message="Пожалуйста, выберите категорию.")],
        choices=[], 
        coerce=int
    )

    def __init__(self, *args, **kwargs):
        super(CreateProduct, self).__init__(*args, **kwargs)
        # Загрузка вариантов для брендов
        try:
            self.brand_id.choices = [(brand.id, brand.name) for brand in BrandDAO.get_all()]
            if not self.brand_id.choices:
                self.brand_id.choices = [(0, "Нет доступных брендов")]
        except Exception as e: 
            print(f"Ошибка загрузки брендов: {e}")
            self.brand_id.choices = [(0, "Ошибка загрузки брендов")]

        # Загрузка вариантов для категорий
        try:
            self.category_id.choices = [(category.id, category.name) for category in CategoryDAO.get_all()]
            if not self.category_id.choices:
                self.category_id.choices = [(0, "Нет доступных категорий")]
        except Exception as e: 
            print(f"Ошибка загрузки категорий: {e}")
            self.category_id.choices = [(0, "Ошибка загрузки категорий")]


    submit = SubmitField('Создать')

class UpdateProduct(CreateProduct):
    id = IntegerField('ID', render_kw={'readonly': True}) 
    submit = SubmitField('Обновить')