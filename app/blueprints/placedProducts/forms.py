from DataLayer.dao import ShelfDAO, ProductDAO, PlanogramDAO
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange

class CreatePlacedProduct(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(CreatePlacedProduct, self).__init__(*args, **kwargs)
        self.shelf_id.choices = [(shelf.id, "Стеллаж №" + str(shelf.shelf_unit.shelf_unit_number) + ". Полка №" + str(shelf.shelf_number)) for shelf in ShelfDAO.get_all()]
        self.product_id.choices = [(product.id, product.name) for product in ProductDAO.get_all()]
        self.planogram_id.choices = [(planogram.id, planogram.name) for planogram in PlanogramDAO.get_all()]

    shelf_id = SelectField('Shelf', validators=[DataRequired()], choices=[])
    product_id = SelectField('Product', validators=[DataRequired()], choices=[])
    planogram_id = SelectField('Planogram', validators=[DataRequired()], choices=[])

    position = IntegerField('Position', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Create')

class UpdatePlacedProduct(CreatePlacedProduct):
    id = IntegerField('ID', validators=[DataRequired()])
    submit = SubmitField('Update')