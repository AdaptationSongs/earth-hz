import dash
from flask import Flask, request, current_app
from flask.helpers import get_root_path
from flask.json import JSONEncoder
from datetime import date
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_login import LoginManager, login_required
from flask_session import Session
from flask_bootstrap import Bootstrap
from flask_admin import Admin
from flask_principal import Principal, identity_loaded
import flask_excel as excel
from config import Config

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
login = LoginManager()
sess = Session()
bootstrap = Bootstrap()
admin = Admin()
principal = Principal() 


class CustomJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, date):
            return o.isoformat()
        return super().default(o)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # initialize plugins
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    login.login_view = 'user_views.login'
    login.login_message = 'Please log in to access this page.'
    login.session_protection = "strong"
    sess.init_app(app)
    bootstrap.init_app(app)
    admin.init_app(app)
    principal.init_app(app)
    excel.init_excel(app)

    register_blueprints(app)
    register_dashapps(app)

    # connect listener for identity loaded signal
    from app.user.roles import on_identity_loaded
    identity_loaded.connect_via(app)(on_identity_loaded)

    # custom overrides
    app.json_encoder = CustomJSONEncoder

    # App is behind https proxy
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

    return app

def register_blueprints(app):
    from app.user.google import bp as google_bp
    app.register_blueprint(google_bp, url_prefix='/login')

    from app.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.projects import bp as projects_bp
    app.register_blueprint(projects_bp, url_prefix='/projects')

    from app.audio import bp as audio_bp
    app.register_blueprint(audio_bp)

    from app.clusters import bp as clusters_bp
    app.register_blueprint(clusters_bp)

    from app.labels import bp as labels_bp
    app.register_blueprint(labels_bp, url_prefix='/labels')

    from app.ml import bp as ml_bp
    app.register_blueprint(ml_bp, url_prefix='/ml')

    from app.results_dash import bp as results_dash_bp
    app.register_blueprint(results_dash_bp, url_prefix='/visualize')


def register_dashapps(app):
    from app.results_dash.layout import layout
    from app.results_dash.callbacks import register_callbacks

    # Meta tags for viewport responsiveness
    meta_viewport = {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}

    results_dash = dash.Dash(__name__,
                         server=app,
                         url_base_pathname='/results_dash/',
                         assets_folder=get_root_path(__name__) + '/results_dash/assets/',
                         meta_tags=[meta_viewport])

    with app.app_context():
        results_dash.title = 'Results Dashboard'
        results_dash.layout = layout
        register_callbacks(results_dash)

    _protect_dashviews(results_dash)


def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])



from app import models

