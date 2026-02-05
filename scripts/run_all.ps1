# Torre Control - Pipeline Completo (Equivalente a 'make all')
# Ejecuta: load → transform → validate → export

Write-Host "`n🚀 EJECUTANDO PIPELINE COMPLETO DE TORRE CONTROL`n" -ForegroundColor Cyan

# 1. Load Data
Write-Host "📥 PASO 1/4: Cargando datos..." -ForegroundColor Yellow
python scripts/load_data.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error en load_data.py" -ForegroundColor Red
    exit 1
}

# 2. Transform (Star Schema)
Write-Host "`n⚙️  PASO 2/4: Transformando a Star Schema..." -ForegroundColor Yellow
python scripts/transform_star_schema.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error en transform_star_schema.py" -ForegroundColor Red
    exit 1
}

# 3. Validate
Write-Host "`n✅ PASO 3/4: Validando Data Warehouse..." -ForegroundColor Yellow
python scripts/validate_dw.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error en validate_dw.py" -ForegroundColor Red
    exit 1
}

# 4. Export for Power BI
Write-Host "`n📤 PASO 4/4: Exportando para Power BI..." -ForegroundColor Yellow
python scripts/export_for_powerbi.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error en export_for_powerbi.py" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ PIPELINE COMPLETADO EXITOSAMENTE`n" -ForegroundColor Green
Write-Host "📂 Archivos CSV disponibles en: Data/Processed/" -ForegroundColor Cyan
