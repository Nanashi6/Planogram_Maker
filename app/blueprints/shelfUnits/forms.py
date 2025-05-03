from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired

class CreateShelfUnit(FlaskForm):
    shelf_unit_number = IntegerField('Shelf Unit Number', validators=[DataRequired()])
    submit = SubmitField('Create')

class UpdateShelfUnit(CreateShelfUnit):
    id = IntegerField('ID', validators=[DataRequired()])
    submit = SubmitField('Update')