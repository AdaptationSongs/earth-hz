from flask_wtf import FlaskForm
from wtforms import Form, SelectField, TextAreaField, SubmitField
from wtforms.validators import InputRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField


class FilterLabelsForm(FlaskForm):
    select_label = QuerySelectField('Label:', validators=[InputRequired()])
    submit_button = SubmitField('Filter results')


class EditLabelForm(FlaskForm):
    select_label = QuerySelectField('Label:', validators=[InputRequired()])
    notes = TextAreaField()
    submit_button = SubmitField('Save')


class DeleteLabelForm(FlaskForm):
    delete_button = SubmitField('Delete')
