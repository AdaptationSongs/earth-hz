from flask_wtf import FlaskForm
from wtforms import Form, SelectField, TextAreaField, SubmitField
from wtforms.validators import InputRequired, Optional
from wtforms.ext.sqlalchemy.fields import QuerySelectField


class FilterForm(FlaskForm):
    select_label = QuerySelectField('Label:', validators=[Optional()], allow_blank=True, blank_text='(All)')
    certain = SelectField('Certain:', choices=[('', 'Any'), ('0', 'Maybe'), ('1', 'Definitely')], default='1', validators=[Optional()])
    submit_button = SubmitField('Filter results')


class EditForm(FlaskForm):
    certainty = SelectField('Certainty:', choices=[(False, 'maybe'), (True, 'definitely')], default=True, validators=[InputRequired()], coerce=lambda x: x == 'True')
    select_type = QuerySelectField('Type:', validators=[InputRequired()])
    select_label = QuerySelectField('Label:', validators=[InputRequired()])
    select_sub_label = QuerySelectField('Sub-label:', validators=[Optional()], allow_blank=True)
    notes = TextAreaField()
    submit_button = SubmitField('Save')


class DeleteForm(FlaskForm):
    delete_button = SubmitField('Delete')
