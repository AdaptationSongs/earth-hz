from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from app.user.roles import admin_permission
from app.results_dash import bp


@bp.route('/project/<project_id>')
@login_required
@admin_permission.require(http_exception=403)
def dashboard(project_id):
    return render_template('results_dash/dashboard.html', title='Visualize Results', project_id=project_id)


