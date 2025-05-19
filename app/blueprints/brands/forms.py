from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField, DecimalField
from wtforms.validators import DataRequired, NumberRange
from DataLayer.dao import CategoryDAO

from DataLayer.enums import RatingEnum

class CreateBrand(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    rating = SelectField(
        'Rating',
        validators=[DataRequired()],
        choices=[(rating.value, rating.value) for rating in RatingEnum],
        coerce=RatingEnum
    )

    def __init__(self, *args, **kwargs):
        super(CreateBrand, self).__init__(*args, **kwargs)
        self.category_id.choices = [(category.id, category.name) for category in CategoryDAO.get_all()]

    category_id = SelectField('Category', validators=[DataRequired()], choices=[])

    share = DecimalField('Share', validators=[DataRequired(), NumberRange(min=0, max=100)], places=1)
    submit = SubmitField('Create')

class UpdateBrand(CreateBrand):
    id = IntegerField('ID', validators=[DataRequired()])
    submit = SubmitField('Update')