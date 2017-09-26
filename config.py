import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = os.getenv('DEBUG') == 'True'
    TESTING = os.getenv('TESTING') == 'True'
    CSRF_ENABLED = os.getenv('CSRF_ENABLED') == 'True'
