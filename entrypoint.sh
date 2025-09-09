#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

if [ "${DJANGO_DEBUG}" = "True" ] || [ "${DJANGO_DEBUG}" = "true" ]; then
  echo "[entrypoint] Iniciando em modo desenvolvimento (runserver)"
  exec python manage.py runserver 0.0.0.0:8000
else
  echo "[entrypoint] Iniciando em modo produção simplificado (gunicorn)"
  : "${PORT:=8000}"
  : "${WEB_CONCURRENCY:=$(python - <<'PY'
import multiprocessing as mp
print(max(2, (mp.cpu_count() * 2) + 1))
PY
)}"
  exec gunicorn perdcomp.wsgi:application \
    --bind 0.0.0.0:"${PORT}" \
    --workers "${WEB_CONCURRENCY}" \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
fi
