from flask import Blueprint

bp = Blueprint('projects', __name__, template_folder='templates')

from app.projects import routes
