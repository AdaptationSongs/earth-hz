from flask import render_template, abort, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from app import db
from app.models import User, AudioFile, Cluster, ClusterGroup, Project
from app.schema import ClusterSchema
from app.user.permissions import ViewResultsPermission, UploadDataPermission
from app.clusters import bp
from app.clusters.forms import FilterForm, DeleteForm
from app.clusters.forms import UploadForm
import pandas as pd


@bp.route('/clusters/project/<project_id>')
@login_required
def cluster_groups(project_id):
    permission = ViewResultsPermission(project_id)
    if permission.can():
        delete_form = DeleteForm()
        page = request.args.get('page', 1, type=int)
        q = ClusterGroup.query.filter(ClusterGroup.project_id == project_id)
        groups = q.order_by(ClusterGroup.name).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
        project = Project.query.get(project_id)
        return render_template('clusters/cluster_groups.html', title='All cluster groups', groups=groups, project=project, delete_form=delete_form)
    # permission denied
    abort(403)

@bp.route('/clusters/<group_id>')
@login_required
def list_clusters(group_id):
    group = ClusterGroup.query.get(group_id)
    permission = ViewResultsPermission(group.project_id)
    if permission.can():
        page = request.args.get('page', 1, type=int)
        filter_form = FilterForm(request.args, meta={'csrf': False})
        filter_form.select_label.query = Cluster.query.filter_by(cg_id=group_id).distinct(Cluster.label)
        q = Cluster.query.filter(Cluster.cg_id == group_id)
        if filter_form.validate():
            if filter_form.select_label.data:
                q = q.filter(Cluster.label == filter_form.select_label.data.label)
        clusters = q.distinct(Cluster.cluster_name).order_by(Cluster.cluster_name).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
        return render_template('clusters/cluster_list.html', title='Sound clusters in group', clusters=clusters, group=group, filter_form=filter_form)
    # permission denied
    abort(403)


@bp.route('/clusters/<group_id>/<cluster_name>')
@login_required
def view_cluster(group_id, cluster_name):
    group = ClusterGroup.query.get(group_id)
    permission = ViewResultsPermission(group.project_id)
    if permission.can():
        page = request.args.get('page', 1, type=int)
        filter_form = FilterForm(request.args)
        filter_form.select_label.query = Cluster.query.filter_by(cg_id=group_id, cluster_name=cluster_name).distinct(Cluster.label)
        q = Cluster.query.filter(Cluster.cg_id == group_id).filter(Cluster.cluster_name == cluster_name)
        if filter_form.validate():
            if filter_form.select_label.data:
                q = q.filter(Cluster.label == filter_form.select_label.data.label)
        clips = q.join(AudioFile).order_by(AudioFile.timestamp).order_by(Cluster.start).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
        cluster_schema = ClusterSchema(many=True)
        clips_json = cluster_schema.dumps(clips.items)
        return render_template('clusters/cluster_view.html', title='Selections in sound cluster', clips=clips, clips_json=clips_json, group=group, cluster_name=cluster_name, filter_form=filter_form)
    # permission denied
    abort(403)


@bp.route('/clusters/project/<project_id>/upload', methods=['GET', 'POST'])
@login_required
def upload(project_id):
    permission = UploadDataPermission(project_id)
    if permission.can():
        current_project = Project.query.get(project_id)
        form = UploadForm()
        if form.validate_on_submit():
            f = form.upload.data
            cluster_df = pd.read_csv(f)
            cluster_df.columns = cluster_df.columns.str.replace('*', '')
            import_df = cluster_df[['IN FILE', 'OFFSET', 'DURATION', 'TOP1MATCH', 'MANUAL ID']]
            cg = ClusterGroup(name=form.cluster_name.data, user=current_user, project=current_project)
            db.session.add(cg)
            db.session.commit()
            import_df['cg_id'] = cg.id
            import_df.to_sql('clusters', con=db.engine, index=False, if_exists='append')
            return redirect(url_for('clusters.cluster_groups', project_id=project_id))
        return render_template('clusters/upload.html', title="Upload cluster file", form=form, project_id=project_id)
    # permission denied
    abort(403)


@bp.route('/clusters/<group_id>/delete', methods=['POST'])
@login_required
def delete_clusters(group_id):
    group = ClusterGroup.query.get(group_id)
    permission = UploadDataPermission(group.project_id)
    if permission.can() or (group.user == current_user):
        db.session.delete(group)
        db.session.commit()
        flash('Cluster group deleted.')
        return redirect(url_for('clusters.cluster_groups', project_id=group.project_id))
    # permission denied
    abort(403)
