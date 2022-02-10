from flask import Blueprint

bp = Blueprint('ml', __name__, template_folder='templates', static_folder='static')

from app.ml import routes
