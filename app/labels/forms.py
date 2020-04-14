from flask_wtf import FlaskForm
from wtforms import Form, SelectField, TextAreaField, SubmitField
from wtforms.validators import InputRequired, Optional
from wtforms.ext.sqlalchemy.fields import QuerySelectField


class FilterForm(FlaskForm):
    select_label = QuerySelectField('Label:', validators=[Optional()], allow_blank=True, blank_text='(All)')
    submit_button = SubmitField('Filter results')


class EditForm(FlaskForm):
    select_label = QuerySelectField('Label:', validators=[InputRequired()])
    notes = TextAreaField()
    submit_button = SubmitField('Save')


class DeleteForm(FlaskForm):
    delete_button = SubmitField('Delete')
