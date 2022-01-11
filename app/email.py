import flask_mail
from app import mail
from app import app
import flask

def send_email(subject, sender, recipients, text_body, html_body):
    msg = flask_mail.Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

def send_password_reset_email(user):
    token = user.get_reset_password_token()

    text_body = flask.render_template('email/reset_password.txt', user=user, token=token)
    html_body = flask.render_template('email/reset_password.html', user=user, token=token)

    send_email(
        '[Flask Mega Tutorial] Password reset',
        sender=app.config['ADMINS'][0],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )