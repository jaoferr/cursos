import flask
from app import app
from app import db
from app.errors import blueprint


# @app.errorhandler(404)
@blueprint.app_errorhandler(404)
def not_found_error(error):
    return flask.render_template('errors/404.html'), 404

# @app.errorhandler(500)
@blueprint.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return flask.render_template('errors/500.html'), 500
