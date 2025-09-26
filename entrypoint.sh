#!/bin/sh
set -e

# Aguarda Postgres se estiver configurado para usar Postgres
if [ "${DJANGO_DB_ENGINE}" = "postgres" ] || [ "${DJANGO_DB_ENGINE}" = "postgresql" ]; then
  echo "[entrypoint] Aguardando Postgres em ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}..."
  ATTEMPTS=0
  until python - <<'PY'
import os, psycopg2, time, sys
host=os.environ.get('POSTGRES_HOST','postgres')
port=int(os.environ.get('POSTGRES_PORT','5432'))
user=os.environ.get('POSTGRES_USER','postgres')
password=os.environ.get('POSTGRES_PASSWORD','')
db=os.environ.get('POSTGRES_DB','postgres')
try:
    psycopg2.connect(host=host, port=port, user=user, password=password, dbname=db).close()
except Exception as e:
    print(e)
    sys.exit(1)
PY
  do
    ATTEMPTS=$((ATTEMPTS+1))
    if [ "$ATTEMPTS" -ge 30 ]; then
      echo "[entrypoint] Postgres indisponível após 30 tentativas." >&2
      exit 1
    fi
    sleep 2
  done
  echo "[entrypoint] Postgres disponível."
fi

python manage.py migrate --noinput
echo "[entrypoint] Executando collectstatic..."
python manage.py collectstatic --noinput --verbosity=2

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
