from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response, abort
from flask_login import current_user, login_required
from app import db
from sqlalchemy import func
from app.models import Project, AudioFile, Equipment, MonitoringStation, ProjectLabel, LabeledClip, Label, LabelType, MLModel, ModelIteration
from app.schema import ProjectLabelSchema
from app.user.permissions import ManageLabelsPermission
from app.projects import bp


@bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    projects = Project.query.paginate(
            page, current_app.config['ITEMS_PER_PAGE'], False)
    return render_template('projects/project_list.html', title='All Projects', projects=projects)


@bp.route('/<project_id>/overview')
@login_required
def overview(project_id):
    project = Project.query.get(project_id)
    project_labels = ProjectLabel.query.join(Label).join(LabelType).filter(ProjectLabel.project_id == project_id).filter(LabelType.parent_type == None).order_by(db.desc(ProjectLabel.clip_count)).limit(10).all()
    iteration_subq = db.session.query(ModelIteration.model_id, func.max(ModelIteration.updated).label('max_date')).group_by(ModelIteration.model_id).subquery()
    iterations = ModelIteration.query.join(MLModel).filter(MLModel.project_id == project_id).join(iteration_subq, (iteration_subq.c.model_id == ModelIteration.model_id) & (iteration_subq.c.max_date == ModelIteration.updated)).limit(10).all()
    return render_template('projects/overview.html', title='Projects Overview', project=project, project_labels=project_labels, iterations=iterations)


@bp.route('/<project_id>/labels')
@login_required
def list_labels(project_id):
    permission = ManageLabelsPermission(project_id)
    if permission.can():
        page = request.args.get('page', 1, type=int)
        project = Project.query.get(project_id)
        q = project.labels.join(Label).join(LabelType).filter(LabelType.parent_id == None).order_by(Label.name)
        labels = q.paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
        labels_schema = ProjectLabelSchema(many=True)
        labels_json = labels_schema.dumps(labels.items)
        return render_template('projects/label_list.html', title='Project Labels', labels=labels, labels_json=labels_json, project=project)
    # permission denied
    abort(403)


@bp.route('/<project_id>/sublabels')
@login_required
def list_sublabels(project_id):
    permission = ManageLabelsPermission(project_id)
    if permission.can():
        page = request.args.get('page', 1, type=int)
        project = Project.query.get(project_id)
        q = project.labels.join(Label).join(LabelType).filter(LabelType.parent_id != None).order_by(Label.name)
        labels = q.paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
        labels_schema = ProjectLabelSchema(many=True)
        labels_json = labels_schema.dumps(labels.items)
        return render_template('projects/sublabel_list.html', title='Project Sublabels', labels=labels, labels_json=labels_json, project=project)
    # permission denied
    abort(403)


@bp.route('/_get_monitoring_stations/<project_id>')
def _get_monitoring_stations(project_id):
    q = MonitoringStation.query.filter(MonitoringStation.project_id == project_id)
    results = q.all()
    stations = [{'id': r.id, 'name': r.name} for r in results]
    return jsonify(stations)


@bp.route('/_add_project_label', methods=['POST'])
def _add_project_label():
    data = request.get_json()
    project_id = data['project_id']
    permission = ManageLabelsPermission(project_id)
    if permission.can():
        q = ProjectLabel.query.filter(ProjectLabel.project_id == project_id).filter(ProjectLabel.label_id == data['label_id'])
        existing_label = q.first()
        if existing_label:
            return jsonify({'message': 'You have already added this label'}), 409
        project_label_schema = ProjectLabelSchema()
        new_label = project_label_schema.load(data)
        db.session.add(new_label)
        db.session.commit()
        return project_label_schema.jsonify(new_label)
    else:
        return jsonify({'message': 'Permission denied'}), 403


@bp.route('/_delete_project_label', methods=['POST'])
def _delete_project_label():
    data = request.get_json()
    project_label = ProjectLabel.query.get(data['id'])
    project_id = project_label.project_id
    permission = ManageLabelsPermission(project_id)
    if permission.can():
        db.session.delete(project_label)
        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify({'message': 'Permission denied'}), 403
