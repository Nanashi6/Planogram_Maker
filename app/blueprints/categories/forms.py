from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, DecimalField
from wtforms.validators import DataRequired, NumberRange

class CreateCategory(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    share = DecimalField('Share', validators=[DataRequired(), NumberRange(min=0, max=100)], places=1)
    submit = SubmitField('Create')

class UpdateCategory(CreateCategory):
    id = IntegerField('ID', validators=[DataRequired()])
    submit = SubmitField('Update')