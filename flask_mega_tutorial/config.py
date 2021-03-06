import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-key'

    # sql alchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # email notifications
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['ADMIN@e.com']

    # pagination
    POSTS_PER_PAGE = 10

    # language support
    LANGUAGES = ['en', 'pt']
    TRANSLATOR_KEY = os.environ.get('TRANSLATOR_KEY')

    # elastic search
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')

    # redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    REDIS_WORKER_NAME = os.environ.get('REDIS_WORKER_NAME') or 'flask_mega_tutorial-tasks'
