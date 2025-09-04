FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências de sistema mínimas para Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x /app/entrypoint.sh || true

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=perdcomp.settings \
    DJANGO_DEBUG=True \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
    PYTHONPATH=/app

ENTRYPOINT ["/app/entrypoint.sh"]
