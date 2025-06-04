from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField, DecimalField 
from wtforms.validators import DataRequired, NumberRange, Optional 
from DataLayer.enums import RatingEnum, SegmentEnum
from DataLayer.dao import CategoryBrandPlacementDAO

class CreateProduct(FlaskForm):
    segment = SelectField(
        'Сегмент', 
        validators=[DataRequired(message="Пожалуйста, выберите сегмент.")],
        choices=[(segment.value, segment.value) for segment in SegmentEnum], 
        coerce=SegmentEnum 
    )
    name = StringField('Название продукта', validators=[DataRequired(message="Пожалуйста, введите название продукта.")]) 
    barcode = StringField('Штрихкод', validators=[DataRequired()])
    SKU_rating = SelectField(
        'Рейтинг SKU', 
        validators=[DataRequired(message="Пожалуйста, выберите рейтинг SKU.")],
        choices=[(rating.value, rating.value) for rating in RatingEnum], 
        coerce=RatingEnum 
    )

    length = DecimalField('Длина (см)', validators=[DataRequired(), NumberRange(min=0, message="Длина не может быть отрицательной.")], places=2) 
    depth = DecimalField('Глубина (см)', validators=[DataRequired(), NumberRange(min=0, message="Глубина не может быть отрицательной.")], places=2) 
    height = DecimalField('Высота (см)', validators=[DataRequired(), NumberRange(min=0, message="Высота не может быть отрицательной.")], places=2) 
    weight = DecimalField('Вес (кг)', validators=[DataRequired(), NumberRange(min=0, message="Вес не может быть отрицательным.")], places=3) 
    price = DecimalField('Цена', validators=[DataRequired(message="Пожалуйста, укажите цену."), NumberRange(min=0, message="Цена не может быть отрицательной.")], places=2) 

    category_brand_placement_id = SelectField(
        'Связка Категория-Бренд', 
        validators=[DataRequired(message="Пожалуйста, выберите связку категория-бренд.")],
        choices=[],
        coerce=int
    )

    def __init__(self, *args, **kwargs):
        super(CreateProduct, self).__init__(*args, **kwargs)
        self.category_brand_placement_id.choices = [
            (item.id, f'{item.category.name} - {item.brand.name}')
            for item in CategoryBrandPlacementDAO.get_all()
        ]
        if not self.category_brand_placement_id.choices:
            self.category_brand_placement_id.choices = [(0, "Нет доступных связок Категория-Бренд")] 


    submit = SubmitField('Создать') 

class UpdateProduct(CreateProduct):
    id = IntegerField('ID', render_kw={'readonly': True})
    submit = SubmitField('Обновить') 