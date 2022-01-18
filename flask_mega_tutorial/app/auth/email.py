import flask
from flask import current_app
from flask_babel import _
from app.email import send_email

def send_password_reset_email(user):
    token = user.get_reset_password_token()

    text_body = flask.render_template('email/reset_password.txt', user=user, token=token)
    html_body = flask.render_template('email/reset_password.html', user=user, token=token)

    send_email(
        '[Flask Mega Tutorial]' + _('Password reset'),
        sender=current_app.config['ADMINS'][0],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )