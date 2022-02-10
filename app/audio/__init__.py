from flask import Blueprint

bp = Blueprint('audio', __name__, template_folder='templates')

from app.audio import routes
