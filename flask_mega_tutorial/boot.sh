#! /bin/bash
source venv_flask/bin/activate
flask db upgrade
flask translate compile
exec gunicorn -b :5000 --access-logfile --error-logfile - flask_mega_tutorial:app