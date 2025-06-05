from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional
from DataLayer.enums import RatingEnum

class CreateBrand(FlaskForm):
    name = StringField('Название', validators=[DataRequired(message="Пожалуйста, введите название бренда.")])
    rating = SelectField(
        'Рейтинг',
        validators=[Optional()],
        choices=[('', '--- Выберите рейтинг ---')] + [(r.value, r.value) for r in RatingEnum], 
        coerce=str, 
        default='' 
    )
    submit = SubmitField('Создать')

class UpdateBrand(CreateBrand): 
    id = IntegerField('ID', render_kw={'readonly': True})
    submit = SubmitField('Сохранить изменения') 