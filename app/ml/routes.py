from flask import render_template, abort, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from sqlalchemy import extract, func, and_
from app import db
from app.models import AudioFile, Equipment, MonitoringStation, MLModel, ModelIteration, ModelOutput, Project, ProjectLabel, Label, LabelType, ModelLabel, LabeledClip, TrainingClip, StatusEnum
from app.schema import ModelOutputSchema
from app.user.permissions import ViewResultsPermission, UploadDataPermission, ManageLabelsPermission
from app.ml import bp
from app.ml.forms import UploadForm, IterationLabelForm, DeleteForm, PreviousForm, NextForm, EditModelForm, EditIterationForm, UseTrainingClipsForm
from app.labels.forms import FilterForm
import pandas as pd
from datetime import datetime
import flask_excel as excel


@bp.route('/project/<project_id>')
@login_required
def list_outputs(project_id):
    permission = ViewResultsPermission(project_id)
    if permission.can():
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', type=int) or current_app.config['ITEMS_PER_PAGE']
        q = ModelOutput.query.join(AudioFile).join(AudioFile.monitoring_station).join(ModelIteration)
        iq = ModelIteration.query.join(MLModel).filter(MLModel.project_id == project_id).filter(ModelIteration.status == StatusEnum.finished).order_by(ModelIteration.updated.desc())
        latest_iteration = iq.first()
        if latest_iteration:
            latest_iteration_id = latest_iteration.id
        else: 
            latest_iteration_id = 0
        iteration = request.args.get('iteration', latest_iteration_id, type=int)
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
            q = q.filter(MonitoringStation.id == station)
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
        csv = request.args.get('csv', type=int)
        if csv:
          q = q.join(Label).with_entities(MonitoringStation.name.label('station'), AudioFile.timestamp, ModelOutput.offset, ModelOutput.duration, Label.name.label('label'), ModelOutput.probability).all()
          column_names = ['station', 'timestamp', 'offset', 'duration', 'label', 'probability']
          return excel.make_response_from_query_sets(q, column_names, 'csv', file_name='predictions.csv') 
        predictions = q.paginate(page, per_page, False)
        output_schema = ModelOutputSchema(many=True)
        clips_json = output_schema.dumps(predictions.items)
        project = Project.query.get(project_id)
        return render_template('ml/output_list.html', title='Machine Learning Output', predictions=predictions, clips_json=clips_json, project=project)
    # permission denied
    abort(403)


@bp.route('/project/<project_id>/models')
@login_required
def list_models(project_id):
    permission = ManageLabelsPermission(project_id)
    if permission.can():
        page = request.args.get('page', 1, type=int)
        project = Project.query.get(project_id)
        q = project.models
        models = q.paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
        return render_template('ml/model_list.html', title='Machine Learning Models', models=models, project=project)
    # permission denied
    abort(403)


@bp.route('/project/<project_id>/new_model', methods=['GET', 'POST'])
@login_required
def new_model(project_id):
    permission = ManageLabelsPermission(project_id)
    if permission.can():
        form = EditModelForm()
        if form.validate_on_submit():
            model = MLModel()
            model.project_id = project_id
            model.name = form.name.data
            model.description = form.description.data
            db.session.add(model)
            db.session.commit()
            flash('New model created')
            return redirect(url_for('ml.list_models', project_id=project_id))
        project = Project.query.get(project_id)
        return render_template('ml/model_edit.html', title='New Model', form=form, project=project)
    # permission denied
    abort(403)


@bp.route('/model/<model_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_model(model_id):
    model = MLModel.query.get(model_id)
    permission = ManageLabelsPermission(model.project_id)
    if permission.can():
        form = EditModelForm()
        if form.validate_on_submit():
            model.name = form.name.data
            model.description = form.description.data
            db.session.add(model)
            db.session.commit()
            flash('Model updated')
            return redirect(url_for('ml.list_models', project_id=project_id))
        form.name.data = model.name
        form.description.data = model.description
        return render_template('ml/model_edit.html', title='Edit Model', form=form, model=model, project=model.project)
    # permission denied
    abort(403)


@bp.route('/model/<model_id>/iterations')
@login_required
def list_iterations(model_id):
    model = MLModel.query.get(model_id)
    permission = ManageLabelsPermission(model.project_id)
    if permission.can():
        page = request.args.get('page', 1, type=int)
        q = model.iterations.order_by(ModelIteration.updated.desc())
        iterations = q.paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
        return render_template('ml/iteration_list.html', title='Model Iterations', iterations=iterations, model=model, project=model.project)
    # permission denied
    abort(403)


@bp.route('/iteration/<iteration_id>')
@login_required
def view_iteration(iteration_id):
    iteration = ModelIteration.query.get(iteration_id)
    model = iteration.model
    permission = ManageLabelsPermission(model.project_id)
    if permission.can():
        page = request.args.get('page', 1, type=int)
        q = ModelLabel.query.filter(ModelLabel.iteration_id == iteration_id).join(Label, ModelLabel.label_id == Label.id).join(LabelType).filter(LabelType.parent_type == None).order_by(Label.name)
        labels = q.paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
        delete_form = DeleteForm()
        previous_status = iteration.previous_status()
        if previous_status:
            previous_form = PreviousForm()
            previous_form.previous_button.label.text = '\u00AB ' + str(previous_status)
        else:
            previous_form = None
        next_status = iteration.next_status()
        if next_status:
            next_form = NextForm()
            next_form.next_button.label.text = str(next_status) + ' \u00BB'
        else:
            next_form = None
        finished = (iteration.status == StatusEnum.finished)
        return render_template('ml/iteration_view.html', title='Model Iteration Labels', labels=labels, iteration=iteration, model=model, project=model.project, finished=finished, delete_form=delete_form, previous_form=previous_form, next_form=next_form)
    # permission denied
    abort(403)


@bp.route('/training_errors/<model_label_id>')
@login_required
def view_errors(model_label_id):
    model_label = ModelLabel.query.get(model_label_id)
    iteration = model_label.iteration
    model = iteration.model
    permission = ManageLabelsPermission(model.project_id)
    if permission.can():
        page = request.args.get('page', 1, type=int)
        errors = model_label.training_errors.paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
        return render_template('ml/training_errors.html', title='Training Errors', errors=errors, model_label=model_label, iteration=iteration, model=model, project=model.project)


@bp.route('/iteration/<iteration_id>/add_label')
@login_required
def add_label(iteration_id):
    iteration = ModelIteration.query.get(iteration_id)
    model = iteration.model
    permission = ManageLabelsPermission(model.project_id)
    if permission.can():
        project = model.project
        page = request.args.get('page', 1, type=int)
        subq = ModelLabel.query.filter(ModelLabel.iteration_id == iteration_id).with_entities(ModelLabel.label_id).subquery()
        q = ProjectLabel.query.filter(ProjectLabel.project == project).join(Label).join(LabelType).filter(LabelType.parent_type == None).filter(ProjectLabel.label_id.notin_(subq))
        labels = q.paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
        return render_template('ml/unused_labels.html', title='Unused Labels', labels=labels, iteration=iteration, model=model, project=project)
    # permission denied
    abort(403)


@bp.route('/iteration/<iteration_id>/label/<label_id>', methods=['GET', 'POST'])
@login_required
def edit_label(iteration_id, label_id):
    iteration = ModelIteration.query.get(iteration_id)
    model = iteration.model
    permission = ManageLabelsPermission(model.project_id)
    if permission.can() and iteration.status == StatusEnum.labeling:
        model_label = ModelLabel.query.filter(ModelLabel.label_id == label_id).filter(ModelLabel.iteration_id == iteration_id).first()
        if model_label:
            combine_with = model_label.combine_with
        else:
            combine_with = None
        form = IterationLabelForm(combine_with=combine_with)
        form.combine_with.query = Label.query.join(ModelLabel, Label.id == ModelLabel.label_id).filter(ModelLabel.iteration_id == iteration_id).filter(ModelLabel.label_id != label_id).order_by(Label.name)
        label = Label.query.get(label_id)
        if form.validate_on_submit():
            if model_label == None:
                model_label = ModelLabel(iteration=iteration, label=label)
                change = 'Added'
            else:
                change = 'Updated'
            model_label.combine_with = form.combine_with.data
            iteration.updated = datetime.utcnow()
            db.session.add(model_label)
            db.session.add(iteration)
            db.session.commit()
            flash(change + ' ' + label.name)
            return redirect(url_for('ml.iteration_clips', iteration_id=iteration_id, select_label=label_id))
        return render_template('ml/label_edit.html', title='Add/Edit Label', form=form, iteration=iteration, model=model, project=model.project, label=label)
    # permission denied
    abort(403)


@bp.route('/iteration/<iteration_id>/label/<label_id>/delete', methods=['POST'])
@login_required
def delete_label(iteration_id, label_id):
    iteration = ModelIteration.query.get(iteration_id)
    permission = ManageLabelsPermission(iteration.model.project_id)
    if permission.can() and iteration.status == StatusEnum.labeling:
        model_label = ModelLabel.query.filter(ModelLabel.label_id == label_id).filter(ModelLabel.iteration_id == iteration_id).first()
        label = Label.query.get(label_id)
        iteration.updated = datetime.utcnow()
        db.session.delete(model_label)
        db.session.add(iteration)
        db.session.commit()
        flash('Removed ' + label.name)
        return redirect(url_for('ml.view_iteration', iteration_id=iteration_id))
    # permission denied
    abort(403)


@bp.route('/iteration/<iteration_id>/previous_status', methods=['POST'])
@login_required
def previous_status(iteration_id):
    iteration = ModelIteration.query.get(iteration_id)
    permission = ManageLabelsPermission(iteration.model.project_id)
    if permission.can():
        previous_status = iteration.previous_status()
        if next_status:
            iteration.status = previous_status
            iteration.updated = datetime.utcnow()
            db.session.add(iteration)
            db.session.commit()
            flash('Updated status')
        else:
            flash('Invalid status change')
        return redirect(url_for('ml.view_iteration', iteration_id=iteration_id))
    # permission denied
    abort(403)


@bp.route('/iteration/<iteration_id>/next_status', methods=['POST'])
@login_required
def next_status(iteration_id):
    iteration = ModelIteration.query.get(iteration_id)
    permission = ManageLabelsPermission(iteration.model.project_id)
    if permission.can():
        next_status = iteration.next_status()
        if next_status:
            iteration.status = next_status
            iteration.updated = datetime.utcnow()
            db.session.add(iteration)
            db.session.commit()
            flash('Updated status')
        else:
            flash('Invalid status change')
        return redirect(url_for('ml.view_iteration', iteration_id=iteration_id))
    # permission denied
    abort(403)


@bp.route('/iteration/<iteration_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_iteration(iteration_id):
    iteration = ModelIteration.query.get(iteration_id)
    model = iteration.model
    permission = ManageLabelsPermission(model.project_id)
    if permission.can():
        form = EditIterationForm()
        if form.validate_on_submit():
            iteration.description = form.notes.data
            iteration.updated = datetime.utcnow()
            db.session.add(iteration)
            db.session.commit()
            flash('Notes updated')
            return redirect(url_for('ml.view_iteration', iteration_id=iteration_id))
        form.notes.data = iteration.description
        return render_template('ml/iteration_edit.html', title='Edit Iteration', form=form, iteration=iteration, model=model, project=model.project)
    # permission denied
    abort(403)


@bp.route('/model/<model_id>/new_iteration', methods=['GET', 'POST'])
@login_required
def new_iteration(model_id):
    model = MLModel.query.get(model_id)
    permission = ManageLabelsPermission(model.project_id)
    if permission.can():
        form = EditIterationForm()
        if form.validate_on_submit():
            iteration = ModelIteration()
            iteration.model = model
            iteration.description = form.notes.data
            db.session.add(iteration)
            db.session.commit()
            flash('New iteration created')
            return redirect(url_for('ml.view_iteration', iteration_id=iteration.id))
        return render_template('ml/iteration_new.html', title='New Iteration', form=form, model=model, project=model.project)
    # permission denied
    abort(403)


@bp.route('/iteration/<iteration_id>/copy', methods=['GET', 'POST'])
@login_required
def copy_iteration(iteration_id):
    iteration = ModelIteration.query.get(iteration_id)
    model = iteration.model
    permission = ManageLabelsPermission(model.project_id)
    if permission.can():
        form = EditIterationForm()
        if form.validate_on_submit():
            new_iteration = ModelIteration()
            new_iteration.model = iteration.model
            new_iteration.description = form.notes.data
            db.session.add(new_iteration)
            labels = ModelLabel.query.filter(ModelLabel.iteration_id == iteration_id).all()
            for label in labels:
                new_label = ModelLabel()
                new_label.iteration = new_iteration
                new_label.label = label.label
                new_label.combine_with = label.combine_with
                db.session.add(new_label)
            db.session.commit()
            flash('New iteration created')
            return redirect(url_for('ml.view_iteration', iteration_id=new_iteration.id))
        form.notes.data = iteration.description
        return render_template('ml/iteration_copy.html', title='Copy Iteration', form=form, iteration=iteration, model=model, project=model.project)
    # permission denied
    abort(403)


@bp.route('/iteration/<iteration_id>/clips', methods=['GET', 'POST'])
@login_required
def iteration_clips(iteration_id):
    iteration = ModelIteration.query.get(iteration_id)
    project = iteration.model.project
    q = LabeledClip.query.join(AudioFile).join(AudioFile.monitoring_station).filter(MonitoringStation.project == project)
    filter_form = FilterForm(request.args, meta={'csrf': False})
    fq = Label.query.join(ModelLabel, Label.id == ModelLabel.label_id).filter(ModelLabel.iteration == iteration).order_by(Label.name)
    filter_form.select_label.query = fq
    if filter_form.validate():
        if filter_form.select_label.data:
            q = q.filter(LabeledClip.label == filter_form.select_label.data)
        if filter_form.certain.data:
            q = q.filter(LabeledClip.certain == filter_form.certain.data)
    permission = ManageLabelsPermission(project.id)
    labeling = (iteration.status == StatusEnum.labeling)
    use_form = UseTrainingClipsForm()
    if permission.can() and labeling and use_form.validate_on_submit():
        training_clips_q = TrainingClip.query.join(LabeledClip).filter(TrainingClip.iteration_id == iteration.id)
        if use_form.use.data:
            selected_clips = q.filter(LabeledClip.id.notin_(training_clips_q.with_entities(LabeledClip.id))).all()
            for clip in selected_clips:
                training_clip = TrainingClip(iteration_id=iteration.id, labeled_clip_id=clip.id)
                db.session.add(training_clip)
            flash('Using {n} clips for training'.format(n=len(selected_clips)))
        if use_form.do_not_use.data:
            selected_clips = training_clips_q.filter(LabeledClip.id.in_(q.with_entities(LabeledClip.id))).all()
            for training_clip in selected_clips:
                db.session.delete(training_clip)
            flash('Stopped using {n} clips for training'.format(n=len(selected_clips)))
        db.session.commit()
        return redirect(url_for('ml.view_iteration', iteration_id=iteration_id))
    clips_count = q.count()
    page = request.args.get('page', 1, type=int)
    per_page = filter_form.per_page.data or current_app.config['ITEMS_PER_PAGE']
    clips = q.paginate(page, per_page, False)
    return render_template('ml/iteration_clips.html', title='Labeled Clips', filter_form=filter_form, use_form=use_form, clips_count=clips_count, clips=clips, iteration=iteration, model=iteration.model, project=project, labeling=labeling)


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
    q = ModelIteration.query.filter(ModelIteration.model_id == model_id).filter(ModelIteration.status == StatusEnum.finished)
    results = q.order_by(ModelIteration.updated.desc()).all()
    iterations = [{'id': r.id, 'updated': r.updated} for r in results]
    return jsonify(iterations)


@bp.route('/_get_model_labels/<iteration_id>')
def _get_model_labels(iteration_id):
    q = ModelLabel.query.join(Label, ModelLabel.label_id == Label.id).filter(ModelLabel.iteration_id == iteration_id)
    results = q.order_by(Label.name).all()
    labels = [{'id': r.label.id, 'name': r.label.name} for r in results]
    return jsonify(labels)


@bp.route('/iteration/<iteration_id>/_use_clip/<clip_id>', methods=['GET', 'POST'])
def _use_clip(iteration_id, clip_id):
    q = TrainingClip.query.filter(TrainingClip.iteration_id == iteration_id).filter(TrainingClip.labeled_clip_id == clip_id)
    training_clip = q.first()
    is_used = (training_clip is not None)
    if request.method == 'POST':
        iteration = ModelIteration.query.get(iteration_id)
        project_id = iteration.model.project_id
        permission = ManageLabelsPermission(project_id)
        if permission.can() and iteration.status == StatusEnum.labeling:
            use = request.get_json()
            if use == True and is_used == False:
                training_clip = TrainingClip(iteration_id=iteration_id, labeled_clip_id=clip_id)
                db.session.add(training_clip)
                is_used = True
            elif use == False and is_used == True:
                db.session.delete(training_clip)
                is_used = False
            db.session.commit()
    return jsonify(is_used)
