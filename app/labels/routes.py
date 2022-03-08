from flask import render_template, abort, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from app import db
from app.models import User, AudioFile, Label, LabelType, LabeledClip, Equipment, MonitoringStation, Project, ProjectLabel, CommonName
from app.schema import LabelTypeSchema, LabelSchema, LabeledClipSchema
from app.user.permissions import ViewResultsPermission, AddLabelPermission, UploadDataPermission, ManageLabelsPermission
from app.labels import bp
from app.labels.forms import FilterForm, EditForm, DeleteForm
from datetime import datetime
from sqlalchemy.orm import aliased
import flask_excel as excel

@bp.route('/')
@bp.route('/project/<project_id>')
@login_required
def list_labels(project_id=None):
    permission = ViewResultsPermission(project_id)
    if permission.can():
        page = request.args.get('page', 1, type=int)
        filter_form = FilterForm(request.args, meta={'csrf': False})
        fq = Label.query.join(LabelType).filter(LabelType.parent_id == None)
        q = LabeledClip.query.join(AudioFile).join(LabeledClip.label)
        view_restricted = ManageLabelsPermission(project_id)
        if not view_restricted.can():
            q = q.filter((Label.restricted == False) | (Label.restricted == None))
        if project_id:
            q = q.join(AudioFile.monitoring_station).filter(MonitoringStation.project_id == project_id)
            fq = fq.join(ProjectLabel, Label.id == ProjectLabel.label_id).filter(ProjectLabel.project_id == project_id)
        filter_form.select_label.query = fq
        if filter_form.validate():
            if filter_form.select_label.data:
                q = q.filter(Label.id == filter_form.select_label.data.id)
            if filter_form.certain.data == '1':
                q = q.filter(LabeledClip.certain == True)
            if filter_form.certain.data == '0':
                q = q.filter(LabeledClip.certain == False)
        clips = q.order_by(AudioFile.timestamp).order_by(LabeledClip.offset).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
        return render_template('labels/label_list.html', title='Labels', clips=clips, project_id=project_id, filter_form=filter_form)
    # permission denied
    abort(403)

@bp.route('/project/<project_id>/download-labels.csv')
@login_required
def export_csv(project_id):
    permission = UploadDataPermission(project_id)
    if permission.can():
        sub = aliased(Label)
        q = LabeledClip.query.join(LabeledClip.label).join(sub, LabeledClip.sub_label, isouter=True).join(User).join(AudioFile).join(AudioFile.monitoring_station).filter(MonitoringStation.project_id == project_id).with_entities(AudioFile.path, LabeledClip.file_name, LabeledClip.offset, Label.name.label('label'), sub.name.label('sub_label'), LabeledClip.certain, LabeledClip.notes, LabeledClip.modified, User.name.label('user')).all()
        column_names = ['path', 'file_name', 'offset', 'label', 'sub_label', 'certain', 'notes', 'modified', 'user']
        return excel.make_response_from_query_sets(q, column_names, 'csv')
    # permission denied
    abort(403)


@bp.route('/clip/<file_name>/<float:offset>', methods=['GET', 'POST'])
@bp.route('/clip/<file_name>/<int:offset>', methods=['GET', 'POST'])
@login_required
def view_clip(file_name, offset):
    delete_form = DeleteForm()
    form = EditForm()
    form.select_type.query = LabelType.query.filter(LabelType.parent_id == None)
    wav_file = AudioFile.query.filter_by(name=file_name).first()
    station = wav_file.recording_device.station
    project_id = station.project_id
    lq = Label.query.join(LabelType).join(ProjectLabel, Label.id == ProjectLabel.label_id).filter(ProjectLabel.project_id == project_id)
    form.select_label.query = lq.filter(LabelType.parent_id == None)
    form.select_sub_label.query = lq.filter(LabelType.parent_id != None)
    add_permission = AddLabelPermission(project_id)
    view_permission = ViewResultsPermission(project_id)
    if form.validate_on_submit():
        if add_permission.can():
            label = LabeledClip(file_name=file_name, offset=offset, duration=current_app.config['CLIP_SECS'], certain=form.certainty.data, label=form.select_label.data, sub_label=form.select_sub_label.data, notes=form.notes.data, user=current_user, modified=datetime.utcnow())
            db.session.add(label)
            db.session.commit()
            flash('Label added.')
            return redirect(url_for('labels.view_clip', file_name=file_name, offset=offset))
        # permission denied
        abort(403)
    if view_permission.can():
        admin_permission = ManageLabelsPermission(project_id)
        labels = LabeledClip.query.filter_by(file_name=file_name, offset=offset).order_by(LabeledClip.modified.desc()).all()
        return render_template('labels/view_clip.html',  title='Add/edit labels', delete_form=delete_form, form=form, labels=labels, wav_file=wav_file, offset=offset, station=station, admin=admin_permission.can())
    # permission denied
    abort(403)


@bp.route('/clip/<file_name>/<offset>/delete/<label_id>', methods=['POST'])
@login_required
def delete_clip_label(file_name, offset, label_id):
    clip_label = LabeledClip.query.get(label_id)
    project_id = clip_label.file.recording_device.station.project.id
    admin_permission = ManageLabelsPermission(project_id)
    if clip_label.user == current_user or admin_permission.can():
        db.session.delete(clip_label)
        db.session.commit()
        flash('Label deleted.')
    return redirect(url_for('labels.view_clip', file_name=file_name, offset=offset))


@bp.route('/_get_labels/<project_id>')
def _get_labels(project_id):
    type_id = request.args.get('type', type=int)
    q = Label.query.join(LabelType).join(ProjectLabel, Label.id == ProjectLabel.label_id).filter(ProjectLabel.project_id == project_id)
    label_query = q.filter(LabelType.id == type_id)
    labels = [{'id':row.id, 'label':row.name} for row in label_query.all()]
    sub_query = q.filter(LabelType.parent_id == type_id)
    sub_labels = [{'id':row.id, 'label':row.name} for row in sub_query.all()]
    sub_type = sub_query.first().type.name if sub_labels else None
    label_json = {'labels':labels, 'sub':{'type':sub_type, 'labels':sub_labels}}
    return jsonify(label_json)


@bp.route('/_get_label_types')
def _get_label_types():
    q = LabelType.query
    all_types = q.all()
    label_types_schema = LabelTypeSchema(many=True)
    return label_types_schema.jsonify(all_types)


@bp.route('/_get_all')
@bp.route('/_get_all/project/<project_id>')
def _get_all_labels(project_id=None):
    q = Label.query
    if project_id:
        q = q.join(ProjectLabel, ProjectLabel.label_id == Label.id).filter(ProjectLabel.project_id == project_id)
    sub = request.args.get('sub', type=int)
    if sub == 1:
        q = q.join(LabelType).filter(LabelType.parent_id != None)
    elif sub == 0:
        q = q.join(LabelType).filter(LabelType.parent_id == None)
    labels = q.order_by(Label.name).all()
    labels_schema = LabelSchema(many=True)
    return labels_schema.jsonify(labels)


@bp.route('/_get_clip_labels/<file_name>')
def _get_clip_labels(file_name):
    q = LabeledClip.query.filter(LabeledClip.file_name == file_name)
    offset = request.args.get('offset', type=float)
    if offset is not None:
        q = q.filter(LabeledClip.offset == offset)
    duration = request.args.get('duration', type=float)
    if duration:
        q = q.filter(LabeledClip.duration == duration)
    clip_labels = q.all()
    labeled_clips_schema = LabeledClipSchema(many=True)
    return labeled_clips_schema.jsonify(clip_labels)


@bp.route('/_add_clip_label', methods=['POST'])
def _add_clip_label():
    data = request.get_json()
    for clip in data['clips']:
        audio_file = AudioFile.query.filter(AudioFile.name == clip['file_name']).first()
        project_id = audio_file.recording_device.station.project_id
        permission = AddLabelPermission(project_id)
        if permission.can():
            clip.update(data['label'])
            clip['user_id'] = current_user.id
            q = LabeledClip.query.filter(LabeledClip.file_name == clip['file_name'], LabeledClip.offset == clip['offset'], LabeledClip.duration == clip['duration'], LabeledClip.label_id == clip['label_id'], LabeledClip.user_id == clip['user_id'])
            if clip['sub_label_id']:
                q = q.filter(LabeledClip.sub_label_id == clip['sub_label_id'])
            existing_label = q.first()
            if existing_label:
                return jsonify({'message': 'You have already added this label'}), 409
            labeled_clip_schema = LabeledClipSchema()
            new_label = labeled_clip_schema.load(clip)
            db.session.add(new_label)
        else:
            return jsonify({'message': 'Permission denied'}), 403
    db.session.commit()
    return labeled_clip_schema.jsonify(new_label)
