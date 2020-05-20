import os
from dotenv import load_dotenv
import redis

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Do not edit this file. Instead, create a a file named .env and set these variables there
class Config(object):
    APP_NAME = os.environ.get('APP_NAME') or 'Earth-Hz'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'SUPERSECRETKEYPHRASE'
    DEBUG = int(os.environ.get('DEBUG') or False)
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///'+os.path.join(basedir, 'app.db')
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE') or 20)
    CLIP_SECS = float(os.environ.get('CLIP_SECS') or 5)

    # Flask-Session
    SESSION_TYPE = os.environ.get('SESSION_TYPE')
    SESSION_REDIS = redis.from_url(os.environ.get('SESSION_REDIS') or 'redis://127.0.0.1:6379')

    # Google OAuth
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')

    # Azure Data Lake
    ADLS_ACCOUNT = os.environ.get('ADLS_ACCOUNT')
    ADLS_TENANT = os.environ.get('ADLS_TENANT')
    ADLS_CLIENT_ID = os.environ.get('ADLS_CLIENT_ID')
    ADLS_CLIENT_SECRET = os.environ.get('ADLS_CLIENT_SECRET')
