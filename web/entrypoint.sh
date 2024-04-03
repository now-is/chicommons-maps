#!/bin/bash
set -e

cd /app
python manage.py migrate
python manage.py migrate directory
python manage.py delete_existing_data
DJANGO_SUPERUSER_PASSWORD=password python manage.py createsuperuser --no-input --username=chicommons --email=chicommons@chicommons.com || true 
python manage.py loaddata 'directory/fixtures/seed_data.yaml'

exec "$@"

