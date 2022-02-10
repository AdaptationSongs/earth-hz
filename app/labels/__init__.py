from flask import Blueprint

bp = Blueprint('labels', __name__, template_folder='templates', static_folder='static')

from app.labels import routes
