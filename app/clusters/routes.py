from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from app import db
from app.models import User, AudioFile, Cluster, ClusterGroup, Project
from app.user.roles import admin_permission
from app.clusters import bp
from app.clusters.forms import FilterForm, DeleteForm
from app.clusters.forms import UploadForm
import pandas as pd


@bp.route('/clusters')
@bp.route('/clusters/project/<project_id>')
@login_required
@admin_permission.require(http_exception=403)
def cluster_groups(project_id=None):
    delete_form = DeleteForm()
    page = request.args.get('page', 1, type=int)
    q = ClusterGroup.query
    if project_id:
        q = q.join(Project).filter(Project.id == project_id)
    groups = q.order_by(ClusterGroup.name).paginate(
            page, current_app.config['ITEMS_PER_PAGE'], False)
    return render_template('clusters/cluster_groups.html', title='All cluster groups', groups=groups, delete_form=delete_form)


@bp.route('/clusters/<group_id>')
@login_required
@admin_permission.require(http_exception=403)
def list_clusters(group_id):
    page = request.args.get('page', 1, type=int)
    filter_form = FilterForm(request.args)
    filter_form.select_label.query = Cluster.query.filter_by(cg_id=group_id).distinct(Cluster.label)
    q = Cluster.query.filter(Cluster.cg_id == group_id)
    if filter_form.validate():
        if filter_form.select_label.data:
            q = q.filter(Cluster.label == filter_form.select_label.data.label)
    clusters = q.distinct(Cluster.cluster_name).order_by(Cluster.cluster_name).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
    return render_template('clusters/cluster_list.html', title='Sound clusters in group', clusters=clusters, filter_form=filter_form)


@bp.route('/clusters/<group_id>/<cluster_name>')
@login_required
@admin_permission.require(http_exception=403)
def view_cluster(group_id, cluster_name):
    page = request.args.get('page', 1, type=int)
    filter_form = FilterForm(request.args)
    filter_form.select_label.query = Cluster.query.filter_by(cg_id=group_id, cluster_name=cluster_name).distinct(Cluster.label)
    q = Cluster.query.filter(Cluster.cg_id == group_id).filter(Cluster.cluster_name == cluster_name)
    if filter_form.validate():
        if filter_form.select_label.data:
            q = q.filter(Cluster.label == filter_form.select_label.data.label)
    clusters = q.join(AudioFile).order_by(AudioFile.timestamp).order_by(Cluster.start).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
    return render_template('clusters/cluster_view.html', title='Selections in sound cluster', clusters=clusters, filter_form=filter_form)


@bp.route('/clusters/upload', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        f = form.upload.data
        cluster_df = pd.read_csv(f)
        cluster_df.columns = cluster_df.columns.str.replace('*', '')
        import_df = cluster_df[['IN FILE', 'OFFSET', 'DURATION', 'TOP1MATCH', 'MANUAL ID']]
        cg = ClusterGroup(name=form.cluster_name.data, user=current_user)
        db.session.add(cg)
        db.session.commit()
        import_df['cg_id'] = cg.id
        import_df.to_sql('clusters', con=db.engine, index=False, if_exists='append')
        return redirect(url_for('clusters.cluster_groups'))
    return render_template('clusters/upload.html', title="Upload cluster file", form=form)


@bp.route('/clusters/<group_id>/delete', methods=['POST'])
@login_required
@admin_permission.require(http_exception=403)
def delete_clusters(group_id):
    group = ClusterGroup.query.get(group_id)
    if (group.user == current_user):
        db.session.delete(group)
        db.session.commit()
        flash('Cluster group deleted.')
    return redirect(url_for('clusters.cluster_groups'))
