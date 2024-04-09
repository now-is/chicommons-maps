#!/bin/sh
set -e

mkdir -p /config/uwsgi/socket/
chown -R www-data:www-data /config/uwsgi/socket/


python manage.py collectstatic --no-input --settings=directory.settings.prod
uwsgi --ini /code/uwsgi.ini