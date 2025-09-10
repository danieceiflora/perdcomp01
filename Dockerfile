############################################
# Stage 1: Build de assets (Tailwind CSS)  #
############################################
FROM node:20-alpine AS assets
WORKDIR /build

# Copia apenas manifestos primeiro para cache eficiente
COPY package.json ./
# Se existir lockfile copie também (não falha se não houver)
COPY package-lock.json* ./

RUN npm install --no-audit --no-fund --quiet

# Copia configs + todo o código ( .dockerignore controla o que entra )
COPY . .

# Gera CSS minificado (garante diretório existente)
RUN test -f ./perdcomp/static/src/input.css || (echo '[ERRO] Arquivo input.css não encontrado' && ls -R perdcomp/static | head -200 && exit 1); \
    npx tailwindcss -i ./perdcomp/static/src/input.css -o ./perdcomp/static/css/app.css --minify

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

# Copia CSS compilado do estágio de assets (overwrite caso exista)
# Copia apenas se foi gerado (multi-stage garante, mas evita falha em build parcial)
COPY --from=assets /build/perdcomp/static/css/app.css ./perdcomp/static/css/app.css
RUN chmod +x /app/entrypoint.sh || true

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=perdcomp.settings \
    PYTHONPATH=/app

ENTRYPOINT ["/app/entrypoint.sh"]
