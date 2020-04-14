from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from app import db
from app.models import User, AudioFile, Label, LabelType, LabeledClip, Equipment, MonitoringStation, Project, ProjectLabel
from app.user.roles import admin_permission
from app.labels import bp
from app.labels.forms import FilterForm, EditForm, DeleteForm
from datetime import datetime


@bp.route('/labels')
@bp.route('/labels/project/<project_id>')
@login_required
@admin_permission.require(http_exception=403)
def list_labels(project_id=None):
    page = request.args.get('page', 1, type=int)
    filter_form = FilterForm(request.args)
    fq = Label.query
    q = LabeledClip.query.join(AudioFile)
    if project_id:
        q = q.join(Equipment, AudioFile.sn == Equipment.serial_number).join(MonitoringStation).filter(MonitoringStation.project_id == project_id)
        fq = fq.join(ProjectLabel, Label.id == ProjectLabel.label_id).filter(ProjectLabel.project_id == project_id)
    filter_form.select_label.query = fq
    if filter_form.validate():
        if filter_form.select_label.data:
            q = q.join(Label).filter(Label.id == filter_form.select_label.data.id)
    clips = q.order_by(AudioFile.timestamp).order_by(LabeledClip.offset).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
    return render_template('labels/label_list.html', title='Labels', clips=clips, filter_form=filter_form)


@bp.route('/clip/<file_name>/<offset>', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def view_clip(file_name, offset):
    delete_form = DeleteForm()
    form = EditForm()
    form.select_label.query = Label.query
    if form.validate_on_submit():
        label = LabeledClip(file_name=file_name, offset=offset, label=form.select_label.data, notes=form.notes.data, user=current_user, modified=datetime.utcnow())
        db.session.add(label)
        db.session.commit()
        return redirect(url_for('labels.view_clip', file_name=file_name, offset=offset))
    labels = LabeledClip.query.filter_by(file_name=file_name, offset=offset).order_by(LabeledClip.modified.desc()).all()
    return render_template('labels/view_clip.html',  title='Add/edit labels', delete_form=delete_form, form=form, labels=labels, file_name=file_name, offset=offset)


@bp.route('/clip/<file_name>/<offset>/delete/<label_id>', methods=['POST'])
@login_required
def delete_clip_label(file_name, offset, label_id):
    clip_label = LabeledClip.query.get(label_id)
    if (clip_label.user == current_user):
        db.session.delete(clip_label)
        db.session.commit()
        flash('Label deleted.')
    return redirect(url_for('labels.view_clip', file_name=file_name, offset=offset))
