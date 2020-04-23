from flask_login import UserMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from datetime import datetime, timedelta
from app import db, login
from flask import current_app

# DB Models


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return self.name

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User)


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return self.name


class MonitoringStation(db.Model):
    __tablename__ = 'monitoring_stations'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey(Project.id))
    project = db.relationship('Project')
    name = db.Column(db.String(255), nullable=False)
    attachment_point = db.Column(db.String(255))
    details = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    elevation = db.Column(db.Float)
    height = db.Column(db.Float)
    canopy_density = db.Column(db.Integer)

    def __repr__(self):
        return self.name


class EquipmentType(db.Model):
    __tablename__ = 'equipment_types'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return self.name


class Equipment(db.Model):
    __tablename__ = 'equipment'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey(MonitoringStation.id), nullable=False)
    station = db.relationship('MonitoringStation')
    type_id = db.Column(db.Integer, db.ForeignKey(EquipmentType.id), nullable=False)
    type = db.relationship('EquipmentType')
    manufacturer = db.Column(db.String(255))
    model = db.Column(db.String(255))
    serial_number = db.Column(db.String(255))
    deployed = db.Column(db.DateTime)
    removed = db.Column(db.DateTime)
    notes = db.Column(db.String(255))

    def __repr__(self):
        return self.serial_number


class AudioFile(db.Model):
    __tablename__ = 'audio_files'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    sn = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime)
    path = db.Column(db.String(255))
    name = db.Column(db.String(255), unique=True)
    size = db.Column(db.Integer)


class ClusterGroup(db.Model):
    __tablename__ = 'cluster_groups'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey(Project.id))
    project = db.relationship('Project')
    name = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship('User')
    clusters = db.relationship('Cluster', back_populates='group', cascade='all, delete, delete-orphan')


class Cluster(db.Model):
    __tablename__ = 'clusters'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    file_name = db.Column('IN FILE', db.String(255), db.ForeignKey(AudioFile.name))
    file = db.relationship('AudioFile')
    start = db.Column('OFFSET', db.Float)
    duration = db.Column('DURATION', db.Float)
    cluster_name = db.Column('TOP1MATCH', db.String(255))
    label = db.Column('MANUAL ID', db.String(255))
    cg_id = db.Column(db.Integer, db.ForeignKey(ClusterGroup.id), nullable=False)
    group = db.relationship('ClusterGroup', back_populates='clusters')

    def start_f(self):
        return str(timedelta(seconds=self.start))

    def nearest_window(self):
        window = current_app.config['CLIP_SECS']
        return round(self.start / window) * window

    def window_start(self):
        return str(self.file.timestamp + timedelta(seconds=self.nearest_window()))

    def name_count(self):
        return Cluster.query.filter_by(cluster_name=self.cluster_name, cg_id=self.cg_id).count()

    def labeled_clips(self):
        return LabeledClip.query.filter_by(file_name=self.file_name, offset=self.nearest_window()).all()


class LabelType(db.Model):
    __tablename__ = 'label_types'
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('label_types.id'))
    parent_type = db.relationship('LabelType', remote_side=[id])
    name = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return self.name


class Label(db.Model):
    __tablename__ = 'labels'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey(LabelType.id), nullable=False)
    type = db.relationship('LabelType')

    def __repr__(self):
        return self.name


class Language(db.Model):
    __tablename__ = 'language'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(5), nullable=False)
    name = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return self.name


class CommonName(db.Model):
    __tablename__ = 'common_name'
    id = db.Column(db.Integer, primary_key=True)
    label_id = db.Column(db.Integer, db.ForeignKey(Label.id), nullable=False)
    label = db.relationship('Label')
    language_id = db.Column(db.Integer, db.ForeignKey(Language.id), nullable=False)
    language = db.relationship('Language')
    name = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return self.name


class LabeledClip(db.Model):
    __tablename__ = 'labeled_clips'
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), db.ForeignKey(AudioFile.name))
    file = db.relationship('AudioFile')
    offset = db.Column(db.Float)
    duration = db.Column(db.Float)
    label_id = db.Column(db.Integer, db.ForeignKey(Label.id))
    label = db.relationship('Label', foreign_keys=[label_id])
    sub_label_id = db.Column(db.Integer, db.ForeignKey(Label.id))
    sub_label = db.relationship('Label', foreign_keys=[sub_label_id])
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship('User')
    certain = db.Column(db.Boolean, default=True)
    notes = db.Column(db.String(255), nullable=True)
    modified = db.Column(db.DateTime, default=datetime.utcnow())

    def start_time(self):
        return str(self.file.timestamp + timedelta(seconds=self.offset))


class ProjectLabel(db.Model):
    __tablename__ = 'project_labels'
    id = db.Column(db.Integer, primary_key=True)
    label_id = db.Column(db.Integer, db.ForeignKey(Label.id), nullable=False)
    label = db.relationship('Label')
    project_id = db.Column(db.Integer, db.ForeignKey(Project.id), nullable=False)
    project = db.relationship('Project')


class MLModel(db.Model):
    __tablename__ = 'ml_models'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey(Project.id), nullable=False)
    project = db.relationship('Project')
    name = db.Column(db.String(255))

    def __repr__(self):
        return self.name


class ModelIteration(db.Model):
    __tablename__ = 'model_iterations'
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey(MLModel.id), nullable=False)
    model = db.relationship('MLModel')
    training_date = db.Column(db.DateTime, default=datetime.utcnow(), nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return self.model.name + ': ' + str(self.training_date)


class ModelOutput(db.Model):
    __tablename__ = 'model_outputs'
    id = db.Column(db.Integer, primary_key=True)
    iteration_id = db.Column(db.Integer, db.ForeignKey(ModelIteration.id), nullable=False)
    iteration = db.relationship('ModelIteration')
    file_name = db.Column(db.String(255), db.ForeignKey(AudioFile.name), nullable=False)
    file = db.relationship('AudioFile')
    label_id = db.Column(db.Integer, db.ForeignKey(Label.id), nullable=False)
    label = db.relationship('Label')
    offset = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    probability = db.Column(db.Float, nullable=False)

    def start_time(self):
        return str(self.file.timestamp + timedelta(seconds=self.offset))

    def labeled_clips(self):
        return LabeledClip.query.filter_by(file_name=self.file_name, offset=self.offset).all()
