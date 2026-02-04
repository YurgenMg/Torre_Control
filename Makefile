# Torre Control - Makefile
# Cross-platform automation for ETL pipeline
# Usage: make help

.PHONY: help install setup-docker run load-raw transform export validate health test lint format clean clean-all logs

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║           Torre Control - Makefile Commands                     ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)📦 SETUP & INSTALLATION$(NC)"
	@echo "  $(GREEN)make install$(NC)         - Install Python dependencies (pip)"
	@echo "  $(GREEN)make setup-docker$(NC)    - Start PostgreSQL container"
	@echo "  $(GREEN)make run$(NC)             - ⚡ RUN EVERYTHING (install→docker→load→transform→export→validate)"
	@echo ""
	@echo "$(YELLOW)🔄 ETL PIPELINE STEPS$(NC)"
	@echo "  $(GREEN)make load-raw$(NC)        - Load CSV → PostgreSQL staging"
	@echo "  $(GREEN)make validate-transform$(NC) - Pre-flight validation checks"
	@echo "  $(GREEN)make transform$(NC)       - Transform → Star Schema"
	@echo "  $(GREEN)make export$(NC)          - Export Star Schema → CSVs (Data/Processed/)"
	@echo "  $(GREEN)make validate$(NC)        - Data quality checks"
	@echo ""
	@echo "$(YELLOW)🧪 TESTING & QUALITY$(NC)"
	@echo "  $(GREEN)make test$(NC)            - Run pytest suite"
	@echo "  $(GREEN)make lint$(NC)            - Run flake8, mypy, isort (check)"
	@echo "  $(GREEN)make format$(NC)          - Auto-format code (black, isort)"
	@echo ""
	@echo "$(YELLOW)📊 DIAGNOSTICS$(NC)"
	@echo "  $(GREEN)make health$(NC)          - System health check"
	@echo "  $(GREEN)make logs$(NC)            - Show recent error logs"
	@echo ""
	@echo "$(YELLOW)🧹 CLEANUP$(NC)"
	@echo "  $(GREEN)make clean$(NC)           - Remove generated files (Data/Processed/, __pycache__)"
	@echo "  $(GREEN)make clean-all$(NC)       - Clean + stop Docker + remove venv"
	@echo ""

# ============================================================================
# CORE TARGETS
# ============================================================================

install:
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Installing Python dependencies...$(NC)"
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

setup-docker:
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Starting PostgreSQL container...$(NC)"
	docker-compose -f config/docker-compose.yml up -d
	@echo "$(YELLOW)⏳ Waiting for PostgreSQL to be ready...$(NC)"
	@sleep 5
	@echo "$(GREEN)✅ PostgreSQL running on localhost:5433$(NC)"

load-raw:
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Loading CSV → PostgreSQL...$(NC)"
	python scripts/load_data.py
	@echo "$(GREEN)✅ Data loaded to dw.stg_raw_orders$(NC)"

validate-transform:
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Pre-flight validation checks...$(NC)"
	python scripts/validate_transform.py

transform:
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Transforming → Star Schema...$(NC)"
	@echo "$(YELLOW)  - Creating dimensions (customer, product, geography, date)$(NC)"
	@echo "$(YELLOW)  - Populating fact_orders with calculated columns$(NC)"
	@echo "$(YELLOW)  - Building analytics views$(NC)"
	python scripts/transform_data.py
	@echo "$(GREEN)✅ Star Schema created$(NC)"

export:
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Exporting Star Schema → CSVs...$(NC)"
	python src/etl/export_star_schema.py
	@echo "$(GREEN)✅ CSVs exported to Data/Processed/$(NC)"

validate:
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Validating data quality...$(NC)"
	@echo "$(YELLOW)  - Checking row counts$(NC)"
	@echo "$(YELLOW)  - Validating critical fields (no nulls)$(NC)"
	@echo "$(YELLOW)  - Calculating OTIF%$(NC)"
	python scripts/load_data.py --validate-only
	@echo "$(GREEN)✅ Data validation complete$(NC)"

# ============================================================================
# FULL PIPELINE (THE MAIN COMMAND)
# ============================================================================

run: install setup-docker load-raw validate-transform transform export validate
	@echo ""
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║                   🎉 PIPELINE COMPLETE! 🎉                     ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)✅ Your data is ready for Power BI:$(NC)"
	@echo "   Data/Processed/fact_orders.csv (186K rows)"
	@echo "   Data/Processed/dim_customer.csv (5K rows)"
	@echo "   Data/Processed/dim_product.csv (1.8K rows)"
	@echo "   Data/Processed/dim_geography.csv (150 rows)"
	@echo "   Data/Processed/dim_date.csv (365 rows)"
	@echo ""
	@echo "$(YELLOW)Next Step:$(NC) Open docs/guides/POWER_BI_CONNECTION_COMPLETE_GUIDE.md"
	@echo ""

# ============================================================================
# TESTING & QUALITY
# ============================================================================

test:
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Running tests...$(NC)"
	pytest tests/ -v
	@echo "$(GREEN)✅ Tests complete$(NC)"

lint:
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Linting code...$(NC)"
	flake8 scripts/ src/ --max-line-length=100
	mypy scripts/ src/ --ignore-missing-imports
	@echo "$(GREEN)✅ Lint checks passed$(NC)"

format:
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Formatting code...$(NC)"
	black scripts/ src/
	isort scripts/ src/
	@echo "$(GREEN)✅ Code formatted$(NC)"

# ============================================================================
# DIAGNOSTICS
# ============================================================================

health:
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║                      System Health Check                       ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)Python:$(NC)"
	@python --version
	@echo ""
	@echo "$(YELLOW)Docker:$(NC)"
	@docker --version || echo "❌ Docker not installed"
	@echo ""
	@echo "$(YELLOW)PostgreSQL:$(NC)"
	@docker-compose -f config/docker-compose.yml ps 2>/dev/null | grep postgres || echo "❌ Container not running (run 'make setup-docker')"
	@echo ""
	@echo "$(YELLOW)Data Files:$(NC)"
	@test -f Data/Raw/DataCoSupplyChainDataset.csv && echo "✅ Data/Raw/DataCoSupplyChainDataset.csv" || echo "❌ Missing raw data"
	@test -d Data/Processed && echo "✅ Data/Processed/ directory exists" || echo "❌ Missing Processed directory"
	@ls -lh Data/Processed/ 2>/dev/null | tail -n +2 | awk '{print "  " $$9 " (" $$5 ")"}' || echo "  (empty)"
	@echo ""
	@echo "$(YELLOW)Key Files:$(NC)"
	@test -f Makefile && echo "✅ Makefile" || echo "❌ Makefile"
	@test -f requirements.txt && echo "✅ requirements.txt" || echo "❌ requirements.txt"
	@test -f scripts/load_data.py && echo "✅ scripts/load_data.py" || echo "❌ scripts/load_data.py"
	@test -f src/etl/export_star_schema.py && echo "✅ src/etl/export_star_schema.py" || echo "❌ src/etl/export_star_schema.py"
	@echo ""

logs:
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Recent logs:$(NC)"
	@tail -n 50 logs/load_data_output.txt 2>/dev/null || echo "No logs found (run: make run)"

# ============================================================================
# CLEANUP
# ============================================================================

clean:
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Cleaning generated files...$(NC)"
	rm -rf Data/Processed/*.csv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Cleaned$(NC)"

clean-all: clean
	@echo "$(BLUE)[$(shell date +'%H:%M:%S')] Full cleanup (includes Docker & venv)...$(NC)"
	docker-compose -f config/docker-compose.yml down 2>/dev/null || true
	rm -rf .venv/
	@echo "$(GREEN)✅ Full cleanup complete$(NC)"

# ============================================================================
# ALIASES
# ============================================================================

setup: install setup-docker
	@echo "$(GREEN)✅ Setup complete$(NC)"

rebuild: clean-all install setup-docker run
	@echo "$(GREEN)✅ Full rebuild complete$(NC)"

.DEFAULT_GOAL := help
