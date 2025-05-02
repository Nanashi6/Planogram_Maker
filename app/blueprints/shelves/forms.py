from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired
from DataLayer.dao import ShelfUnitDAO

class CreateShelf(FlaskForm):
    shelf_number = IntegerField('Shelf Number', validators=[DataRequired()])
    length = IntegerField('Length', validators=[DataRequired()])
    depth = IntegerField('Depth', validators=[DataRequired()])
    height = IntegerField('Height', validators=[DataRequired()])
    max_weight = IntegerField('Max Weight', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(CreateShelf, self).__init__(*args, **kwargs)
        self.shelf_unit_id.choices = [(unit.id, "Стеллаж №" + str(unit.shelf_unit_number)) for unit in ShelfUnitDAO.get_all()]

    shelf_unit_id = SelectField('Shelf Unit', validators=[DataRequired()], choices=[])

    submit = SubmitField('Create')

class UpdateShelf(CreateShelf):
    id = IntegerField('ID', validators=[DataRequired()])
    submit = SubmitField('Update')