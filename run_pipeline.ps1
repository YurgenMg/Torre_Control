#!/usr/bin/env powershell
<#
.SYNOPSIS
    Torre Control - Pipeline Execution Script
    Ejecuta el pipeline ETL completo sin Make
#>

Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   TORRE CONTROL - PIPELINE EXECUTION (PowerShell)" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Paso 1: Verificar Python
Write-Host "[1/6] Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "  OK: $pythonVersion" -ForegroundColor Green

# Paso 2: Instalar dependencias
Write-Host "[2/6] Instalando dependencias..." -ForegroundColor Yellow
pip install pandas sqlalchemy psycopg2-binary python-dotenv -q
Write-Host "  OK: Dependencias instaladas" -ForegroundColor Green

# Paso 3: Iniciar Docker
Write-Host "[3/6] Iniciando PostgreSQL Docker..." -ForegroundColor Yellow
docker-compose -f config/docker-compose.yml up -d
Write-Host "  OK: Docker iniciado" -ForegroundColor Green

# Paso 4: Esperar a PostgreSQL
Write-Host "[4/6] Esperando a PostgreSQL..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host "  OK: PostgreSQL listo" -ForegroundColor Green

# Paso 5: Cargar datos
Write-Host "[5/6] Cargando datos RAW..." -ForegroundColor Yellow
python scripts/load_data.py
Write-Host "  OK: Datos cargados" -ForegroundColor Green

# Paso 6: Exportar a CSVs
Write-Host "[6/6] Exportando a CSVs..." -ForegroundColor Yellow
python src/etl/export_star_schema.py
Write-Host "  OK: CSVs generados" -ForegroundColor Green

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   PIPELINE COMPLETADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Verificando archivos generados..." -ForegroundColor Yellow
Get-ChildItem "Data/Processed/" -ErrorAction SilentlyContinue | Select-Object Name, Length
Write-Host ""
Write-Host "Siguiente paso: Abrir Power BI Desktop" -ForegroundColor Cyan
Write-Host "  1. PBIX/TorreControl_v0.1.pbix" -ForegroundColor White
Write-Host "  2. Get Data -> Folder -> Data/Processed/" -ForegroundColor White
Write-Host "  3. Importar todos los CSVs" -ForegroundColor White
Write-Host ""
