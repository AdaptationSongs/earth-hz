from flask import Blueprint

bp = Blueprint('clusters', __name__, template_folder='templates')

from app.clusters import routes
