from flask_login import current_user
from flask_principal import RoleNeed, UserNeed, ItemNeed
from app import login
from app.models import User


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


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

    # Get all project roles
    # If not assigned to a project, treat it as a global role
    if hasattr(current_user, 'projects'):
        for project in current_user.projects:
            if project.project_coordinator:
                if project.project_id is None:
                    identity.provides.add(RoleNeed('project_coordinator'))
                else:
                    identity.provides.add(ItemNeed('project_coordinator', project.project_id, 'project_role'))
            if project.data_labeler:
                if project.project_id is None:
                    identity.provides.add(RoleNeed('data_labeler'))
                else:
                    identity.provides.add(ItemNeed('data_labeler', project.project_id, 'project_role'))
            if project.data_scientist:
                if project.project_id is None:
                    identity.provides.add(RoleNeed('data_scientist'))
                else:
                    identity.provides.add(ItemNeed('data_scientist', project.project_id, 'project_role'))

