from flask import Blueprint

bp = Blueprint('labels', __name__)

from app.labels import routes
