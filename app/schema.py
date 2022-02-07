from app import ma
from app.models import User, Language, CommonName, Label, LabelType, ProjectLabel, LabeledClip, MonitoringStation, Equipment, AudioFile, Cluster, ModelOutput


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True


class LanguageSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Language
        load_instance = True
        include_fk = True


class CommonNameSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CommonName
        load_instance = True
        include_fk = True

    language = ma.Nested(LanguageSchema)


class LabelTypeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = LabelType
        load_instance = True
        include_fk = True


class LabelSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Label
        load_instance = True
        include_fk = True

    common_names = ma.Nested(CommonNameSchema, many=True)
    type = ma.Nested(LabelTypeSchema)


class ProjectLabelSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ProjectLabel
        load_instance = True
        include_fk = True

    label = ma.Nested(LabelSchema)
    clip_count = ma.Function(lambda obj: obj.clip_count)


class LabeledClipSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = LabeledClip
        load_instance = True
        include_fk = True

    label = ma.Nested(LabelSchema)
    sub_label = ma.Nested(LabelSchema)
    user = ma.Nested(UserSchema, only=('name',))


class MonitoringStationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = MonitoringStation
        load_instance = True
        include_fk = True


class EquipmentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Equipment
        load_instance = True
        include_fk = True

    station = ma.Nested(MonitoringStationSchema)


class AudioFileSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AudioFile
        load_instance = True
        include_fk = True

    recording_device = ma.Nested(EquipmentSchema)


class ClusterSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Cluster
        load_instance = True
        include_fk = True

    window_start = ma.Function(lambda obj: obj.window_start())
    offset = ma.Function(lambda obj: obj.nearest_window())
    file = ma.Nested(AudioFileSchema)


class ModelOutputSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ModelOutput
        load_instance = True
        include_fk = True

    window_start = ma.Function(lambda obj: obj.start_time())
    file = ma.Nested(AudioFileSchema)
    label = ma.Nested(LabelSchema)
