from flask_wtf import FlaskForm
from wtforms import Form, SelectField, SubmitField, StringField, FloatField
from wtforms.validators import InputRequired, Optional, NumberRange
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed, FileRequired


def iteration_text(row):
    return row.model.name + ': ' + str(row.training_date)

class FilterForm(FlaskForm):
    model_iteration = QuerySelectField('Model:', get_label=iteration_text, validators=[Optional()], allow_blank=False)
    predicted_label = QuerySelectField('Predicted label:', validators=[Optional()], allow_blank=True, blank_text='(All)')
    threshold = FloatField('Threshold:', validators=[Optional(), NumberRange(min=0, max=1)])
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
