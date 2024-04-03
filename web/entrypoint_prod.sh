#!/bin/sh

python manage.py collectstatic --no-input --settings=directory.settings.prod
uwsgi --ini /code/uwsgi.ini
# Optionally, execute the command passed to the Docker container
exec "$@"
