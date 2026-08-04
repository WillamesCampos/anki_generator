#!/bin/sh
set -e

if [ "$1" = "web" ]; then
    python manage.py migrate --noinput
    exec python manage.py runserver 0.0.0.0:8000
elif [ "$1" = "celery-worker" ]; then
    exec celery -A core worker --loglevel=info
else
    exec "$@"
fi
