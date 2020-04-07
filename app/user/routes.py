from flask import render_template, redirect, url_for, flash, session, current_app
from flask_login import logout_user, current_user, login_required
from flask_principal import Identity, AnonymousIdentity, identity_changed
from app.user import bp


@bp.route('/login')
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.')
        return redirect(url_for('main.index'))
    return render_template('user/login.html')


@bp.route('/logout')
@login_required
def logout():  
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
    flash('You are now logged out.')
    return redirect(url_for('main.index'))

