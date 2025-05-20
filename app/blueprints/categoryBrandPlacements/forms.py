from flask_wtf import FlaskForm
from wtforms import SelectField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange, Optional
from DataLayer.dao import CategoryDAO, BrandDAO

class CreateCategoryBrandPlacementForm(FlaskForm):
    category_id = SelectField(
        'Category',
        validators=[DataRequired()],
        coerce=int
    )
    brand_id = SelectField(
        'Brand',
        validators=[DataRequired()],
        coerce=int
    )
    share = FloatField(
        'Share (%)',
        validators=[Optional(), NumberRange(min=0, max=100, message="Share must be between 0 and 100.")]
    )
    submit = SubmitField('Create')

    def __init__(self, *args, **kwargs):
        super(CreateCategoryBrandPlacementForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(category.id, category.name) for category in CategoryDAO.get_all()]
        self.brand_id.choices = [(brand.id, brand.name) for brand in BrandDAO.get_all()]

class UpdateCategoryBrandPlacementForm(CreateCategoryBrandPlacementForm):
    id = HiddenField('ID', validators=[DataRequired()])
    submit = SubmitField('Update')