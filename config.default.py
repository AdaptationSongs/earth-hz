import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    APP_NAME = "Earth Hz"
    SECRET_KEY = os.environ.get("SECRET_KEY") or "SUPERSECRETKEYPHRASE"
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, "test.db")
    ITEMS_PER_PAGE = 20
    CLIP_SECS = 5

    # Google OAuth
    CLIENT_ID =
    CLIENT_SECRET =
    REDIRECT_URI =
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
    SCOPE = ['profile', 'email']

    # Azure Data Lake
    ADLS_ACCOUNT =
    ADLS_TENANT =
    ADLS_CLIENT_ID =
    ADLS_CLIENT_SECRET =

