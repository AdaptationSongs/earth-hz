from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from app import db
from app.models import User, AudioFile, Label, LabelType, LabeledClip
from app.user.roles import admin_permission
from app.labels import bp
from app.labels.forms import FilterLabelsForm, EditLabelForm, DeleteLabelForm
from datetime import datetime


@bp.route('/labels', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def list_labels():
    page = request.args.get('page', 1, type=int)
    filter_form = FilterLabelsForm()
    filter_form.select_label.query = Label.query
    if request.method == 'POST':
        selected_label = filter_form.select_label.data
    else:
        selected_label = request.args.get('label', type=int)
    if selected_label:
        clips = LabeledClip.query.filter_by(label=selected_label).join(LabeledClip.file).order_by(AudioFile.timestamp).order_by(LabeledClip.offset).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
    else:
        clips = LabeledClip.query.join(LabeledClip.file).order_by(AudioFile.timestamp).order_by(LabeledClip.offset).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)

    filters = {'label': selected_label}
    return render_template('labels/label_list.html', title='Labels', clips=clips, filter_form=filter_form, filters=filters)


@bp.route('/clip/<file_name>/<offset>', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def view_clip(file_name, offset):
    delete_form = DeleteLabelForm()
    form = EditLabelForm()
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
