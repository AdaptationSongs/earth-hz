from app import ma
from app.models import User, Language, CommonName, Label, LabelType, ProjectLabel, LabeledClip


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

class LabeledClipSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = LabeledClip
        load_instance = True
        include_fk = True

    label = ma.Nested(LabelSchema)
    sub_label = ma.Nested(LabelSchema)
    user = ma.Nested(UserSchema, only=('name',))
