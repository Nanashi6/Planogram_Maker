from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired
from DataLayer.dao import ShelfUnitDAO

class CreatePlanogram(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    def __init__(self, *args, **kwargs):
        super(CreatePlanogram, self).__init__(*args, **kwargs)
        self.shelf_unit_id.choices = [(shelfUnit.id, "Стеллаж №" + str(shelfUnit.shelf_unit_number)) for shelfUnit in ShelfUnitDAO.get_all()]

    shelf_unit_id = SelectField('Shelf Unit', validators=[DataRequired()], choices=[])
    submit = SubmitField('Create')

class UpdatePlanogram(CreatePlanogram):
    id = IntegerField('ID', validators=[DataRequired()])
    submit = SubmitField('Update')