from flask_wtf import FlaskForm
from wtforms import Form, SelectField, SubmitField, StringField, FloatField
from wtforms.validators import InputRequired, Optional, NumberRange
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed, FileRequired


def iteration_text(row):
    return row.model.name + ': ' + str(row.updated)

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
    delete_button = SubmitField('Remove')


class PreviousForm(FlaskForm):
    previous_button = SubmitField('Previous')


class NextForm(FlaskForm):
    next_button = SubmitField('Next')


class IterationLabelForm(FlaskForm):
    combine_with = QuerySelectField('Combine with:', validators=[Optional()], allow_blank=True, blank_text='(None)')
    submit_button = SubmitField('Save')


class EditModelForm(FlaskForm):
    name = StringField(validators=[InputRequired()])
    description = StringField()
    submit_button = SubmitField('Save')


class EditIterationForm(FlaskForm):
    notes = StringField()
    submit_button = SubmitField('Save')
