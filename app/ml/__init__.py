from flask import Blueprint

bp = Blueprint('ml', __name__, static_folder='static')

from app.ml import routes
