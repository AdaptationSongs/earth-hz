from flask import render_template, abort, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from sqlalchemy import extract, func, and_
from app import db
from app.models import AudioFile, Equipment, MLModel, ModelIteration, ModelOutput, Project, ProjectLabel, Label, ModelLabel, LabeledClip
from app.user.permissions import ViewResultsPermission, UploadDataPermission
from app.ml import bp
from app.ml.forms import FilterForm, UploadForm
import pandas as pd
from datetime import datetime


@bp.route('/project/<project_id>')
@login_required
def list_outputs(project_id):
    permission = ViewResultsPermission(project_id)
    if permission.can():
        page = request.args.get('page', 1, type=int)
        iq = ModelIteration.query.join(MLModel).filter(MLModel.project_id == project_id).order_by(ModelIteration.training_date.desc())
        q = ModelOutput.query.join(AudioFile).join(ModelIteration).join(MLModel).filter(MLModel.project_id == project_id)
        iteration = request.args.get('iteration', iq.first().id, type=int)
        q = q.filter(ModelIteration.id == iteration)
        predicted_label = request.args.get('label', type=int)
        if predicted_label:
            q = q.filter(ModelOutput.label_id == predicted_label)
        min_prob = request.args.get('min_prob', 0.99, type=float)
        q = q.filter(ModelOutput.probability >= min_prob)
        max_prob = request.args.get('max_prob', 1.0, type=float)
        q = q.filter(ModelOutput.probability <= max_prob)
        station = request.args.get('station', type=int)
        if station:
            q = q.join(Equipment, AudioFile.sn == Equipment.serial_number).filter(Equipment.station_id == station)
        start_date = request.args.get('start_date')
        if start_date:
            q = q.filter(func.date(AudioFile.timestamp) >= start_date)
        end_date = request.args.get('end_date')
        if end_date:
            q = q.filter(func.date(AudioFile.timestamp) <= end_date)
        start_hour = request.args.get('start_hour', type=int)
        if start_hour and start_hour > 0:
            q = q.filter(extract('hour', AudioFile.timestamp) >= start_hour)
        end_hour = request.args.get('end_hour', type=int)
        if end_hour and end_hour < 23:
            q = q.filter(extract('hour', AudioFile.timestamp) <= end_hour)
        verification = request.args.get('verification')
        if verification == 'confirmed':
            q = q.join(LabeledClip, (LabeledClip.file_name == ModelOutput.file_name) & (LabeledClip.offset == ModelOutput.offset) & (LabeledClip.label_id == ModelOutput.label_id))
        if verification == 'unverified':
            q = q.outerjoin(LabeledClip, (LabeledClip.file_name == ModelOutput.file_name) & (LabeledClip.offset == ModelOutput.offset)).filter(LabeledClip.id == None)
        sort = request.args.get('sort')
        single = request.args.get('single')
        if sort == 'prob' or sort == None:
            if single == 'on':
                subq = q.with_entities(ModelOutput.id, func.row_number().over(order_by=ModelOutput.probability.desc(), partition_by=ModelOutput.file_name).label('rank')).subquery()
                q = ModelOutput.query.join(subq, ModelOutput.id == subq.c.id).filter(subq.c.rank == 1).order_by(ModelOutput.probability.desc())
            else:
                q = q.order_by(ModelOutput.probability.desc())
        if sort == 'earliest':
            q = q.order_by(ModelOutput.file_name).order_by(ModelOutput.offset)
            if single == 'on':
                q = q.distinct(ModelOutput.file_name)
        if sort == 'latest':
            q = q.order_by(ModelOutput.file_name.desc()).order_by(ModelOutput.offset.desc())
            if single == 'on':
                q = q.distinct(ModelOutput.file_name)
        predictions = q.paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
        return render_template('ml/output_list.html', title='Machine Learning Output', predictions=predictions, project_id=project_id)
    # permission denied 
    abort(403)


@bp.route('/project/<project_id>/upload_single_label', methods=['GET', 'POST'])
@login_required
def upload_single_label(project_id):
    permission = UploadDataPermission(project_id)
    if permission.can():
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
    # permission denied 
    abort(403)


@bp.route('/_get_models/<project_id>')
def _get_models(project_id):
    q = MLModel.query.filter(MLModel.project_id == project_id)
    results = q.all()
    models = [{'id': r.id, 'name': r.name} for r in results]
    return jsonify(models)


@bp.route('/_get_model_iterations/<model_id>')
def _get_model_iterations(model_id):
    q = ModelIteration.query.filter(ModelIteration.model_id == model_id)
    results = q.order_by(ModelIteration.training_date.desc()).all()
    iterations = [{'id': r.id, 'training_date': r.training_date} for r in results]
    return jsonify(iterations)


@bp.route('/_get_model_labels/<iteration_id>')
def _get_model_labels(iteration_id):
    q = ModelLabel.query.join(Label, ModelLabel.label_id == Label.id).filter(ModelLabel.iteration_id == iteration_id)
    results = q.order_by(Label.name).all()
    labels = [{'id': r.label.id, 'name': r.label.name} for r in results]
    return jsonify(labels)

