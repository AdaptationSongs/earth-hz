from flask import Blueprint

bp = Blueprint('user_views', __name__)

from app.user import routes

