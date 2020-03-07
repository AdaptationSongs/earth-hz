from flask_wtf import FlaskForm
from wtforms import Form, SelectField, SubmitField, StringField
from wtforms.validators import InputRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed, FileRequired


def manual_id(row):
    return row.label


class FilterClustersForm(FlaskForm):
    select_label = QuerySelectField('Manual ID:', get_label=manual_id, get_pk=manual_id)
    submit_button = SubmitField('Filter results')


class UploadForm(FlaskForm):
    upload = FileField('Cluster CSV File', validators=[
        FileRequired(), FileAllowed(['csv'], 'CSV files only!')
    ])
    cluster_name = StringField('Description', validators=[InputRequired()])
    submit_button = SubmitField('Upload Now')


class DeleteForm(FlaskForm):
    delete_button = SubmitField('Delete')
