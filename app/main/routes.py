from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from app.main import bp


@bp.route('/')
def index():
    return render_template('index.html')


@bp.app_errorhandler(403)
def access_denied(e):
    return render_template('access_denied.html', error=e)
