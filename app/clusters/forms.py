from flask_wtf import FlaskForm
from wtforms import Form, SelectField, SubmitField, StringField
from wtforms.validators import InputRequired, Optional
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed, FileRequired


def manual_id(row):
    return row.label


class FilterForm(FlaskForm):
    select_label = QuerySelectField('Manual ID:', get_label=manual_id, get_pk=manual_id, validators=[Optional()], allow_blank=True, blank_text='(All)')
    per_page = SelectField('Per page:', choices=[(10, '10 per page'), (25, '25 per page'), (50, '50 per page'), (100, '100 per page')], default=10, validators=[Optional()], coerce=int)
    submit_button = SubmitField('Filter results')


class UploadForm(FlaskForm):
    upload = FileField('Cluster CSV File', validators=[
        FileRequired(), FileAllowed(['csv'], 'CSV files only!')
    ])
    cluster_name = StringField('Description', validators=[InputRequired()])
    submit_button = SubmitField('Upload Now')


class DeleteForm(FlaskForm):
    delete_button = SubmitField('Delete')
