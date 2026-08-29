#!/bin/sh
set -e

if [ "$1" = "web" ]; then
    python manage.py migrate --noinput
    exec python manage.py runserver 0.0.0.0:8000
elif [ "$1" = "celery-worker" ]; then
    exec celery -A core worker --loglevel=info
elif [ "$1" = "celery-beat" ]; then
    # `--schedule` fora de /app de propósito: /app é bind mount do host em
    # dev, sobrescrevendo o chown feito no build da imagem (mesmo problema
    # já visto no document-generator com /data/anki_audio) — o usuário
    # anki_generator não-root não conseguiria escrever o arquivo de estado
    # do scheduler ali.
    exec celery -A core beat --loglevel=info --schedule=/var/lib/celery/celerybeat-schedule
else
    exec "$@"
fi
