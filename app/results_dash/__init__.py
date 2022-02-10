from flask import Blueprint

bp = Blueprint('results_dash', __name__, template_folder='templates')

from app.results_dash import routes
