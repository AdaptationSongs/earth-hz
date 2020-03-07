from flask import Blueprint

bp = Blueprint('audio', __name__)

from app.audio import routes
