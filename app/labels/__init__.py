from flask import Blueprint

bp = Blueprint('labels', __name__, static_folder='static')

from app.labels import routes
