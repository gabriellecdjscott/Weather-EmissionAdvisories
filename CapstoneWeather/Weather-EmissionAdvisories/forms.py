from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class ICAOForm(FlaskForm):
    icao_code = StringField('ICAO Code', validators=[DataRequired(), Length(min=4, max=4)])
    submit = SubmitField('Submit')
