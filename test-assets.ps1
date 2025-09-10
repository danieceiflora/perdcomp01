# Script de teste para pipeline de assets Tailwind
Write-Host "=== Teste de Pipeline de Assets Tailwind ===" -ForegroundColor Yellow

# 1. Compilar Tailwind localmente
Write-Host "1. Compilando Tailwind..." -ForegroundColor Cyan
try {
    npm run build
    Write-Host "✓ Tailwind compilado com sucesso" -ForegroundColor Green
} catch {
    Write-Host "✗ Erro ao compilar Tailwind" -ForegroundColor Red
    exit 1
}

# 2. Verificar se o arquivo foi criado
Write-Host "2. Verificando arquivo CSS gerado..." -ForegroundColor Cyan
$cssFile = "perdcomp/static/css/app.css"
if (Test-Path $cssFile) {
    $size = (Get-Item $cssFile).Length
    Write-Host "✓ app.css encontrado ($size bytes)" -ForegroundColor Green
} else {
    Write-Host "✗ app.css não encontrado" -ForegroundColor Red
    exit 1
}

# 3. Verificar Docker
Write-Host "3. Verificando Docker..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version
    Write-Host "✓ $dockerVersion" -ForegroundColor Green
    
    # Testar se Docker Desktop está rodando
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker Engine rodando" -ForegroundColor Green
        
        # Build da imagem
        Write-Host "4. Fazendo build da imagem..." -ForegroundColor Cyan
        docker compose build --no-cache web
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Build concluído com sucesso" -ForegroundColor Green
            
            # Subir containers
            Write-Host "5. Subindo containers..." -ForegroundColor Cyan
            docker compose up -d
            
            # Aguardar inicialização
            Start-Sleep 15
            
            # Verificar arquivo no container
            Write-Host "6. Verificando CSS no container..." -ForegroundColor Cyan
            docker compose exec web ls -l perdcomp/static/css/app.css
            
            # Testar endpoint (se curl estiver disponível)
            Write-Host "7. Testando endpoint /static/css/app.css..." -ForegroundColor Cyan
            try {
                $response = Invoke-WebRequest -Uri "http://localhost/static/css/app.css" -Method Head -TimeoutSec 10
                if ($response.StatusCode -eq 200) {
                    Write-Host "✓ CSS acessível via HTTP (200 OK)" -ForegroundColor Green
                } else {
                    Write-Host "⚠️ CSS retornou código: $($response.StatusCode)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "⚠️ Não foi possível testar HTTP: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
        } else {
            Write-Host "✗ Falha no build Docker" -ForegroundColor Red
        }
        
    } else {
        Write-Host "⚠️ Docker Engine não está rodando" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "⚠️ Docker não encontrado ou não instalado" -ForegroundColor Yellow
}

Write-Host "=== Teste concluído ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para acessar a aplicação: http://localhost" -ForegroundColor Cyan
Write-Host "Para acessar CSS diretamente: http://localhost/static/css/app.css" -ForegroundColor Cyan
