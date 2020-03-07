from flask import render_template, redirect, url_for, flash, request, session, current_app
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
#from flask_babel import _
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError
from app import db
from app.auth import bp
#from app.auth.forms import LoginForm, RegistrationForm, \
#    ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
#from app.auth.email import send_password_reset_email
import json

# OAuth Session creation
def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(current_app.config['CLIENT_ID'], token=token)
    if state:
        return OAuth2Session(
            current_app.config['CLIENT_ID'],
            state=state,
            redirect_uri=current_app.config['REDIRECT_URI'])
    oauth = OAuth2Session(
        current_app.config['CLIENT_ID'],
        redirect_uri=current_app.config['REDIRECT_URI'],
        scope=current_app.config['SCOPE'])
    return oauth

@bp.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        current_app.config['AUTH_URI'], access_type='offline')
    session['oauth_state'] = state
    return render_template('auth/login.html', auth_url=auth_url)

@bp.route('/login/callback')
def callback():
    # Redirect user to home page if already logged in.
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('index'))
    if 'error' in request.args:
        if request.args.get('error') == 'access_denied':
            return 'Access Denied.'
        return 'Error encountered.'
    if 'code' not in request.args and 'state' not in request.args:
        return redirect(url_for('login'))
    else:
        # Execution reaches here when user has
        # successfully authenticated our app.
        google = get_google_auth(state=session['oauth_state'])
        try:
            print(request.url)
            token = google.fetch_token(
                current_app.config['TOKEN_URI'],
                client_secret=current_app.config['CLIENT_SECRET'],
                authorization_response=request.url)
        except HTTPError:
            return 'HTTPError occurred.'
        google = get_google_auth(token=token)
        resp = google.get(current_app.config['USER_INFO'])
        if resp.status_code == 200:
            user_data = resp.json()
            email = user_data['email']
            user = User.query.filter_by(email=email).first()
            if user is None:
                user = User()
                user.email = email
            user.name = user_data['name']
            print(token)
            user.tokens = json.dumps(token)
            user.avatar = user_data['picture']
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('main.index'))
        return 'Could not fetch your information.'

@bp.route('/logout')
#@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

