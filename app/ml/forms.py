from flask_wtf import FlaskForm
from wtforms import Form, SelectField, SubmitField, StringField, FloatField
from wtforms.validators import InputRequired, Optional, NumberRange
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed, FileRequired


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


class UseTrainingClipsForm(FlaskForm):
    use = SubmitField('Use')
    do_not_use = SubmitField('Do not use')
