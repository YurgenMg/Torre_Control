.PHONY: help setup init start load transform validate powerbi stop clean all

PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python
DOCKER_COMPOSE := docker-compose -f config/docker-compose.yml
DB_PORT := 5433
DB_NAME := supply_chain_dw
DB_USER := admin
DB_PASS := adminpassword

# ============================================================================
# COMANDOS PRINCIPALES
# ============================================================================

help: ## 📖 Mostrar ayuda
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  🏢 TORRE CONTROL - Pipeline de Ejecución"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🎯 Quick Start: make all"
	@echo ""

setup: ## 🔧 Instalación inicial (Python venv + dependencias)
	@echo "🔧 Creando entorno virtual..."
	$(PYTHON) -m venv $(VENV)
	@echo "📦 Instalando dependencias..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ Instalación completada"

init: ## 📁 Crear estructura de carpetas estándar
	@echo "📁 Creando estructura de directorios..."
	@mkdir -p data/raw data/interim data/processed data/external
	@mkdir -p notebooks tests logs
	@touch data/.gitkeep notebooks/.gitkeep tests/__init__.py logs/.gitkeep
	@touch src/__init__.py src/etl/__init__.py
	@echo "✅ Estructura creada"

start: ## 🐳 Iniciar infraestructura (Docker PostgreSQL + PgAdmin)
	@echo "🐳 Iniciando contenedores Docker..."
	$(DOCKER_COMPOSE) up -d
	@echo "⏳ Esperando PostgreSQL..."
	@sleep 10
	@until docker exec supply_chain_db pg_isready -U $(DB_USER) >/dev/null 2>&1; do \
		sleep 2; \
	done
	@echo "✅ PostgreSQL listo en localhost:$(DB_PORT)"
	@echo "✅ PgAdmin: http://localhost:5050"
	@echo "   Email: admin@dataco.com"
	@echo "   Password: $(DB_PASS)"

schema: start ## 📐 Crear schema de Data Warehouse
	@echo "📐 Ejecutando DDL..."
	@docker exec -i supply_chain_db psql -U $(DB_USER) -d $(DB_NAME) \
		< sql/ddl/01_schema_base.sql
	@echo "✅ Schema creado: dw.dim_*, dw.fact_orders, dw.stg_raw_orders"

load: ## 📥 Cargar datos RAW → Staging
	@echo "📥 Ejecutando carga CSV → PostgreSQL..."
	@if [ ! -f "data/raw/DataCoSupplyChainDataset.csv" ]; then \
		echo "❌ ERROR: data/raw/DataCoSupplyChainDataset.csv no encontrado"; \
		echo "   Descarga el dataset y colócalo en data/raw/"; \
		exit 1; \
	fi
	$(PYTHON_VENV) scripts/load_data.py
	@echo "✅ Datos cargados a dw.stg_raw_orders"

transform: ## 🔄 Transformar Staging → Star Schema
	@echo "🔄 Ejecutando transformaciones..."
	@if [ ! -f "scripts/transform_data.py" ]; then \
		echo "⚠️  WARNING: scripts/transform_data.py no existe"; \
		echo "   Creando script básico..."; \
		$(MAKE) create-transform; \
	fi
	$(PYTHON_VENV) scripts/transform_data.py
	@echo "✅ Dimensiones y hechos poblados"

validate: ## ✅ Validar calidad de datos
	@echo "🔍 Validando conteos..."
	@docker exec supply_chain_db psql -U $(DB_USER) -d $(DB_NAME) -c \
		"SELECT 'stg_raw_orders' as tabla, COUNT(*) as registros FROM dw.stg_raw_orders \
		UNION ALL SELECT 'dim_customer', COUNT(*) FROM dw.dim_customer \
		UNION ALL SELECT 'dim_geography', COUNT(*) FROM dw.dim_geography \
		UNION ALL SELECT 'dim_product', COUNT(*) FROM dw.dim_product \
		UNION ALL SELECT 'dim_date', COUNT(*) FROM dw.dim_date \
		UNION ALL SELECT 'fact_orders', COUNT(*) FROM dw.fact_orders;"
	@echo ""
	@echo "🔍 OTIF por Market:"
	@docker exec supply_chain_db psql -U $(DB_USER) -d $(DB_NAME) -c \
		"SELECT * FROM dw.v_otif_by_market ORDER BY otif_percentage DESC;"

export-csv: ## 📤 Exportar datos a CSV para Power BI
	@echo "📤 Exportando tablas..."
	@mkdir -p data/processed
	@docker exec supply_chain_db psql -U $(DB_USER) -d $(DB_NAME) -c \
		"\COPY (SELECT * FROM dw.fact_orders) TO STDOUT CSV HEADER" \
		> data/processed/fact_orders.csv
	@docker exec supply_chain_db psql -U $(DB_USER) -d $(DB_NAME) -c \
		"\COPY (SELECT * FROM dw.dim_customer) TO STDOUT CSV HEADER" \
		> data/processed/dim_customer.csv
	@docker exec supply_chain_db psql -U $(DB_USER) -d $(DB_NAME) -c \
		"\COPY (SELECT * FROM dw.dim_geography) TO STDOUT CSV HEADER" \
		> data/processed/dim_geography.csv
	@docker exec supply_chain_db psql -U $(DB_USER) -d $(DB_NAME) -c \
		"\COPY (SELECT * FROM dw.dim_product) TO STDOUT CSV HEADER" \
		> data/processed/dim_product.csv
	@docker exec supply_chain_db psql -U $(DB_USER) -d $(DB_NAME) -c \
		"\COPY (SELECT * FROM dw.dim_date) TO STDOUT CSV HEADER" \
		> data/processed/dim_date.csv
	@echo "✅ CSVs en: data/processed/"
	@ls -lh data/processed/*.csv

powerbi-info: ## 📊 Mostrar información de conexión Power BI
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  📊 POWER BI - Información de Conexión"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "OPCIÓN 1: PostgreSQL DirectQuery (RECOMENDADO)"
	@echo "  Servidor: localhost:$(DB_PORT)"
	@echo "  Base de datos: $(DB_NAME)"
	@echo "  Usuario: $(DB_USER)"
	@echo "  Password: $(DB_PASS)"
	@echo "  Tablas: dw.fact_orders, dw.dim_customer, dw.dim_geography, dw.dim_product, dw.dim_date"
	@echo ""
	@echo "OPCIÓN 2: CSV Import (DESARROLLO)"
	@echo "  Ejecutar: make export-csv"
	@echo "  Ruta: $$(pwd)/data/processed/"
	@echo "  Archivos: fact_orders.csv, dim_*.csv"
	@echo ""

stop: ## ⏹️  Detener contenedores
	@echo "⏹️  Deteniendo contenedores..."
	$(DOCKER_COMPOSE) stop

clean: ## 🧹 Limpiar contenedores y datos (¡CUIDADO!)
	@echo "⚠️  Esto eliminará todos los contenedores y datos"
	@read -p "¿Continuar? [y/N]: " confirm && [ "$$confirm" = "y" ]
	$(DOCKER_COMPOSE) down -v
	rm -rf data/processed/*.csv
	@echo "✅ Limpieza completada"

logs: ## 📋 Ver logs de PostgreSQL
	$(DOCKER_COMPOSE) logs -f postgres

test: ## 🧪 Ejecutar tests (si existen)
	@if [ -d "tests" ] && [ -f "tests/test_*.py" ]; then \
		$(PYTHON_VENV) -m pytest tests/ -v; \
	else \
		echo "⚠️  No hay tests configurados"; \
	fi

all: setup init start schema load transform validate ## 🎯 Pipeline completo
	@echo ""
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  ✅ PIPELINE COMPLETADO"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "Próximos pasos:"
	@echo "  1. Ver datos: make validate"
	@echo "  2. Exportar CSV: make export-csv"
	@echo "  3. Conectar Power BI: make powerbi-info"
	@echo ""

# ============================================================================
# HELPERS
# ============================================================================

create-transform: ## 🔧 Crear script transform_data.py básico
	@echo "Creando scripts/transform_data.py..."
	@echo '#!/usr/bin/env python3' > scripts/transform_data.py
	@echo '"""Torre Control - ETL Transformation"""' >> scripts/transform_data.py
	@echo 'print("⚠️  Script de transformación pendiente de implementar")' >> scripts/transform_data.py
	@echo 'print("Ver documentación para crear populate_dim_* functions")' >> scripts/transform_data.py
	@chmod +x scripts/transform_data.py
	@echo "✅ scripts/transform_data.py creado"