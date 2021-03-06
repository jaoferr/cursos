import os
import logging
import rq
import elasticsearch
from flask import Flask
from flask import current_app
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from flask import request
from logging.handlers import SMTPHandler
from logging.handlers import RotatingFileHandler
from datetime import datetime
from redis import Redis
from typing import TYPE_CHECKING

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy()
migrate = Migrate(compare_type=True)
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = _l(login.login_message)
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # elasticsearch
    if app.config['ELASTICSEARCH_URL']:
        app.elasticsearch = elasticsearch.Elasticsearch([app.config['ELASTICSEARCH_URL']])
        if app.elasticsearch.ping():
            pass
        else:
            app.logger.info('Elasticsearch server not running. Search functionality is not available.')
            app.elasticsearch = None
    else:
        app.elasticsearch = None
        app.logger.info('Elasticsearch not configured. Search functionality is not available.')

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)

    # redis
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue(app.config['REDIS_WORKER_NAME'], connection=app.redis)

    # blueprints
    from app.errors import blueprint as errors_blueprint
    app.register_blueprint(errors_blueprint)

    from app.auth import blueprint as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.main import blueprint as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.api import blueprint as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'],
                subject='Flask mega tutorial error - ' + str(datetime.utcnow()),
                credentials=auth,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/flask_mega_tutorial.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))

        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Flask mega tutorial')

    return app

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])

from app import models
