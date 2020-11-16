from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from app import db, admin
from app.user.roles import admin_permission
from app.models import User, Project, ProjectUser, MonitoringStation, EquipmentType, Equipment, ClusterGroup, LabelType, Label, Language, CommonName, ProjectLabel, MLModel, ModelIteration, ModelLabel 


# Customized model view class
class MyModelView(ModelView):
    def is_accessible(self):
        return admin_permission.can()


class ClusterGroupView(MyModelView):
    form_excluded_columns = ('clusters')


admin.add_link(MenuLink(name='Main Site', category='', url='/'))

admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Project, db.session))
admin.add_view(MyModelView(ProjectUser, db.session))
admin.add_view(MyModelView(MonitoringStation, db.session))
admin.add_view(MyModelView(EquipmentType, db.session))
admin.add_view(MyModelView(Equipment, db.session))
admin.add_view(ClusterGroupView(ClusterGroup, db.session))
admin.add_view(MyModelView(LabelType, db.session))
admin.add_view(MyModelView(Label, db.session))
admin.add_view(MyModelView(Language, db.session))
admin.add_view(MyModelView(CommonName, db.session))
admin.add_view(MyModelView(ProjectLabel, db.session))
admin.add_view(MyModelView(MLModel, db.session))
admin.add_view(MyModelView(ModelIteration, db.session))
admin.add_view(MyModelView(ModelLabel, db.session))

