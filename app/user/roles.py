from collections import namedtuple
from functools import partial
from flask_login import current_user
from flask_principal import RoleNeed, UserNeed, ItemNeed, Permission
from app import login
from app.models import User

admin_need = RoleNeed('admin')
admin_permission = Permission(admin_need)


class AddLabelPermission(Permission):
    def __init__(self, project_id):
        coordinator_need = ItemNeed('project_coordinator', int(project_id), 'project_role')
        labeler_need = ItemNeed('data_labeler', int(project_id), 'project_role')
        super(AddLabelPermission, self).__init__(admin_need, coordinator_need, labeler_need)


class ViewResultsPermission(Permission):
    def __init__(self, project_id):
        coordinator_need = ItemNeed('project_coordinator', int(project_id), 'project_role')
        labeler_need = ItemNeed('data_labeler', int(project_id), 'project_role')
        scientist_need = ItemNeed('data_scientist', int(project_id), 'project_role')
        super(ViewResultsPermission, self).__init__(admin_need, coordinator_need, labeler_need, scientist_need)


class UploadDataPermission(Permission):
    def __init__(self, project_id):
        coordinator_need = ItemNeed('project_coordinator', int(project_id), 'project_role')
        scientist_need = ItemNeed('data_scientist', int(project_id), 'project_role')
        super(UploadDataPermission, self).__init__(admin_need, coordinator_need, scientist_need)


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
    if hasattr(current_user, 'projects'):
        for project in current_user.projects:
            if project.project_coordinator:
                identity.provides.add(ItemNeed('project_coordinator', project.project_id, 'project_role'))
            if project.data_labeler:
                identity.provides.add(ItemNeed('data_labeler', project.project_id, 'project_role'))
            if project.data_scientist:
                identity.provides.add(ItemNeed('data_scientist', project.project_id, 'project_role'))

