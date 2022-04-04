from flask import render_template, abort
from flask_login import current_user, login_required
from app.models import Project
from app.user.permissions import ViewResultsPermission
from app.results_dash import bp


@bp.route('/project/<project_id>')
@login_required
def dashboard(project_id):
    permission = ViewResultsPermission(project_id)
    if permission.can():
        project = Project.query.get(project_id)
        return render_template('results_dash/dashboard.html', title='Visualize Results', project=project)
    # permission denied
    abort(403)

