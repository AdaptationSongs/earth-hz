from flask_login import UserMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, timedelta
import enum
from app import db
from flask import current_app


# DB Models


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.Column(db.Boolean, default=False)
    projects = db.relationship('ProjectUser', back_populates='user')

    def __repr__(self):
        return self.name


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
    labels = db.relationship('ProjectLabel', back_populates='project', lazy='dynamic')
    models = db.relationship('MLModel', back_populates='project', lazy='dynamic')

    def __repr__(self):
        return self.name


class ProjectUser(db.Model):
    __tablename__ = 'project_users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship('User', back_populates='projects')
    project_id = db.Column(db.Integer, db.ForeignKey(Project.id))
    project = db.relationship('Project')
    project_coordinator = db.Column(db.Boolean, default=False)
    data_labeler = db.Column(db.Boolean, default=False)
    data_scientist = db.Column(db.Boolean, default=False)


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
    recording_device = db.relationship('Equipment', foreign_keys=[sn], primaryjoin='Equipment.serial_number == AudioFile.sn')
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
    common_names = db.relationship('CommonName', back_populates='label')
    restricted = db.Column(db.Boolean, default=False)

    def translate(self, language='en'):
        result = CommonName.query.join(Language).filter(CommonName.label_id == self.id, Language.code == language).first()
        if result:
            return result.name
        else:
            return None

    def __repr__(self):
        translation =  self.translate()
        if translation:
            return self.name + ' (' + translation + ')'
        else:
            return self.name


class Language(db.Model):
    __tablename__ = 'language'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(5), nullable=False)
    code3 = db.Column(db.String(3))
    name = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return self.name


class CommonName(db.Model):
    __tablename__ = 'common_name'
    id = db.Column(db.Integer, primary_key=True)
    label_id = db.Column(db.Integer, db.ForeignKey(Label.id), nullable=False)
    label = db.relationship('Label', back_populates='common_names')
    language_id = db.Column(db.Integer, db.ForeignKey(Language.id), nullable=False)
    language = db.relationship('Language')
    name = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return self.name


class LabeledClip(db.Model):
    __tablename__ = 'labeled_clips'
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), db.ForeignKey(AudioFile.name), index=True)
    file = db.relationship('AudioFile')
    offset = db.Column(db.Float, index=True)
    duration = db.Column(db.Float)
    exact_time = db.Column(db.Boolean, default=False) 
    label_id = db.Column(db.Integer, db.ForeignKey(Label.id), index=True)
    label = db.relationship('Label', foreign_keys=[label_id])
    sub_label_id = db.Column(db.Integer, db.ForeignKey(Label.id))
    sub_label = db.relationship('Label', foreign_keys=[sub_label_id])
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship('User')
    certain = db.Column(db.Boolean, default=True)
    notes = db.Column(db.String(255), nullable=True)
    modified = db.Column(db.DateTime, default=datetime.utcnow)

    def start_time(self):
        return str(self.file.timestamp + timedelta(seconds=self.offset))


class ProjectLabel(db.Model):
    __tablename__ = 'project_labels'
    id = db.Column(db.Integer, primary_key=True)
    label_id = db.Column(db.Integer, db.ForeignKey(Label.id), nullable=False)
    label = db.relationship('Label')
    project_id = db.Column(db.Integer, db.ForeignKey(Project.id), nullable=False)
    project = db.relationship('Project')

    @hybrid_property
    def clip_count(self):
        return LabeledClip.query.join(AudioFile).join(Equipment, AudioFile.sn == Equipment.serial_number).join(MonitoringStation).filter(MonitoringStation.project_id == self.project_id).filter(LabeledClip.label_id == self.label_id).count()

    @clip_count.expression
    def clip_count(cls):
        q = db.select([db.func.count(LabeledClip.id)])
        q = q.select_from(db.join(q.froms[0], AudioFile).join(Equipment, AudioFile.sn == Equipment.serial_number).join(MonitoringStation)).where(MonitoringStation.project_id == cls.project_id).where(LabeledClip.label_id == cls.label_id)
        return q


class MLModel(db.Model):
    __tablename__ = 'ml_models'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey(Project.id), nullable=False)
    project = db.relationship('Project', back_populates='models')
    name = db.Column(db.String(255))
    description = db.Column(db.String(255))
    iterations = db.relationship('ModelIteration', back_populates='model', lazy='dynamic')

    def __repr__(self):
        return self.name


class StatusEnum(enum.Enum):
    labeling = 'Labeling'
    ready_to_train = 'Ready to train'
    training = 'Training'
    trained = 'Trained'
    ready_to_run = 'Ready to run'
    running = 'Running'
    finished = 'Finished'

    def __str__(self):
        return self.value


class ModelIteration(db.Model):
    __tablename__ = 'model_iterations'
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey(MLModel.id), nullable=False)
    model = db.relationship('MLModel', back_populates='iterations')
    updated = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    description = db.Column(db.String(255))
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.labeling)
    accuracy = db.Column(db.Float)
    training_errors = db.relationship('TrainingError', back_populates='iteration', lazy='dynamic')

    def __repr__(self):
        return self.model.name + ': ' + str(self.updated)

    def next_status(self):
        if self.status == StatusEnum.labeling:
            return StatusEnum.ready_to_train
        elif self.status == StatusEnum.trained:
            return StatusEnum.ready_to_run
        else:
            return None

    def previous_status(self):
        if self.status == StatusEnum.ready_to_train or self.status == StatusEnum.trained or self.status == StatusEnum.ready_to_run:
            return StatusEnum.labeling
        else:
            return None


class ModelLabel(db.Model):
    __tablename__ = 'model_labels'
    id = db.Column(db.Integer, primary_key=True)
    iteration_id = db.Column(db.Integer, db.ForeignKey(ModelIteration.id), nullable=False)
    iteration = db.relationship('ModelIteration')
    label_id = db.Column(db.Integer, db.ForeignKey(Label.id), nullable=False)
    label = db.relationship('Label', foreign_keys=[label_id])
    combine_with_id = db.Column(db.Integer, db.ForeignKey(Label.id))
    combine_with = db.relationship('Label', foreign_keys=[combine_with_id])
    project_label = db.relationship('ProjectLabel', secondary='join(Project, MLModel).join(ModelIteration)', primaryjoin='and_(ProjectLabel.label_id == ModelLabel.label_id, ModelIteration.id == ModelLabel.iteration_id)', uselist=False, viewonly=True)
    training_errors = db.relationship('TrainingError', primaryjoin='and_(foreign(ModelLabel.iteration_id) == TrainingError.iteration_id, foreign(ModelLabel.label_id) == TrainingError.should_be_id)', uselist=True, viewonly=True, lazy='dynamic')


class ModelOutput(db.Model):
    __tablename__ = 'model_outputs'
    id = db.Column(db.Integer, primary_key=True)
    iteration_id = db.Column(db.Integer, db.ForeignKey(ModelIteration.id), nullable=False, index=True)
    iteration = db.relationship('ModelIteration')
    file_name = db.Column(db.String(255), db.ForeignKey(AudioFile.name), nullable=False, index=True)
    file = db.relationship('AudioFile')
    label_id = db.Column(db.Integer, db.ForeignKey(Label.id), nullable=False, index=True)
    label = db.relationship('Label')
    offset = db.Column(db.Float, nullable=False, index=True)
    duration = db.Column(db.Float, nullable=False)
    probability = db.Column(db.Float, nullable=False, index=True)

    def start_time(self):
        return str(self.file.timestamp + timedelta(seconds=self.offset))

    def labeled_clips(self):
        return LabeledClip.query.filter_by(file_name=self.file_name, offset=self.offset).all()


class TrainingError(db.Model):
    __tablename__ = 'training_errors'
    id = db.Column(db.Integer, primary_key=True)
    iteration_id = db.Column(db.Integer, db.ForeignKey(ModelIteration.id), nullable=False)
    iteration = db.relationship('ModelIteration', back_populates='training_errors')
    file_name = db.Column(db.String(255), db.ForeignKey(AudioFile.name), nullable=False)
    file = db.relationship('AudioFile')
    offset = db.Column(db.Float, nullable=False)
    should_be_id = db.Column(db.Integer, db.ForeignKey(Label.id), nullable=False)
    should_be = db.relationship('Label', foreign_keys=[should_be_id])
    came_out_id = db.Column(db.Integer, db.ForeignKey(Label.id), nullable=False)
    came_out = db.relationship('Label', foreign_keys=[came_out_id])
