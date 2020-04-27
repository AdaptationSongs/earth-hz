from flask_wtf import FlaskForm
from wtforms import Form, SelectField, SubmitField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired, Optional, ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectField


def station_name(row):
    return row.name

def hours_list():
    choice_list = [(n, '{:02d}:00'.format(n)) for n in range(0, 24)]
    return choice_list

class FilterForm(FlaskForm):
    select_station = QuerySelectField('Monitoring Station:', get_label=station_name, allow_blank=True, blank_text='(All stations)')
    after = DateField('After:', validators=[Optional()])
    before = DateField('Before:', validators=[Optional()])
    from_hour = SelectField('From:', choices=hours_list(), validators=[Optional()], coerce=int)
    until_hour = SelectField('Until:', choices=hours_list(), validators=[Optional()], coerce=int)
    submit_button = SubmitField('Filter results')

    def validate_after(form, field):
        if field.data and form.before.data and (field.data > form.before.data):
            raise ValidationError('After and before dates reversed.')

    def validate_before(form, field):
        if field.data and form.after.data and (field.data == form.after.data):
            raise ValidationError('After and before cannot be the same day.')

