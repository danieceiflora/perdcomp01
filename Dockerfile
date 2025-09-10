############################################
# Stage 1: Build de assets (Tailwind CSS)  #
############################################
FROM node:20-alpine AS assets
WORKDIR /build

# Copia todo o código primeiro para garantir presença de perdcomp/static
COPY . .

# Diagnóstico de estrutura (limite para não explodir log)
RUN echo "[DEBUG] Estrutura de diretorios (nivel 2):" && find . -maxdepth 2 -type d | sort && \
        echo "[DEBUG] Listando perdcomp/static:" && (ls -R perdcomp/static 2>/dev/null | head -200 || echo '[WARN] perdcomp/static ausente')

# Instala dependências Node (usa lock se existir)
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi

# Compila Tailwind somente se o fonte existir; caso contrário cria CSS vazio para não quebrar estágio seguinte
RUN if [ -f ./perdcomp/static/src/input.css ]; then \
            echo "[INFO] Compilando Tailwind" && \
            npx tailwindcss -i ./perdcomp/static/src/input.css -o ./perdcomp/static/css/app.css --minify ; \
        else \
            echo "[WARN] Fonte Tailwind (perdcomp/static/src/input.css) não encontrado. Gerando placeholder." && \
            mkdir -p ./perdcomp/static/css && echo '/* placeholder tailwind (fonte ausente no build) */' > ./perdcomp/static/css/app.css ; \
        fi

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
