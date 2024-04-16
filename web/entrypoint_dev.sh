#!/bin/bash
set -e

cd /code/

python manage.py collectstatic --no-input

if [ ! -f "/data/db.sqlite3" ]; then
    python manage.py migrate
    DJANGO_SUPERUSER_PASSWORD=password python manage.py createsuperuser --no-input --username=chicommons --email=chicommons@chicommons.com || true 
    python manage.py loaddata 'directory/fixtures/seed_data.yaml'
fi

python manage.py runserver 0.0.0.0:8000