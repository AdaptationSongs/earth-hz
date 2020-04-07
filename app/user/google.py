from flask import flash, request, session, redirect, url_for, current_app
from flask_login import login_user, current_user
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer import oauth_before_login, oauth_authorized, oauth_error
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_principal import Identity, AnonymousIdentity, identity_changed
from sqlalchemy.orm.exc import NoResultFound
from app import db
from app.models import User, OAuth

bp = make_google_blueprint(
    scope=['profile', 'email'],
    storage=SQLAlchemyStorage(OAuth, db.session, user=current_user),
)


# save next url for redirect
@oauth_before_login.connect_via(bp)
def before_login(blueprint, url):
    session['next_url'] = request.args.get('next')


# create/login local user on successful OAuth login
@oauth_authorized.connect_via(bp)
def google_logged_in(bp, token):
    if not token:
        flash('Failed to log in.', category='error')
        return False

    resp = bp.session.get('/oauth2/v1/userinfo')
    if not resp.ok:
        msg = 'Failed to fetch user info.'
        flash(msg, category='error')
        return False

    info = resp.json()
    user_id = info['id']

    # Find this OAuth token in the database, or create it
    query = OAuth.query.filter_by(provider=bp.name, provider_user_id=user_id)
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(provider=bp.name, provider_user_id=user_id, token=token)

    if oauth.user:
        user = oauth.user
    else:
        # check for existing user with this email
        user = User.query.filter_by(email=info['email']).first()
        if user is None: 
            # Create a new local user account for this user
            user = User()
            user.email = info['email']
            user.name = info['name']
            user.avatar = info['picture']
            db.session.add(user)
        # Associate the new local user account with the OAuth token
        oauth.user = user
        # Save and commit our database models
        db.session.add(oauth)
        db.session.commit()

    # Log in the local user account
    login_user(user)

    # Tell Flask-Principal the identity changed
    identity_changed.send(current_app._get_current_object(),
                          identity=Identity(user.id))

    flash('Successfully signed in.')

    # retrieve `next_url` from Flask's session cookie
    next_url = session['next_url'] or url_for('main.index')
    return redirect(next_url)


# notify on OAuth provider error
@oauth_error.connect_via(bp)
def google_error(bp, message, response):
    msg = ('OAuth error from {name}! ' 'message={message} response={response}').format(
        name=bp.name, message=message, response=response
    )
    flash(msg, category='error')

