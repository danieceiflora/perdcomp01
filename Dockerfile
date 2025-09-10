############################################
# Stage 1: Build de assets (Tailwind CSS)  #
############################################
FROM node:20-alpine AS assets
WORKDIR /build

# Copia package files para cache eficiente
COPY package*.json ./
RUN npm ci --no-audit --no-fund --quiet

# Copia configurações e arquivos necessários para Tailwind
COPY tailwind.config.js postcss.config.js ./
COPY perdcomp/templates perdcomp/templates/
COPY */templates */templates/
COPY perdcomp/static perdcomp/static/

# Compila Tailwind CSS
RUN npx tailwindcss -i ./perdcomp/static/src/input.css -o ./perdcomp/static/css/app.css --minify

############################################
# Stage 2: Runtime Python + Django + Gunicorn
############################################
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

# Garante diretórios de dados/estáticos existentes na imagem
RUN mkdir -p /app/sqlite /app/media /app/staticfiles

COPY . .

# Copia CSS compilado do estágio de assets
COPY --from=assets /build/perdcomp/static/css/app.css ./perdcomp/static/css/app.css
RUN chmod +x /app/entrypoint.sh || true

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=perdcomp.settings \
    PYTHONPATH=/app

ENTRYPOINT ["/app/entrypoint.sh"]
