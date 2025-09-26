#!/bin/bash

echo "=== Teste de Pipeline de Assets Tailwind ==="

# 1. Compilar Tailwind localmente
echo "1. Compilando Tailwind..."
npm run build
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao compilar Tailwind"
    exit 1
fi

# 2. Verificar se o arquivo foi criado
echo "2. Verificando arquivo CSS gerado..."
if [ -f "perdcomp/static/css/app.css" ]; then
    echo "✓ app.css encontrado ($(wc -c < perdcomp/static/css/app.css) bytes)"
else
    echo "✗ app.css não encontrado"
    exit 1
fi

# 3. Testar build Docker (se Docker estiver rodando)
echo "3. Testando build Docker..."
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "Docker disponível, iniciando build..."
    docker compose build --no-cache web
    if [ $? -eq 0 ]; then
        echo "✓ Build Docker concluído"
        
        # 4. Subir containers
        echo "4. Subindo containers..."
        docker compose up -d
        sleep 10
        
        # 5. Verificar arquivo no container
        echo "5. Verificando CSS no container..."
        docker compose exec web ls -l perdcomp/static/css/app.css
        
        # 6. Testar endpoint
        echo "6. Testando endpoint static..."
        curl -s -o /dev/null -w "%{http_code}" http://localhost/static/css/app.css
        
    else
        echo "✗ Falha no build Docker"
    fi
else
    echo "⚠️ Docker não disponível, pulando testes Docker"
fi

echo "=== Teste concluído ==="
