from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from DataLayer.enums import RatingEnum, SegmentEnum
from DataLayer.dao import CategoryDAO, BrandDAO

class CreateProduct(FlaskForm):
    segment = SelectField(
        'Segment',
        validators=[DataRequired()],
        choices=[(segment.value, segment.value) for segment in SegmentEnum],
        coerce=SegmentEnum
    )
    name = StringField('Product Name', validators=[DataRequired()])
    barcode = IntegerField('Barcode', validators=[DataRequired()])
    SKU_rating = SelectField(
        'SKU Rating',
        validators=[DataRequired()],
        choices=[(rating.value, rating.value) for rating in RatingEnum],
        coerce=RatingEnum
    )
    length = IntegerField('Length', validators=[DataRequired()])
    depth = IntegerField('Depth', validators=[DataRequired()])
    height = IntegerField('Height', validators=[DataRequired()])
    weight = IntegerField('Weight', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(CreateProduct, self).__init__(*args, **kwargs)
        self.category_id.choices = [(category.id, category.name) for category in CategoryDAO.get_all()]
        self.brand_id.choices = [(brand.id, brand.name) for brand in BrandDAO.get_all()]

    category_id = SelectField('Category', validators=[DataRequired()], choices=[])
    brand_id = SelectField('Brand', validators=[DataRequired()], choices=[])

    submit = SubmitField('Create')

class UpdateProduct(CreateProduct):
    id = IntegerField('ID', validators=[DataRequired()])
    submit = SubmitField('Update')