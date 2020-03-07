from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from app import db
from app.models import User, AudioFile, Cluster, ClusterGroup
from app.clusters import bp
from app.clusters.forms import FilterClustersForm, DeleteForm
from app.clusters.forms import UploadForm
import pandas as pd


@bp.route('/clusters')
@login_required
def cluster_groups():
    delete_form = DeleteForm()
    page = request.args.get('page', 1, type=int)
    groups = ClusterGroup.query.order_by(ClusterGroup.name).paginate(
            page, current_app.config['ITEMS_PER_PAGE'], False)
    return render_template('clusters/cluster_groups.html', title='All cluster groups', groups=groups, delete_form=delete_form)


@bp.route('/clusters/<group_id>', methods=['GET', 'POST'])
@login_required
def list_clusters(group_id):
    page = request.args.get('page', 1, type=int)
    filter_form = FilterClustersForm()
    filter_form.select_label.query = Cluster.query.filter_by(cg_id=group_id).distinct(Cluster.label)
    if filter_form.validate_on_submit():
        selected_label = filter_form.select_label.data.label
    else:
        selected_label = request.args.get('label', type=str)
    if selected_label:
        clusters = Cluster.query.filter_by(cg_id=group_id, label=selected_label).distinct(Cluster.cluster_name).order_by(Cluster.cluster_name).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
    else:
        clusters = Cluster.query.filter_by(cg_id=group_id).distinct(Cluster.cluster_name).order_by(Cluster.cluster_name).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)

    filters = {'label': selected_label}
    return render_template('clusters/cluster_list.html', title='Sound clusters in group', clusters=clusters, filter_form=filter_form, filters=filters)


@bp.route('/clusters/<group_id>/<cluster_name>', methods=['GET', 'POST'])
@login_required
def view_cluster(group_id, cluster_name):
    page = request.args.get('page', 1, type=int)
    filter_form = FilterClustersForm()
    filter_form.select_label.query = Cluster.query.filter_by(cg_id=group_id, cluster_name=cluster_name).distinct(Cluster.label)
    if filter_form.validate_on_submit():
        selected_label = filter_form.select_label.data.label
    else:
        selected_label = request.args.get('label', type=str)
    if selected_label:
        clusters = Cluster.query.filter_by(cg_id=group_id, cluster_name=cluster_name, label=selected_label).join(Cluster.file).order_by(AudioFile.timestamp).order_by(Cluster.start).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)
    else:
        clusters = Cluster.query.filter_by(cg_id=group_id, cluster_name=cluster_name).join(Cluster.file).order_by(AudioFile.timestamp).order_by(Cluster.start).paginate(page, current_app.config['ITEMS_PER_PAGE'], False)

    filters = {'label': selected_label}
    return render_template('clusters/cluster_view.html', title='Selections in sound cluster', clusters=clusters, filter_form=filter_form, filters=filters)


@bp.route('/clusters/upload', methods=['GET', 'POST'])
@login_required
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
def delete_clusters(group_id):
    group = ClusterGroup.query.get(group_id)
    if (group.user == current_user):
        db.session.delete(group)
        db.session.commit()
        flash('Cluster group deleted.')
    return redirect(url_for('clusters.cluster_groups'))
