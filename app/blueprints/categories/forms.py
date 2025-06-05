from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField 
from wtforms.validators import DataRequired 

class CreateCategory(FlaskForm): 
    name = StringField('Название', validators=[DataRequired(message="Пожалуйста, введите название категории.")])

    submit = SubmitField('Создать')

class UpdateCategory(CreateCategory): 
    id = IntegerField('ID', render_kw={'readonly': True}) 
    submit = SubmitField('Сохранить изменения') 