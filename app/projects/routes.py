from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
from app import db
from app.models import Project
from app.user.roles import admin_permission
from app.projects import bp


@bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    projects = Project.query.paginate(
            page, current_app.config['ITEMS_PER_PAGE'], False)
    return render_template('projects/project_list.html', title='All Projects', projects=projects)


