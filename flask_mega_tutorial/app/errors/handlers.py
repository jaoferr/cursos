import flask
from app import db
from app.errors import blueprint
from app.api.errors import error_response as api_error_response


def prefer_json_response():
    return flask.request.accept_mimetypes['application/json'] >= \
        flask.request.accept_mimetypes['text/html']

@blueprint.app_errorhandler(404)
def not_found_error(error):
    if prefer_json_response():
        return api_error_response(404)
    return flask.render_template('errors/404.html'), 404

@blueprint.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if prefer_json_response():
        return api_error_response(500)

    return flask.render_template('errors/500.html'), 500
