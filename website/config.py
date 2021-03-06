import os


class BaseConfig(object):
    DEBUG = bool(os.environ['DEBUG'])
    TESTING = os.environ['TESTING']
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
    SQLALCHEMY_POOL_RECYCLE = int(os.environ['SQLALCHEMY_POOL_RECYCLE'])
    CLIENT_ID = os.environ['CLIENT_ID']
    CLIENT_SECRET = os.environ['CLIENT_SECRET']
    REDIRECT_URI = os.environ['REDIRECT_URI']
    SQLALCHEMY_TRACK_MODIFICATIONS = bool(os.environ['SQLALCHEMY_TRACK_MODIFICATIONS'])
