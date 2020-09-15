from flask import Blueprint

bp = Blueprint('results_dash', __name__)

from app.results_dash import routes
