# Instalar GNU Make en Windows usando Chocolatey
# IMPORTANTE: Ejecutar este script como ADMINISTRADOR

Write-Host "`n🔧 INSTALANDO GNU MAKE`n" -ForegroundColor Cyan

# Verificar si se está ejecutando como administrador
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  ADVERTENCIA: Este script necesita permisos de ADMINISTRADOR`n" -ForegroundColor Yellow
    Write-Host "Por favor:" -ForegroundColor White
    Write-Host "1. Cierra esta ventana" -ForegroundColor Gray
    Write-Host "2. Busca 'PowerShell' en el menú Inicio" -ForegroundColor Gray
    Write-Host "3. Click derecho → 'Ejecutar como administrador'" -ForegroundColor Gray
    Write-Host "4. Ejecuta: cd '$PWD'" -ForegroundColor Gray
    Write-Host "5. Ejecuta: .\install_make.ps1`n" -ForegroundColor Gray
    
    # Intentar relanzar como administrador
    Write-Host "Presiona Enter para intentar relanzar como administrador..." -ForegroundColor Cyan
    Read-Host
    Start-Process powershell -Verb RunAs -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\install_make.ps1"
    exit
}

Write-Host "✅ Ejecutando como administrador`n" -ForegroundColor Green

# Verificar Chocolatey
Write-Host "📦 Verificando Chocolatey..." -ForegroundColor Yellow
$chocoVersion = choco --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Chocolatey no encontrado. Instalando...`n" -ForegroundColor Red
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString("https://community.chocolatey.org/install.ps1"))
    Write-Host "`n✅ Chocolatey instalado: $(choco --version)" -ForegroundColor Green
}
else {
    Write-Host "✅ Chocolatey ya instalado: $chocoVersion`n" -ForegroundColor Green
}

# Instalar make
Write-Host "🔧 Instalando GNU Make..." -ForegroundColor Yellow
choco install make -y

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ GNU Make instalado exitosamente!`n" -ForegroundColor Green
    
    # Verificar instalación
    refreshenv
    $makePath = (Get-Command make -ErrorAction SilentlyContinue).Source
    if ($makePath) {
        Write-Host "📍 Ubicación: $makePath" -ForegroundColor Cyan
        Write-Host "📌 Versión: $(make --version | Select-Object -First 1)" -ForegroundColor Cyan
    }
    else {
        Write-Host "⚠️  Make instalado pero no disponible en esta sesión" -ForegroundColor Yellow
        Write-Host "   Cierra y abre una nueva terminal PowerShell`n" -ForegroundColor Gray
    }
    
    Write-Host "`n🎯 Ahora puedes usar comandos como:" -ForegroundColor Cyan
    Write-Host "   make validate" -ForegroundColor White
    Write-Host "   make transform" -ForegroundColor White
    Write-Host "   make test" -ForegroundColor White
    Write-Host "   make all`n" -ForegroundColor White
}
else {
    Write-Host "`n❌ Error durante la instalación" -ForegroundColor Red
    Write-Host "   Verifica tu conexión a internet y vuelve a intentar`n" -ForegroundColor Yellow
}

Write-Host "Presiona Enter para cerrar..." -ForegroundColor Gray
Read-Host
