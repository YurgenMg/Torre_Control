# Power BI Connection Guide for Torre Control
## Complete Integration Manual for Supply Chain Analytics

**Version:** 1.0  
**Last Updated:** 2026-02-04  
**Author:** Torre Control Engineering Team

---

## 📊 Overview

This guide provides complete instructions for connecting Power BI to Torre Control's data warehouse. You can choose between two connection methods:

1. **Import from Files** (Recommended) - Best performance, offline capability
2. **DirectQuery to PostgreSQL** - Real-time data, suitable for live dashboards

---

## 🎯 Prerequisites

### Required Software
- **Power BI Desktop** (Latest version)
- **PostgreSQL ODBC Driver** (for DirectQuery option)
- **Torre Control ETL Pipeline** (completed successfully)

### Data Location
- **Processed Files:** `data/processed/` directory
- **Database:** PostgreSQL at `localhost:5433`
- **Schema:** `dw` (data warehouse)

---

## 📁 Option 1: Import from Files (RECOMMENDED)

### Why Choose This Method?
✅ **Fastest performance** - No network latency  
✅ **Offline capability** - Work without database connection  
✅ **Optimized format** - Parquet files are compressed and efficient  
✅ **Version control** - Snapshot of data at export time  

### Step-by-Step Instructions

#### 1. Export Data for Power BI

Run the export utility to generate Parquet files:

```bash
# Export all tables as Parquet (recommended)
make export-powerbi

# Or use the script directly
python scripts/export_for_powerbi.py --format parquet
```

This creates the following files in `data/processed/`:
- `dim_customer.parquet` (~5K rows)
- `dim_product.parquet` (~1.8K rows)
- `dim_geography.parquet` (~150 rows)
- `dim_date.parquet` (~365 rows)
- `fact_orders.parquet` (~186K rows)

#### 2. Connect Power BI to Folder

1. Open **Power BI Desktop**
2. Click **Get Data** → **More...**
3. Search for **Folder** and select it
4. Click **Connect**
5. Browse to your `data/processed/` directory
6. Click **OK**

#### 3. Combine Parquet Files

1. Power BI will show a list of files
2. Click **Combine & Transform Data**
3. Power BI will automatically detect Parquet format
4. Each file will become a separate table

#### 4. Create Data Model Relationships

In the **Model** view, create these relationships:

```
fact_orders → dim_customer
  ├─ Cardinality: Many-to-One (*)
  ├─ Foreign Key: fact_orders[customer_id]
  └─ Primary Key: dim_customer[customer_id]

fact_orders → dim_product
  ├─ Cardinality: Many-to-One (*)
  ├─ Foreign Key: fact_orders[product_card_id]
  └─ Primary Key: dim_product[product_card_id]

fact_orders → dim_geography
  ├─ Cardinality: Many-to-One (*)
  ├─ Foreign Key: fact_orders[geography_key]
  └─ Primary Key: dim_geography[geography_key]

fact_orders → dim_date
  ├─ Cardinality: Many-to-One (*)
  ├─ Foreign Key: fact_orders[date_key]
  └─ Primary Key: dim_date[date_key]
```

#### 5. Mark Date Table

1. Right-click on **dim_date** table
2. Select **Mark as Date Table**
3. Choose **date_key** or **full_date** as the date column

---

## 🔗 Option 2: DirectQuery to PostgreSQL

### Why Choose This Method?
✅ **Real-time data** - Always up-to-date  
✅ **No data refresh** - Queries database directly  
✅ **Smaller file size** - Power BI file only stores model  

⚠️ **Trade-offs:**  
❌ Slower performance (network latency)  
❌ Requires constant database connection  
❌ Limited DAX functionality  

### Step-by-Step Instructions

#### 1. Install PostgreSQL ODBC Driver

Download from: https://www.postgresql.org/ftp/odbc/versions/

Choose the appropriate version for your system (x64 recommended).

#### 2. Configure Connection String

Use these connection parameters:

```
Server: localhost
Port: 5433
Database: supply_chain_dw
Username: admin
Password: adminpassword
```

#### 3. Connect Power BI

1. Open **Power BI Desktop**
2. Click **Get Data** → **Database** → **PostgreSQL database**
3. Enter connection details:
   - **Server:** `localhost:5433`
   - **Database:** `supply_chain_dw`
4. Click **OK**
5. Choose **DirectQuery** mode
6. Select tables from **dw** schema:
   - `dw.dim_customer`
   - `dw.dim_product`
   - `dw.dim_geography`
   - `dw.dim_date`
   - `dw.fact_orders`
7. Click **Load**

#### 4. Create Relationships

Follow the same relationship structure as Option 1 above.

---

## 📊 Building Your First Dashboard

### Key Measures to Create

#### 1. OTIF Percentage

```dax
OTIF % = 
DIVIDE(
    CALCULATE(
        COUNTROWS(fact_orders),
        fact_orders[is_late] = FALSE,
        fact_orders[is_complete] = TRUE,
        fact_orders[is_canceled] = FALSE
    ),
    CALCULATE(
        COUNTROWS(fact_orders),
        fact_orders[is_canceled] = FALSE
    ),
    0
) * 100
```

#### 2. Revenue at Risk

```dax
Revenue at Risk = 
CALCULATE(
    SUM(fact_orders[sales]),
    fact_orders[is_late] = TRUE
)
```

#### 3. Total Sales

```dax
Total Sales = SUM(fact_orders[sales])
```

#### 4. Average Delay Days

```dax
Avg Delay Days = 
AVERAGE(fact_orders[delay_days])
```

#### 5. Order Count

```dax
Order Count = 
DISTINCTCOUNT(fact_orders[order_id])
```

### Recommended Visualizations

#### Page 1: Executive Overview
- **KPI Card:** OTIF %
- **KPI Card:** Total Sales
- **KPI Card:** Revenue at Risk
- **Line Chart:** Sales trend by date (dim_date[full_date])
- **Map:** OTIF % by geography (dim_geography[order_city])

#### Page 2: Geographic Analysis
- **Map Visual:** Market → Region → City drill-down
- **Table:** OTIF % by Market and Region
- **Bar Chart:** Top 10 Cities by Order Volume
- **Scatter Plot:** OTIF % vs. Sales by Region

#### Page 3: Customer Analysis
- **Table:** Top 10 Customers by Sales
- **Pie Chart:** Sales by Customer Segment
- **Line Chart:** Customer retention trend
- **Table:** VIP Customers at Risk

#### Page 4: Product Performance
- **Bar Chart:** Sales by Department
- **Tree Map:** Sales by Category → Product
- **Table:** Product profitability analysis

---

## 🔄 Data Refresh Strategy

### For Import Mode (Parquet Files)

#### Manual Refresh
1. Run ETL pipeline: `make run-etl`
2. Export for Power BI: `make export-powerbi`
3. In Power BI Desktop: **Home** → **Refresh**

#### Scheduled Refresh (Power BI Service)
1. Publish report to Power BI Service
2. Configure **Scheduled Refresh**
3. Set up **On-premises data gateway** to access local files
4. Schedule refresh frequency (daily, hourly, etc.)

### For DirectQuery Mode

Data is always up-to-date. No refresh needed.

---

## ⚡ Performance Optimization Tips

### 1. Use Parquet Format
Parquet files are **10-50x faster** than CSV for Power BI.

```bash
# Always use Parquet
python scripts/export_for_powerbi.py --format parquet
```

### 2. Filter Early
Apply filters at the data source level, not in visuals.

### 3. Incremental Refresh
For large fact tables (>100K rows), configure incremental refresh:
1. Right-click **fact_orders** table
2. Select **Incremental refresh**
3. Configure based on **date_key** column

### 4. Aggregate Tables
Create summary tables for faster dashboard load:

```dax
Orders_Summary = 
SUMMARIZE(
    fact_orders,
    dim_date[full_date],
    dim_geography[market],
    "Total Sales", SUM(fact_orders[sales]),
    "Order Count", DISTINCTCOUNT(fact_orders[order_id])
)
```

### 5. Use Calculated Columns Sparingly
Prefer measures over calculated columns for better performance.

---

## 🛠️ Troubleshooting

### Issue: "Cannot connect to PostgreSQL"

**Solution:**
1. Verify PostgreSQL is running: `docker ps`
2. Check port: Should be `5433` (not default `5432`)
3. Test connection: `psql -h localhost -p 5433 -U admin -d supply_chain_dw`

### Issue: "Parquet files not loading"

**Solution:**
1. Ensure Parquet files exist: `ls data/processed/*.parquet`
2. Update Power BI Desktop to latest version
3. Check file permissions

### Issue: "Relationships not creating automatically"

**Solution:**
1. Verify foreign keys exist in fact_orders
2. Check that dimension primary keys are unique
3. Manually create relationships if needed

### Issue: "Slow query performance"

**Solution:**
1. Switch from DirectQuery to Import mode
2. Use Parquet format instead of CSV
3. Create indexes on foreign key columns in PostgreSQL

---

## 📚 Additional Resources

### Torre Control Documentation
- **ETL Pipeline Guide:** `docs/guides/ETL_COMPLETE_PIPELINE.md`
- **Data Dictionary:** `Data/Raw/DescriptionDataCoSupplyChain.csv`
- **Architecture Overview:** `AUDITORIA_ARQUITECTURA.md`

### Power BI Resources
- [Power BI Best Practices](https://docs.microsoft.com/power-bi/guidance/power-bi-optimization)
- [DAX Function Reference](https://dax.guide/)
- [DirectQuery Best Practices](https://docs.microsoft.com/power-bi/connect-data/desktop-directquery-about)

### Support
- **GitHub Issues:** [Torre Control Repository](https://github.com/YurgenMg/Torre_Control)
- **Documentation:** `docs/` directory

---

## 🎯 Success Checklist

- [ ] PostgreSQL database running (port 5433)
- [ ] ETL pipeline executed successfully
- [ ] Data exported to Parquet format
- [ ] Power BI Desktop installed
- [ ] Data model relationships created
- [ ] dim_date marked as date table
- [ ] Key measures created (OTIF%, Revenue at Risk, etc.)
- [ ] Dashboard published to Power BI Service (optional)

---

**🎉 Congratulations!** You've successfully connected Power BI to Torre Control.

For questions or issues, refer to the documentation in `docs/` or create a GitHub issue.
