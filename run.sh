#!/bin/bash
# Torre Control - Quick Start Script

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════"
echo "  🏢 TORRE CONTROL - Quick Setup"
echo "═══════════════════════════════════════════════════════════"

# 1. Setup
echo "🔧 Instalando dependencias..."
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Infraestructura
echo "🐳 Iniciando Docker..."
docker-compose -f config/docker-compose.yml up -d
sleep 10

# 3. Schema
echo "📐 Creando schema..."
docker exec -i supply_chain_db psql -U admin -d supply_chain_dw < sql/ddl/01_schema_base.sql

# 4. Load
echo "📥 Cargando datos..."
python scripts/load_data.py

# 5. Validate
echo "✅ Validando..."
docker exec supply_chain_db psql -U admin -d supply_chain_dw -c \
    "SELECT COUNT(*) as total_rows FROM dw.stg_raw_orders;"

echo ""
echo "✅ Setup completado!"
echo "Conecta Power BI a: localhost:5433 / supply_chain_dw"
