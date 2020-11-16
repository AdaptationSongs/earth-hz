from flask import render_template, abort
from flask_login import current_user, login_required
from app.user.roles import ViewResultsPermission
from app.results_dash import bp


@bp.route('/project/<project_id>')
@login_required
def dashboard(project_id):
    permission = ViewResultsPermission(project_id)
    if permission.can():
        return render_template('results_dash/dashboard.html', title='Visualize Results', project_id=project_id)
    # permission denied
    abort(403)

