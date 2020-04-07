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
    GOOGLE_OAUTH_CLIENT_ID =
    GOOGLE_OAUTH_CLIENT_SECRET =

    # Azure Data Lake
    ADLS_ACCOUNT =
    ADLS_TENANT =
    ADLS_CLIENT_ID =
    ADLS_CLIENT_SECRET =

