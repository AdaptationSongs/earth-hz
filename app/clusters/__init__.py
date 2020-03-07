from flask import Blueprint

bp = Blueprint('clusters', __name__)

from app.clusters import routes
