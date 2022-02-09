#! /bin/bash
source venv_flask/bin/activate
while true; do
    flask db upgrade
    if [ "$?" == "0" ] 
    then
        break
    fi
    echo Upgrade command failed, retrying in 5 secs...
    sleep 5
done
flask translate compile
exec gunicorn -b :5000 --access-logfile - --error-logfile - flask_mega_tutorial:app