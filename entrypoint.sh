#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

if [ "${DJANGO_DEBUG}" = "True" ] || [ "${DJANGO_DEBUG}" = "true" ]; then
  echo "[entrypoint] Iniciando em modo desenvolvimento (runserver)"
  exec python manage.py runserver 0.0.0.0:8000
else
  echo "[entrypoint] Iniciando em modo produção simplificado (gunicorn)"
  exec gunicorn perdcomp.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --log-level info
fi
