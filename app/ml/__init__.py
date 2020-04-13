from flask import Blueprint

bp = Blueprint('ml', __name__)

from app.ml import routes
