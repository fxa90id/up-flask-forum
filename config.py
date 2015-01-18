import os
import json

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
path = lambda *args: os.path.join(ROOT_DIR, *args)

get_secret_key = lambda: os.getenv('FLASK_SECRET_KEY', 'ThisIsNotASecret')

class Config(object):
    DEBUG = False
    TESTING = False
    DATABASE_URI = 'sqlite:////tmp/file.db'
    SECRET_KEY = get_secret_key()

class ProductionConfig(Config):
    DATABASE_URI = 'mysql://fforum@localhost/fforum'

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True