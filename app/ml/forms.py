from flask_wtf import FlaskForm
from wtforms import Form, SelectField, SubmitField, StringField
from wtforms.validators import InputRequired, Optional
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed, FileRequired


def manual_id(row):
    return row.label


class FilterForm(FlaskForm):
    select_label = QuerySelectField('Label:', validators=[Optional()], allow_blank=True, blank_text='(All)')
    submit_button = SubmitField('Filter results')


class UploadForm(FlaskForm):
    upload = FileField('Predictions CSV File', validators=[
        FileRequired(), FileAllowed(['csv'], 'CSV files only!')
    ])
    select_iteration = QuerySelectField('Model Iteration')
    select_label = QuerySelectField('Label')
    submit_button = SubmitField('Upload Now')


class DeleteForm(FlaskForm):
    delete_button = SubmitField('Delete')
