from flask_login import current_user
from flask_principal import RoleNeed, UserNeed, ItemNeed, Permission
from app.models import AudioFile, Equipment, MonitoringStation, LabeledClip, Label 

admin_permission = Permission(RoleNeed('admin'))


class AddLabelPermission(Permission):
    def __init__(self, project_id):
        coordinator_need = ItemNeed('project_coordinator', int(project_id), 'project_role')
        labeler_need = ItemNeed('data_labeler', int(project_id), 'project_role')
        super(AddLabelPermission, self).__init__(RoleNeed('admin'), RoleNeed('project_coordinator'), RoleNeed('data_labeler'), coordinator_need, labeler_need)


class ViewResultsPermission(Permission):
    def __init__(self, project_id):
        coordinator_need = ItemNeed('project_coordinator', int(project_id), 'project_role')
        labeler_need = ItemNeed('data_labeler', int(project_id), 'project_role')
        scientist_need = ItemNeed('data_scientist', int(project_id), 'project_role')
        super(ViewResultsPermission, self).__init__(RoleNeed('admin'), RoleNeed('project_coordinator'), RoleNeed('data_labeler'), RoleNeed('data_scientist'), coordinator_need, labeler_need, scientist_need)


class UploadDataPermission(Permission):
    def __init__(self, project_id):
        coordinator_need = ItemNeed('project_coordinator', int(project_id), 'project_role')
        scientist_need = ItemNeed('data_scientist', int(project_id), 'project_role')
        super(UploadDataPermission, self).__init__(RoleNeed('admin'), RoleNeed('project_coordinator'), RoleNeed('data_scientist'), coordinator_need, scientist_need)


class ListenPermission(Permission):
    def __init__(self, file_name):
        restricted = LabeledClip.query.filter(LabeledClip.file_name == file_name).join(Label, Label.id == LabeledClip.label_id).filter(Label.restricted == True).first()
        if restricted:
            station = MonitoringStation.query.join(Equipment).join(AudioFile, AudioFile.sn == Equipment.serial_number).filter(AudioFile.name == file_name).first()
            project_need = ItemNeed('project_coordinator', int(station.project_id), 'project_role')
        else:
            project_need = UserNeed(current_user.id)
        super(ListenPermission, self).__init__(RoleNeed('admin'), RoleNeed('project_coordinator'), project_need)


class ManageLabelsPermission(Permission):
    def __init__(self, project_id):
        coordinator_need = ItemNeed('project_coordinator', int(project_id), 'project_role')
        super(ManageLabelsPermission, self).__init__(RoleNeed('admin'), RoleNeed('project_coordinator'), coordinator_need)

