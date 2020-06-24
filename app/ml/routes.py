from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from app import db
from app.models import AudioFile, MLModel, ModelIteration, ModelOutput, Project, ProjectLabel, Label
from app.user.roles import admin_permission
from app.ml import bp
from app.ml.forms import FilterForm, UploadForm
import pandas as pd


@bp.route('/project/<project_id>')
@login_required
@admin_permission.require(http_exception=403)
def list_outputs(project_id):
    page = request.args.get('page', 1, type=int)
    filter_form = FilterForm(request.args)
    filter_form.predicted_label.query = Label.query.join(ProjectLabel, Label.id == ProjectLabel.label_id).filter(ProjectLabel.project_id == project_id)
    q = ModelOutput.query.join(ModelIteration).join(MLModel).filter(MLModel.project_id == project_id)
    if filter_form.validate():
        if filter_form.predicted_label.data:
            q = q.filter(ModelOutput.label_id == filter_form.select_label.data.id)
    else:
        filter_form.threshold.data = 0.99
    if filter_form.threshold.data:
        q = q.filter(ModelOutput.probability >= filter_form.threshold.data)
    predictions = q.join(AudioFile).order_by(AudioFile.timestamp).order_by(ModelOutput.offset).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
    return render_template('ml/output_list.html', title='Machine Learning Output', predictions=predictions, filter_form=filter_form, project_id=project_id)


@bp.route('/project/<project_id>/upload_single_label', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def upload_single_label(project_id):
    form = UploadForm()
    form.select_iteration.query = ModelIteration.query.join(MLModel).join(Project).filter(Project.id == project_id)
    form.select_label.query = Label.query.join(ProjectLabel, Label.id == ProjectLabel.label_id).join(Project).filter(Project.id == project_id) 
    if form.validate_on_submit():
        f = form.upload.data
        df = pd.read_csv(f)
        df.columns = df.columns.str.lower()
        df = df.rename(columns={'in file': 'file_name', 'predicted_probability': 'probability'})
        import_df = df[['file_name', 'offset', 'duration', 'probability']]
        import_df['iteration_id'] = form.select_iteration.data.id
        import_df['label_id'] = form.select_label.data.id
        import_df.to_sql('model_outputs', con=db.engine, index=False, if_exists='append')
        return redirect(url_for('ml.list_outputs', project_id=project_id))
    return render_template('ml/upload_single_label.html', title="Upload predictions file", form=form)

