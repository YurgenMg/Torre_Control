.PHONY: help setup init start schema load transform validate export powerbi-info backup stop clean logs refresh test all

# Variables de Configuración
PYTHON := python
VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python
DOCKER_COMPOSE := docker-compose -f config/docker-compose.yml
DB_HOST := localhost
DB_PORT := 5433
DB_NAME := supply_chain_dw
DB_USER := admin
DB_PASS := adminpassword

# Colores para output
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
RED := \033[0;31m
NC := \033[0m

# ============================================================================
# COMANDOS PRINCIPALES
# ============================================================================

help: ## 📖 Mostrar ayuda
	@echo "$(GREEN)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  🏢 TORRE CONTROL - Supply Chain Analytics$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "  $(BLUE)setup$(NC)               🔧 Instalar dependencias Python"
	@echo "  $(BLUE)init$(NC)                📁 Crear estructura de carpetas"
	@echo "  $(BLUE)start$(NC)               🐳 Iniciar PostgreSQL + PgAdmin"
	@echo "  $(BLUE)schema$(NC)              📋 Crear esquema DW"
	@echo "  $(BLUE)load$(NC)                📥 Cargar datos raw → staging"
	@echo "  $(BLUE)transform$(NC)           ⚙️  Transformar staging → Star Schema"
	@echo "  $(BLUE)validate$(NC)            ✅ Validar calidad de datos"
	@echo "  $(BLUE)export$(NC)              📤 Exportar CSV para Power BI"
	@echo "  $(BLUE)test$(NC)                🧪 Ejecutar tests unitarios"
	@echo "  $(BLUE)backup$(NC)              💾 Backup de PostgreSQL"
	@echo "  $(BLUE)stop$(NC)                🛑 Detener contenedores"
	@echo "  $(BLUE)clean$(NC)               🧹 Limpiar datos procesados"
	@echo "  $(BLUE)refresh$(NC)             🔄 Refresh completo (drop → load → transform)"
	@echo "  $(BLUE)all$(NC)                 🚀 Pipeline completo"
	@echo ""
	@echo "$(YELLOW)🎯 Quick Start:$(NC) make all"
	@echo ""

setup: ## 🔧 Instalar dependencias Python
	@echo "$(BLUE)📦 Instalando dependencias...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencias instaladas$(NC)"

init: ## 📁 Crear estructura estándar (Cookiecutter Data Science)
	@echo "$(BLUE)📁 Creando carpetas...$(NC)"
	@mkdir -p data/raw data/interim data/processed data/external
	@mkdir -p notebooks tests logs models
	@touch data/.gitkeep notebooks/.gitkeep tests/__init__.py logs/.gitkeep
	@touch src/__init__.py src/etl/__init__.py
	@echo "$(GREEN)✅ Estructura creada$(NC)"

start: ## 🐳 Iniciar PostgreSQL + PgAdmin (Docker)
	@echo "$(BLUE)🐳 Iniciando contenedores...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(YELLOW)⏳ Esperando PostgreSQL (10s)...$(NC)"
	@sleep 10
	@echo "$(GREEN)✅ PostgreSQL listo en $(DB_PORT)$(NC)"
	@echo "$(GREEN)✅ PgAdmin: http://localhost:5050$(NC)"

schema: start ## 📐 Crear schema DW (DDL completo)
	@echo "$(BLUE)📐 Ejecutando DDL...$(NC)"
	@docker exec -i supply_chain_db psql -U $(DB_USER) -d $(DB_NAME) \
		< sql/ddl/01_schema_base.sql
	@echo "$(GREEN)✅ Schema creado: dw.* tables$(NC)"

load: ## 📥 Cargar CSV → stg_raw_orders (PRODUCCIÓN)
	@echo "$(BLUE)📥 Ejecutando load_data.py...$(NC)"
	@if [ ! -f "Data/Raw/DataCoSupplyChainDataset.csv" ]; then \
		echo "$(RED)❌ Dataset no encontrado en Data/Raw/$(NC)"; \
		exit 1; \
	fi
	$(PYTHON) scripts/load_data.py
	@echo "$(GREEN)✅ Staging poblado$(NC)"

transform: ## 🔄 Transformar → Star Schema (USA SQL NATIVO)
	@echo "$(BLUE)🔄 Ejecutando transform_star_schema.py...$(NC)"
	$(PYTHON) scripts/transform_star_schema.py
	@echo "$(GREEN)✅ Star Schema poblado:$(NC)"
	@echo "   - dim_customer (38K)"
	@echo "   - dim_geography (213)"
	@echo "   - dim_product (98)"
	@echo "   - dim_date (1,127)"
	@echo "   - fact_orders (150K)"

validate: ## ✅ Validar calidad de datos
	@echo "$(BLUE)🔍 Validando DW...$(NC)"
	@$(PYTHON) scripts/validate_dw.py

export: ## 📤 Exportar CSV para Power BI (PostgreSQL → CSV)
	@echo "$(BLUE)📤 Exportando a Data/Processed/...$(NC)"
	@mkdir -p Data/Processed
	@$(PYTHON) src/etl/export_star_schema.py
	@echo "$(GREEN)✅ CSVs exportados:$(NC)"
	@ls -lh Data/Processed/*.csv 2>/dev/null || echo "   (ejecutar después de transform)"

powerbi-info: ## 📊 Info de conexión Power BI
	@echo ""
	@echo "$(GREEN)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  📊 POWER BI - Conexión DirectQuery$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "  Servidor:       $(DB_HOST):$(DB_PORT)"
	@echo "  Base de datos:  $(DB_NAME)"
	@echo "  Usuario:        $(DB_USER)"
	@echo "  Contraseña:     $(DB_PASS)"
	@echo "  Schema:         dw"
	@echo ""
	@echo "  Tablas:"
	@echo "    ✓ dw.fact_orders"
	@echo "    ✓ dw.dim_customer"
	@echo "    ✓ dw.dim_geography"
	@echo "    ✓ dw.dim_product"
	@echo "    ✓ dw.dim_date"
	@echo ""

backup: ## 💾 Crear backup PostgreSQL
	@echo "$(BLUE)💾 Creando backup...$(NC)"
	@mkdir -p backupsDocker
	$(DOCKER_COMPOSE) stop
	@echo "$(GREEN)✅ Contenedores detenidos$(NC)"

clean: ## 🧹 Limpiar todo (⚠️ DATOS BORRADOS)
	@echo "$(RED)⚠️  ¿Eliminar TODOS los datos? [y/N]:$(NC)" && read ans && [ $${ans:-N} = y ]
	$(DOCKER_COMPOSE) down -v
	rm -rf Data/Processed/*.csv logs/*.log
	@echo "$(GREEN)✅ Limpieza completada$(NC)"

logs: ## 📋 Ver logs PostgreSQL
	$(DOCKER_COMPOSE) logs -f postgres

test: ## 🧪 Ejecutar tests unitarios (pytest)
	@echo "$(BLUE)🧪 Ejecutando tests...$(NC)"
	$(PYTHON) -m pytest tests/test_etl.py -v --tb=short

refresh: load transform validate ## 🔄 Refresh ETL completo
	@echo "$(GREEN)✅ ETL Refresh completado$(NC)"

all: setup init start schema load transform validate ## 🎯 Pipeline completo
	@echo ""
	@echo "$(GREEN)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  ✅ PIPELINE COMPLETADO$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)Próximos pasos:$(NC)"
	@echo "  1. make export        → Generar CSVs"
	@echo "  2. make powerbi-info  → Ver conexión"
	@echo "  3. make backup        → Crear respaldo"
	@echo "  4. make test          → Ejecutar tests"
	@echo ""

.DEFAULT_GOAL := help
create-transform: ## 🔧 Crear script transform_data.py básico
	@echo "Creando scripts/transform_data.py..."
	@echo '#!/usr/bin/env python3' > scripts/transform_data.py
	@echo '"""Torre Control - ETL Transformation"""' >> scripts/transform_data.py
	@echo 'print("⚠️  Script de transformación pendiente de implementar")' >> scripts/transform_data.py
	@echo 'print("Ver documentación para crear populate_dim_* functions")' >> scripts/transform_data.py
	@chmod +x scripts/transform_data.py
	@echo "✅ scripts/transform_data.py creado"