# Torre Control - ETL Pipeline Architecture

## 📋 Production Pipeline

**Automated ETL workflow for Supply Chain Analytics**

```
┌─────────────────────────────────────────────────────────────┐
│                    ETL PIPELINE V2.0                        │
│              (SQL-based transformation)                     │
└─────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │  Raw Data    │  DataCoSupplyChainDataset.csv (180K records)
  │  (CSV files) │
  └──────┬───────┘
         │
         │ python scripts/load_data.py
         ▼
  ┌──────────────────┐
  │  Staging Layer   │  dw.stg_raw_orders (50K records)
  │  PostgreSQL DB   │  - Raw data ingestion
  └──────┬───────────┘  - Basic data types
         │
         │ python scripts/transform_star_schema.py
         │ (executes sql/populate_star_schema_simple.sql)
         ▼
  ┌────────────────────────────────────────────────┐
  │           Star Schema (Kimball)                │
  ├────────────────────────────────────────────────┤
  │  Dimensions:                                   │
  │    • dim_customer   (50K records)              │
  │    • dim_geography  (259 locations)            │
  │    • dim_product    (196 products)             │
  │    • dim_date       (1,127 dates)              │
  │                                                 │
  │  Facts:                                        │
  │    • fact_orders    (950K transactions)        │
  └────────────────┬───────────────────────────────┘
                   │
                   │ Power BI Connector
                   ▼
  ┌────────────────────────────────────────────────┐
  │         Power BI Dashboard                     │
  │  - OTIF Performance                            │
  │  - Revenue at Risk                             │
  │  - VIP Churn Analysis                          │
  │  - Geographic Heatmap                          │
  │  - Anomaly Detection                           │
  └────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Load Raw Data to Staging
```bash
python scripts/load_data.py
```
**Output:** 50,000 records in `dw.stg_raw_orders`

### 2. Transform to Star Schema
```bash
python scripts/transform_star_schema.py
```
**Output:** 1M+ records across 5 tables (4 dimensions + 1 fact)

### 3. Connect Power BI
- **Host:** localhost:5433
- **Database:** supply_chain_dw
- **User:** admin
- **Schema:** dw

## 📁 Script Reference

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/load_data.py` | CSV → Staging | ✅ Production |
| `scripts/transform_star_schema.py` | Staging → Star Schema | ✅ Production |
| `scripts/transform_data.py` | Pandas-based transform | ⚠️  Deprecated |
| `sql/populate_star_schema_simple.sql` | SQL transformation | ✅ Production |

## 🏗️ Architecture Decisions

### Why SQL for Transformations?

1. **Performance**: Native PostgreSQL processing > Pandas for large datasets
2. **Reliability**: Direct SQL = no schema mismatch issues
3. **Maintainability**: SQL transformations easier to review and modify
4. **Industry Standard**: Follows modern ELT pattern (dbt, Dataform, Fivetran)

### Pipeline Components

```python
# Load (Python orchestration)
scripts/load_data.py
  ├─ Reads CSV files
  ├─ Validates data types
  └─ Bulk inserts to staging

# Transform (SQL execution via Python)
scripts/transform_star_schema.py
  ├─ Executes SQL script
  ├─ Verifies results
  └─ Reports metrics

# SQL Transformation Logic
sql/populate_star_schema_simple.sql
  ├─ Dimension population (DISTINCT + dedup)
  ├─ Fact table population (JOINs)
  └─ Data quality checks
```

## 📊 Data Lineage

```
DataCoSupplyChainDataset.csv
  └─> stg_raw_orders (staging)
       ├─> dim_customer (Customer ID, Name, Segment)
       ├─> dim_geography (Market → Region → Country)
       ├─> dim_product (Product ID, Name, Category)
       ├─> dim_date (Date dimensions: Year, Month, Day)
       └─> fact_orders (Foreign keys + Sales + OTIF metrics)
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
DATABASE_URL=postgresql://admin:adminpassword@localhost:5433/supply_chain_dw
PGPASSWORD=adminpassword
```

### Database Schema
- **Schema:** `dw` (data warehouse)
- **Tables:** 6 total (1 staging + 5 star schema)
- **Primary Keys:** Surrogate keys (auto-increment)
- **Foreign Keys:** Enforced referential integrity

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| **Staging Load** | ~10 seconds (50K records) |
| **Star Schema Transform** | ~56 seconds (1M records) |
| **Total Pipeline** | ~66 seconds end-to-end |
| **Data Growth Factor** | 20x (50K → 1M records) |

## 🐛 Troubleshooting

### Common Issues

**Issue:** `transform_data.py` schema errors  
**Solution:** Use `transform_star_schema.py` instead (SQL-based)

**Issue:** Duplicate records in dimensions  
**Solution:** SQL uses `DISTINCT` and conflict handling automatically

**Issue:** NULL foreign keys in facts  
**Solution:** Transform script filters out records with missing FKs

## 📚 Documentation

- [ETL Complete Pipeline Guide](../docs/guides/ETL_COMPLETE_PIPELINE.md)
- [Transform Data Guide](../docs/guides/TRANSFORM_DATA_GUIDE.md)
- [Power BI Connection Guide](../docs/guides/POWER_BI_CONNECTION_COMPLETE_GUIDE.md)

## 🎯 Next Phase: Analytics

After pipeline completion:
1. Build Power BI data model
2. Create DAX measures for 5 Strategic Questions
3. Design executive dashboards
4. Implement predictive analytics (Phase 3)

---

**Version:** 2.0  
**Last Updated:** 2026-02-04  
**Status:** Production Ready ✅
