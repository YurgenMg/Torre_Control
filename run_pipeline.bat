@echo off
REM Torre Control - Pipeline Execution Script for Windows
REM Este script ejecuta el pipeline completo sin necesidad de Make

echo.
echo ========================================================
echo   TORRE CONTROL - PIPELINE EXECUTION
echo ========================================================
echo.

REM Paso 1: Instalar dependencias
echo [1/5] Instalando dependencias Python...
pip install pandas sqlalchemy psycopg2-binary python-dotenv -q

REM Paso 2: Iniciar Docker
echo [2/5] Iniciando PostgreSQL...
docker-compose -f config/docker-compose.yml up -d

REM Paso 3: Esperar a que PostgreSQL est? listo
echo [3/5] Esperando a PostgreSQL...
timeout /t 5 /nobreak

REM Paso 4: Cargar datos
echo [4/5] Cargando datos RAW...
python scripts/load_data.py

REM Paso 5: Exportar a CSVs
echo [5/5] Exportando a CSVs...
python src/etl/export_star_schema.py

REM Verificar resultado
echo.
echo ========================================================
echo   PIPELINE COMPLETADO
echo ========================================================
echo.
echo Verificando datos en Data/Processed/:
dir Data\Processed\
echo.
echo Siguiente paso: Abrir Power BI
echo.
