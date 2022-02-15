from flask import current_app
import flask_mail
from app import mail
from threading import Thread


def async_send_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(
    subject: str, sender:str, recipients: list[str], 
    text_body: str, html_body: str,
    attachments: list[tuple]=None, sync: bool=False):
    msg = flask_mail.Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body

    if attachments:
        for attachment in attachments:
            msg.attach(attachment)
    if sync:
        mail.send(msg)
    else:
        Thread(
            target=async_send_email, 
            args=(current_app._get_current_object(), msg)).start()
