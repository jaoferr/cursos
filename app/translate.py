import json
import requests
from flask_babel import _
from app import app


def translate(text, source_language, dest_language):
    if 'TRANSLATOR_KEY' not in app.config or not app.config['TRANSLATOR_KEY']:
        return _('Translation service is not configured.')

    return _('Translation service is not configured.')

    # microsft azure service, disabled
    auth = {
        'Ocp-Apim-Subscription-Key': app.config['TRANSLATOR_KEY'],
        'Ocp-Apim-Subscription-Region': ''
    }
    r = requests.post(
        'https://api.cognitive.microsofttranslator.com'
        f'/translate?api-version=3.0&from={source_language}&to={dest_language}',
        headers=auth, json=[{'Text': text}]
    )
    if r.status_code != 200:
        return _('Translation service failed.')
    return r.json()[0]['translations'][0]['text']
