from flask_login import current_user
from flask_principal import RoleNeed, UserNeed, Permission


admin_permission = Permission(RoleNeed('admin'))


def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # If the user account has the admin flag, make them a global admin
    if hasattr(current_user, 'admin'):
        if current_user.admin:
            identity.provides.add(RoleNeed('admin'))

