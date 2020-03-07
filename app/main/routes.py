#from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response
from flask_login import current_user, login_required
#from flask_babel import _, get_locale
#from guess_language import guess_language
from app import db
#from app.main.forms import EditProfileForm, PostForm, SearchForm, MessageForm
from app.models import User, AudioFile, Cluster
#from app.translate import translate
from app.main import bp
import sys
import re


@bp.route('/')
def index():
    return render_template('index.html')

