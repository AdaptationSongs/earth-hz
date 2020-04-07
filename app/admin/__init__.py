from flask import Blueprint

bp = Blueprint('admin_views', __name__)

from app.admin import views
