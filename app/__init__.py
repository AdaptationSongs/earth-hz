import os
from flask import Flask, request, current_app
from flask_behind_proxy import FlaskBehindProxy
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_admin import Admin
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
login.session_protection = "strong"
bootstrap = Bootstrap()
admin = Admin()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    proxied_app = FlaskBehindProxy(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    bootstrap.init_app(app)
    admin.init_app(app)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.audio import bp as audio_bp
    app.register_blueprint(audio_bp)

    from app.clusters import bp as clusters_bp
    app.register_blueprint(clusters_bp)

    from app.labels import bp as labels_bp
    app.register_blueprint(labels_bp)

    return app

from app import models

