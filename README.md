# 🏢 TORRE CONTROL - Supply Chain Analytics Platform

**Build a Centralized Intelligence Hub for Global Logistics**

## 🎯 Mission

Transform DataCo Global's fragmented ERP data into a **real-time operational intelligence platform** that enables executive decision-making across supply chain, finance, and operations.

**The Problem We Solve:**
- ❌ Sales, shipping, and customer data live in silos
- ❌ No single source of truth for delivery performance (OTIF)
- ❌ Logistics costs spiraling with zero visibility
- ❌ Customer churn rising due to unreliable delivery

**The Solution:**
- ✅ Centralized data warehouse (star schema) from legacy ERP
- ✅ Real-time Power BI dashboards answering 5 strategic questions
- ✅ Predictive models for late delivery risk
- ✅ Actionable insights for executives (COO, CFO, CMO)

---

## 📊 The 5 Strategic Questions (KPIs)

Every analysis radiates from these 5 executive imperatives:

| # | Question | Metric | Impact |
|---|----------|--------|--------|
| **Q1** | **Visibility of Service:** What is our real OTIF%? Where are we failing? | OTIF% by Market/Region | Renegotiate carrier contracts |
| **Q2** | **Revenue at Risk:** How much $ are we losing to late deliveries? | Revenue at Risk ($) by Segment | Prioritize high-value routes |
| **Q3** | **Churn Risk:** Which Top 10% customers will defect? | VIP Customers + 2 Late Orders | Proactive retention calls |
| **Q4** | **Geographic Efficiency:** Are there "Black Holes" in our network? | OTIF% by Market → Region → City | Close unprofitable routes |
| **Q5** | **Fraud & Anomalies:** How much inventory are we losing? | Loss ($) by Order Status | Internal audit, reduce shrinkage |

---

## 📁 Project Structure

```
Proyecto_TorreContol/
├── 📊 Data/
│   ├── Raw/                              (Never modify)
│   │   ├── DataCoSupplyChainDataset.csv  (100K+ orders, 54 fields)
│   │   ├── DescriptionDataCoSupplyChain.csv (Data dictionary)
│   │   └── tokenized_access_logs.csv
│   │
│   └── Processed/                        (ETL output → Power BI input)
│       ├── etl_pipeline.py               (Main orchestrator - BUILD THIS)
│       ├── data_ingestion.py
│       ├── data_transformation.py
│       ├── data_validation.py
│       ├── feature_engineering.py
│       ├── dim_customer.csv              (Customer dimension)
│       ├── dim_product.csv               (Product dimension)
│       ├── dim_geography.csv             (Location hierarchy)
│       ├── dim_date.csv                  (Time dimension)
│       └── fact_orders.csv               (Order transactions - core fact table)
│
├── 📈 PBIX/                              (Power BI Dashboards)
│   ├── TorreControl_v0.1.pbix            (Main dashboard - 5 views)
│   └── Emoticones/                       (Custom icons & branding)
│
├── 📚 Documentation/
│   ├── .github/copilot-instructions.md   (AI agent guide)
│   ├── CONTEXTO_ESTRATEGICO.md           (Deep business context)
│   └── README.md                         (This file)
│
└── .gitignore
```

---

## 🚀 Quick Start

### Prerequisites

#### System Requirements
- **Python 3.9+** (with pip)
- **Docker Desktop** (for PostgreSQL database)
- **VS Code** with recommended extensions (see `.vscode/extensions.json`)
- **Git** (for version control)

#### Installation

**Step 1: Clone the Repository**
```bash
git clone https://github.com/YurgenMg/Torre_Control.git
cd Torre_Control
```

**Step 2: Install Dependencies**
```bash
# Install core dependencies
make install

# Or install with development tools
make install-dev
```

**Step 3: Configure Environment**
```bash
# Copy example configuration
cp config/.env.example .env

# Edit .env with your settings (optional)
# Default values work for local development
```

**Step 4: Start Database**
```bash
# Start PostgreSQL container
make setup-docker
```

**Step 5: Run ETL Pipeline**
```bash
# Option 1: Run new modular pipeline (RECOMMENDED)
make run-etl

# Option 2: Run legacy pipeline
make run
```

**Step 6: Export for Power BI**
```bash
# Export data in Parquet format
make export-powerbi
```

---

## 🏗️ Production-Ready Architecture

### New Modular Structure (2026 Refactoring)

```
Torre_Control/
├── src/
│   ├── config.py                    # ✨ Pydantic settings management
│   ├── logging_config.py            # ✨ Centralized logging
│   └── etl/
│       ├── extract.py               # ✨ DataExtractor class
│       ├── transform.py             # ✨ DataTransformer class
│       ├── load.py                  # ✨ DataLoader class
│       ├── validate.py              # ✨ DataValidator class
│       └── utils.py                 # ✨ Helper functions
│
├── scripts/
│   ├── run_etl.py                   # ✨ ETL orchestrator
│   ├── export_for_powerbi.py        # ✨ Parquet export utility
│   ├── load_data.py                 # Legacy: CSV loading
│   └── transform_data.py            # Legacy: Transformation
│
├── tests/
│   ├── conftest.py                  # ✨ Pytest fixtures
│   ├── test_extract.py              # ✨ Extraction tests
│   ├── test_transform.py            # ✨ Transformation tests
│   └── test_validate.py             # ✨ Validation tests
│
├── docs/
│   ├── POWERBI_GUIDE.md             # ✨ Power BI connection guide
│   └── guides/                      # Additional documentation
│
├── data/
│   ├── raw/                         # Source CSV files (gitignored)
│   └── processed/                   # Exported Parquet/CSV (gitignored)
│
├── config/
│   ├── .env.example                 # Environment configuration template
│   └── docker-compose.yml           # PostgreSQL container setup
│
├── Makefile                         # ✨ Updated automation commands
├── requirements.txt                 # ✨ Updated core dependencies
├── requirements-dev.txt             # ✨ Development dependencies
└── .env                             # Local configuration (gitignored)
```

✨ = New/Updated in 2026 refactoring

### Key Improvements

#### 1. **Configuration Management**
- **Pydantic v2** settings with validation
- **Environment variables** via `.env` file
- **Type-safe** configuration access

```python
from src.config import get_settings

settings = get_settings()
db_url = settings.database_url  # Type-safe, validated
```

#### 2. **Centralized Logging**
- **Consistent** logging across all modules
- **File and console** handlers
- **Execution time** tracking decorator

```python
from src.logging_config import get_logger, log_execution_time

logger = get_logger(__name__)

@log_execution_time
def my_function():
    logger.info("Processing data...")
```

#### 3. **Modular ETL Components**
- **Separation of concerns**: Extract, Transform, Load, Validate
- **Reusable classes** with dependency injection
- **Testable** design with mocks/fixtures

```python
from src.etl.extract import DataExtractor
from src.etl.load import DataLoader
from src.etl.transform import DataTransformer

extractor = DataExtractor()
loader = DataLoader()
transformer = DataTransformer(loader=loader)

df = extractor.extract_and_sanitize()
loader.load_dataframe(df, "staging_table", schema="dw")
transformer.transform_all()
```

#### 4. **Power BI Integration**
- **Parquet export** for 10-50x faster loading
- **DirectQuery support** for real-time dashboards
- **Comprehensive guide** at `docs/POWERBI_GUIDE.md`

```bash
# Export optimized Parquet files
make export-powerbi

# Export specific tables
python scripts/export_for_powerbi.py --tables dim_customer,fact_orders
```

#### 5. **Testing Infrastructure**
- **Pytest** with fixtures and markers
- **Unit and integration** tests
- **Database mocking** for isolation

```bash
# Run all tests
make test

# Run only unit tests
pytest -m unit

# Run with coverage
pytest --cov=src --cov-report=html
```

---

## 📋 Available Commands

### ETL Pipeline
```bash
make run-etl              # Run new modular ETL pipeline
make export-powerbi       # Export data for Power BI (Parquet)
make run                  # Run legacy pipeline (backwards compatible)
```

### Development
```bash
make install              # Install core dependencies
make install-dev          # Install development dependencies
make test                 # Run test suite
make lint                 # Run code quality checks
make format               # Auto-format code
```

### Database
```bash
make setup-docker         # Start PostgreSQL container
make health               # Check system health
make logs                 # View recent logs
```

### Cleanup
```bash
make clean                # Remove generated files
make clean-all            # Full cleanup (includes Docker)
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_extract.py

# Run only unit tests
pytest -m unit

# Run with coverage report
pytest --cov=src --cov-report=html

# Skip slow tests
pytest -m "not slow"

# Skip database tests
pytest -m "not database"
```

---

## 📊 Power BI Integration

### Quick Start

1. **Run ETL Pipeline**
```bash
make run-etl
```

2. **Export Data**
```bash
make export-powerbi
```

3. **Connect Power BI**
   - Open Power BI Desktop
   - Get Data → Folder
   - Select `data/processed/` directory
   - Load Parquet files

4. **Create Relationships**
   - fact_orders → dim_customer (customer_id)
   - fact_orders → dim_product (product_card_id)
   - fact_orders → dim_geography (geography_key)
   - fact_orders → dim_date (date_key)

For detailed instructions, see **[Power BI Connection Guide](docs/POWERBI_GUIDE.md)**

---

## 🛠️ Configuration

### Environment Variables

Edit `.env` file to customize configuration:

```bash
# PostgreSQL Configuration
POSTGRES_USER=admin
POSTGRES_PASSWORD=adminpassword
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=supply_chain_dw

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# Data Loading Configuration
CSV_FILE_PATH=data/raw/DataCoSupplyChainDataset.csv
BATCH_SIZE=1000

# Analytics Configuration
OTIF_TARGET=95
REVENUE_AT_RISK_THRESHOLD=1000000
CHURN_RISK_LTV_THRESHOLD=50000
```

---

## 📚 Documentation

- **[Power BI Guide](docs/POWERBI_GUIDE.md)** - Complete Power BI integration
- **[ETL Pipeline Guide](docs/guides/ETL_COMPLETE_PIPELINE.md)** - ETL architecture
- **[Setup Guide](docs/guides/SETUP_GUIDE.md)** - Detailed setup instructions
- **[Strategic Context](docs/guides/CONTEXTO_ESTRATEGICO.md)** - Business context

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 🎯 Success Metrics

After running the pipeline, you should see:

✅ **Data Quality**
- OTIF% calculated (target: >95%)
- Revenue at risk identified
- VIP customers at risk flagged
- Geographic performance analyzed

✅ **Technical**
- All tests passing
- Logs generated in `logs/etl.log`
- Parquet files exported to `data/processed/`
- Star schema populated in PostgreSQL

✅ **Power BI Ready**
- 5 dimension tables exported
- 1 fact table with 186K+ rows
- Relationships documented
- DAX measures provided

---

## 🆘 Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'pydantic'`
```bash
# Solution: Install dependencies
make install
```

**Issue:** `Connection to PostgreSQL failed`
```bash
# Solution: Start Docker container
make setup-docker

# Check if running
docker ps | grep postgres
```

**Issue:** `CSV file not found`
```bash
# Solution: Ensure raw data exists
ls data/raw/DataCoSupplyChainDataset.csv
```

**Issue:** `Tests failing`
```bash
# Solution: Install development dependencies
make install-dev

# Run tests with verbose output
pytest tests/ -v
```

For more issues, see [GitHub Issues](https://github.com/YurgenMg/Torre_Control/issues).

---

**Built with ❤️ by the Torre Control Engineering Team**

**macOS/Linux (Bash):**
```bash
cd Proyecto_TorreContol
chmod +x scripts/setup.sh
./scripts/setup.sh
./scripts/health-check.sh
```

### Architecture Overview

```
┌─────────────────────────────────────────────┐
│ Raw Data (data/raw/)                        │
│ • DataCoSupplyChainDataset.csv              │
│ • DescriptionDataCoSupplyChain.csv          │
└─────────────────────────────────────────────┘
           ⬇️ ETL Pipeline
┌─────────────────────────────────────────────┐
│ PostgreSQL Data Warehouse (Docker)          │
│ • Schema: dw                                │
│ • Tables: dim_*, fact_orders, stg_*         │
│ • Views: v_otif_*, v_revenue_*, v_fraud_*   │
└─────────────────────────────────────────────┘
           ⬇️ SQL Queries
┌─────────────────────────────────────────────┐
│ VS Code + SQLTools (Analysis)               │
│ • Q1-Q5 Strategic Question Queries          │
│ • Real-time data exploration                │
└─────────────────────────────────────────────┘
           ⬇️ Power BI
┌─────────────────────────────────────────────┐
│ PBIX/TorreControl_v0.1.pbix (Dashboards)    │
│ • 5 Executive Views                         │
│ • Drill-down hierarchies                    │
│ • Interactive slicers                       │
└─────────────────────────────────────────────┘
```

### Access Points

**PostgreSQL Database (via SQLTools in VS Code):**
- Connection: `Torre Control - Local Dev`
- Host: `localhost:5432`
- Database: `supply_chain_dw`
- Username: `admin`
- Password: `adminpassword`

**PgAdmin (Web UI):**
- URL: http://localhost:5050
- Email: `admin@dataco.com`
- Password: `adminpassword`

### Phase 1: Explore Data Warehouse

1. **Open VS Code** in project root
2. **Install SQLTools extension** (if not already done)
3. **Connect to database** using saved connection
4. **Browse schema** (dw schema in supply_chain_dw database)
5. **Run queries** from `sql/queries/q1_q5_strategic_questions.sql`

**Example: Check OTIF**
```sql
-- Run this in SQLTools
SELECT * FROM dw.v_otif_by_market;
```

### Phase 2: Load CSV Data to Database

Create a Python script in `scripts/load_data.py`:
```python
import pandas as pd
import sqlalchemy as sa

# Read raw CSV
df = pd.read_csv('data/raw/DataCoSupplyChainDataset.csv')

# Connect to database
engine = sa.create_engine(
    'postgresql://admin:adminpassword@localhost:5432/supply_chain_dw'
)

# Insert into staging table
df.to_sql('stg_raw_orders', con=engine, schema='dw', 
          if_exists='append', index=False)

print(f"✅ Loaded {len(df)} rows into stg_raw_orders")
```

Then run:
```bash
python scripts/load_data.py
```

### Phase 3: Transform & Load to Fact/Dimension Tables

Create a Python script in `scripts/transform_data.py` that:
1. Reads from `dw.stg_raw_orders`
2. Creates dimension records
3. Creates fact records
4. Marks data as processed

### Phase 4: Load to Power BI
1. Open `PBIX/TorreControl_v0.1.pbix`
2. Data source → New connection (PostgreSQL)
3. Connect to `localhost:5432 / supply_chain_dw`
4. Import tables: fact_orders, dim_*
5. Establish relationships
6. Refresh (Data → Refresh)

### Phase 5: Validate Dashboards
- Check 5 views operational
- Verify drill-down (Market → Region → State → City)
- Test slicers (Date, Segment, Market)

---

## 🎯 Key Metrics & Formulas

### OTIF (On-Time In-Full)
```
On-Time:  Days for shipping (real) ≤ Days for shipment (scheduled)
In-Full:  Delivery Status NOT IN ('Canceled', 'Suspected Fraud')

OTIF% = (On-Time ✓ AND In-Full ✓) / Total Orders × 100
```

### Revenue at Risk
```
Revenue at Risk = SUM(Sales) WHERE Late_delivery_risk = 1
Revenue at Risk % = Revenue_at_Risk / Total_Revenue × 100
```

### Churn Risk Score
```
VIP Customers at Risk = 
  WHERE Sales_per_Customer in Top 10% (by LTV)
  AND Last_2_Orders.Late_delivery_risk = [1, 1]
  
Churn Risk = (Avg_Days_Late × Frequency) / LTV
```

### Delivery Delay Ratio
```
Delay_Ratio = Days for shipping (real) / Days for shipment (scheduled)
Expected: < 1.0 (on time), > 1.0 (late)
```

---

## 🔍 Data Quality Standards

Before any analysis, validate:

✅ **No Nulls in Critical Fields**
```
Late_delivery_risk, Days for shipping (real), Customer ID, Order ID, Sales
```

✅ **Outlier Detection**
```
Days for shipping (real) > 60 days    → Flag as anomaly
Order Item Discount Rate > 100%       → Impossible, mark fraud
Sales < $0                             → Negative revenue
```

✅ **Geographic Consistency**
```
Market ∈ [Africa, Europe, LATAM, Pacific Asia, USCA]
Region ∈ [20+ valid values]
State/City must have valid parent market
```

✅ **Cross-Field Validation**
```
IF Late_delivery_risk = 1 THEN Days_real > Days_scheduled
IF Delivery_Status = 'Canceled' THEN Sales may be $0
IF Order_Status = 'SUSPECTED_FRAUD' THEN investigate discount_rate
```

---

## 📋 Deliverables Checklist

### ✅ Phase 1: Foundation (Weeks 1-3)
- [ ] ETL pipeline operational
- [ ] Star schema modeled (4 dims + 1 fact)
- [ ] Data quality checks passing
- [ ] All processed CSVs generated
- [ ] Field mappings documented

### ✅ Phase 2: Dashboarding (Weeks 4-6)
- [ ] Power BI data model refreshed
- [ ] 5 executive views built
- [ ] Slicers & filters working
- [ ] Drill-down hierarchies functional
- [ ] Auto-refresh scheduled

### ✅ Phase 3: Advanced Analytics (Weeks 7+)
- [ ] Predictive model (Late delivery risk)
- [ ] Scenario planning implemented
- [ ] Automated alerts configured
- [ ] Executive training completed

---

## 🧠 Design Philosophy

### 1. **Market Dimension is Core**
The project deliberately organizes around geography because:
- Regional logistics vary dramatically (Africa ≠ Europe)
- Drill-down: Market → Region → State → City enables root cause analysis
- Decision point: "Should we adjust SLAs for West Africa specifically?"

### 2. **OTIF is Non-Negotiable**
- Both conditions must be TRUE: On-Time AND In-Full
- Calculate at every drill-level (global, market, region, city, product, segment)
- Single audit trail: If OTIF = 85%, why? Drill until you find root cause.

### 3. **Revenue Speaks Louder Than Count**
- Executive question: "Are late orders $10 or $500?" (not just "how many")
- Weight metrics by sales value, not just frequency
- VIP customer = high LTV, highest churn risk if service degrades

### 4. **Single Source of Truth**
- All 5 questions answered from same fact table (fact_orders)
- No Excel silos, no conflicting numbers
- One data owner (Data Analyst), one refresh schedule

---

## 🔗 Dependencies & Integration Points

### External Dependencies
- **Data Source:** Legacy ERP exports (CSV)
- **BI Tool:** Microsoft Power BI Desktop / Service
- **Schedule:** ETL runs daily @ 2 AM UTC (configurable)

### Internal Dependencies
- `DescriptionDataCoSupplyChain.csv` is the field definition authority
- Power BI refresh depends on processed CSV availability
- Geographic validation must precede any dashboard publication

---

## 📖 Documentation Hierarchy

| Document | Purpose | Audience |
|----------|---------|----------|
| **README.md** (this) | Project overview, quick start | Everyone |
| **.github/copilot-instructions.md** | AI agent development guide | Developers, AI |
| **CONTEXTO_ESTRATEGICO.md** | Deep business case, 5 Qs explained | Executives, Analysts |
| **Data/Processed/etl_pipeline.py** | Implementation details | Engineers |
| **PBIX/TorreControl_v0.1.pbix** | Live dashboard | End Users |

---

## 🚨 Common Pitfalls (Avoid!)

| ❌ Pitfall | ✅ Solution |
|-----------|-----------|
| Building beautiful dashboards without solving the 5 Qs | Every viz must answer one of the 5 strategic questions |
| Analyzing data at global level only | Drill down to region/city (regional patterns differ) |
| Ignoring Late_delivery_risk vs Delivery_Status discrepancies | Cross-validate; document mismatches |
| Using simple averages instead of weighted by value | Weight by Sales (high-value orders matter more) |
| Not validating geographic/market data consistency | Validate market list at ETL time, before dashboard |
| Forgetting OTIF = On-Time AND In-Full (both true) | Code: `otif_flag = (days_real ≤ days_scheduled) & (status != 'Canceled')` |

---

## 💬 Support & Questions

**For Development Issues:**
- See `.github/copilot-instructions.md`

**For Business Context:**
- See `CONTEXTO_ESTRATEGICO.md`

**For Data Definitions:**
- See `Data/Raw/DescriptionDataCoSupplyChain.csv`

---

## 📊 Success Metrics

**We'll know we've succeeded when:**

1. ✅ **COO has dashboard open daily** - Using it to make real decisions
2. ✅ **OTIF visibility improves** - From unknown → 85% (tracked by region)
3. ✅ **Revenue at Risk decreases** - From $2.3M → < $1.5M
4. ✅ **VIP retention improves** - Proactive outreach saves at-risk accounts
5. ✅ **Operational costs optimize** - Logistics investments directed to problem areas
6. ✅ **Fraud detection improves** - Loss ($) from anomalies investigated & reduced

---

## 📅 Timeline

| Phase | Duration | Goal | Owner |
|-------|----------|------|-------|
| **Phase 1** | Weeks 1-3 | Single Source of Truth | Data Engineer |
| **Phase 2** | Weeks 4-6 | Executive Dashboards Live | BI Developer |
| **Phase 3** | Weeks 7+ | Predictive Intelligence | Data Scientist |

---

## 🎓 Learning Resources

- **Star Schema Design:** "The Data Warehouse Toolkit" (Ralph Kimball)
- **Power BI Best Practices:** Microsoft Power BI Documentation
- **Supply Chain Metrics:** "Supply Chain Metrics That Matter" (APICS)
- **Data Quality:** "Fundamentals of Data Quality Management" (DAMA)

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-02-02 | Initial project setup, 5 strategic questions defined |
| 0.2 | TBD | ETL pipeline implemented, processed data available |
| 0.3 | TBD | Power BI dashboards operational |
| 1.0 | TBD | Full production deployment |

---

**Last Updated:** 2 de Febrero de 2026  
**Project Lead:** Your Name  
**Status:** 🔨 Foundation Phase (Building ETL)

---

*"We're not building dashboards. We're solving operational blindness."*
