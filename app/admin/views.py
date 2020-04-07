from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from app import db, admin
from app.user.roles import admin_permission
from app.models import User, MonitoringStation, EquipmentType, Equipment, ClusterGroup, LabelType, Label, Language, CommonName 


# Customized model view class
class MyModelView(ModelView):
    def is_accessible(self):
        return admin_permission.can()

admin.add_link(MenuLink(name='Main Site', category='', url='/'))

admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(MonitoringStation, db.session))
admin.add_view(MyModelView(EquipmentType, db.session))
admin.add_view(MyModelView(Equipment, db.session))
admin.add_view(MyModelView(ClusterGroup, db.session))
admin.add_view(MyModelView(LabelType, db.session))
admin.add_view(MyModelView(Label, db.session))
admin.add_view(MyModelView(Language, db.session))
admin.add_view(MyModelView(CommonName, db.session))

