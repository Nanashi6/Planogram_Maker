from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from DataLayer.enums import RatingEnum, SegmentEnum
from DataLayer.dao import CategoryBrandPlacementDAO

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
        self.category_brand_placement_id.choices = [(item.id, f'{item.category.name} {item.brand.name}') for item in CategoryBrandPlacementDAO.get_all()]

    category_brand_placement_id = SelectField('Category-Brand Placement', validators=[DataRequired()], choices=[])

    submit = SubmitField('Create')

class UpdateProduct(CreateProduct):
    id = IntegerField('ID', validators=[DataRequired()])
    submit = SubmitField('Update')