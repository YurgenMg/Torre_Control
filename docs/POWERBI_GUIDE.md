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

## 📊 Building Your Dashboard (Best Practices)

### 🏗️ Architecture: Executive vs. Operational Views

#### Landing Page (Executive View)
**Purpose:** High-level KPIs for decision-makers  
**Design Principle:** Menos es Más - Limitar objetos visuales para mejor rendimiento

**Structure:**
1. **KPI Cards (Top Row)** - 4 tarjetas principales con tendencias
2. **Main Chart** - Vista macro de OTIF% over time
3. **Geographic Overview** - Map con drill-down capability
4. **Hidden Filters** - Use Bookmarks to toggle visibility

#### Drill-Through Pages (Operational View)
**Purpose:** Detailed analysis for operational teams  
**Access:** Right-click on data point → "Drill Through"

---

### 📈 Key Measures with DAX Best Practices

#### 1. OTIF Percentage (Using VAR for Performance)

```dax
OTIF % = 
VAR OnTimeOrders = 
    CALCULATE(
        COUNTROWS(fact_orders),
        fact_orders[is_late] = FALSE,
        fact_orders[is_complete] = TRUE,
        fact_orders[is_canceled] = FALSE
    )
VAR TotalValidOrders = 
    CALCULATE(
        COUNTROWS(fact_orders),
        fact_orders[is_canceled] = FALSE
    )
RETURN
    DIVIDE(OnTimeOrders, TotalValidOrders, 0) * 100
```

**Why VAR?** Mejora rendimiento al calcular expresiones una sola vez.

#### 2. Revenue at Risk (Explicit Measure)

```dax
Revenue at Risk = 
VAR LateOrders = 
    FILTER(
        fact_orders,
        fact_orders[is_late] = TRUE
    )
RETURN
    SUMX(LateOrders, fact_orders[sales])
```

#### 3. Total Sales (Never use implicit measures!)

```dax
Total Sales = SUM(fact_orders[sales])
```

#### 4. Average Delay Days (Handle BLANKs correctly)

```dax
Avg Delay Days = 
-- No convertir BLANKs a 0 artificialmente
AVERAGE(fact_orders[delay_days])
```

#### 5. Order Count (Distinct count for accuracy)

```dax
Order Count = DISTINCTCOUNT(fact_orders[order_id])
```

#### 6. Churn Rate (For Customer Analysis)

```dax
Churn Rate % = 
VAR TotalCustomers = DISTINCTCOUNT(fact_orders[customer_id])
VAR ChurnedCustomers = 
    CALCULATE(
        DISTINCTCOUNT(fact_orders[customer_id]),
        fact_orders[has_churned] = TRUE
    )
RETURN
    DIVIDE(ChurnedCustomers, TotalCustomers, 0) * 100
```

---

### 🎯 Pro Tip: Calculation Groups for KPI Time Intelligence

**Problem:** Creating separate measures for OTIF YTD, OTIF QTD, OTIF MTD is repetitive and clutters your model.

**Solution:** Use **Calculation Groups** to dynamically switch between time calculations:

1. Create Calculation Group: `Time Intelligence`
2. Add calculation items:
   - `Current Period`
   - `YTD` (Year-to-Date)
   - `QTD` (Quarter-to-Date)
   - `PY` (Prior Year)
   - `Growth %`

3. In visual, use a slicer to let users choose the time context dynamically.

**Example Calculation Item (YTD):**
```dax
YTD = 
TOTALYTD(SELECTEDMEASURE(), dim_date[date])
```

**Benefit:** One measure (`OTIF %`), multiple time contexts without creating 20+ measures.

---

### 🗺️ Recommended Visualizations by Use Case

#### Page 1: Executive Dashboard

| Visual Type | Purpose | Data Setup |
|-------------|---------|------------|
| **KPI Card** (x4) | OTIF%, Total Sales, Revenue at Risk, Churn Rate | Add trend sparkline |
| **Line & Stacked Column Chart** | OTIF% trend + Volume | Line: OTIF%, Bars: Order Count |
| **Shape Map** (Azure Maps) | Geographic OTIF by Market | Size: Sales, Color: OTIF% (Red=Bad) |
| **Smart Narrative** | Auto-generated insights | Drag-and-drop visual |

**Interactivity:**
- Use **Bookmarks** to switch between "Sales View" and "Logistics View"
- Configure **Tooltips** to show detail on hover without cluttering main view

#### Page 2: Geographic Deep-Dive

| Visual Type | Purpose | Configuration |
|-------------|---------|--------------|
| **Shape Map** with Hierarchy | Drill-down Market→Region→City | Enable "Drill mode" |
| **Matrix** | OTIF% by Market & Region | Conditional formatting: Red <90%, Green >95% |
| **Decomposition Tree** | Root cause analysis of delays | Start with "Revenue at Risk" |

**Navigation:**
- Configure **Drill-Through** to "Order Details" page (see below)
- On map selection, other visuals auto-filter

#### Page 3: Operational - Order Details (Drill-Through Page)

**Setup:**
1. Create new page, set as **Drill-Through page**
2. Add `dim_date[date]` to Drill-Through fields
3. Mark page as **Hidden** (users access via right-click)

| Visual Type | Purpose |
|-------------|---------|
| **Matrix** | List of late orders with Order ID, Customer, Days Late |
| **Bar Chart** | Top carriers with delays |
| **Back Button** | Return to previous page |

**Why Drill-Through?** Keeps executive view clean while providing operational detail on-demand.

#### Page 4: Customer Risk Analysis

| Visual Type | Purpose | Configuration |
|-------------|---------|--------------|
| **Matrix** | VIP customers with consecutive late orders | Sort by `sales_per_customer` DESC |
| **Scatter Plot** | Customer LTV vs. Late Order % | Identify high-value at-risk customers |
| **Decomposition Tree** | Churn drivers (by segment, product, region) | Root: Churn Rate % |

**Format Tip:** Use **Conditional Formatting** on the Matrix to highlight revenue >$10K in bold red.

---

### 🎨 Design Best Practices (From Your Notebook)

#### 1. Hierarchy Configuration
Create geographic hierarchy for drill-down:
```
dim_geography
  └─ Geographic Hierarchy
      ├─ Market (Level 1)
      ├─ Region (Level 2)
      ├─ Country (Level 3)
      └─ City (Level 4)
```

**Usage:** Drag hierarchy to visual, enable drill-down button in visual.

#### 2. Limit Visuals Per Page
**Recommendation:** Max **5-7 visuals** per page to minimize parallel queries and improve load time.

#### 3. Annotations in Presentations
When exporting to PowerPoint, use **Data Point Annotations** to highlight key insights directly on charts.

#### 4. Modern Tooltips
Configure **Tooltip Pages** instead of default tooltips:
- Create a hidden page with detailed breakdown
- Assign as tooltip for main visual
- Shows rich context on hover

---

### 🚀 Advanced: Star Schema Optimization Reminders

**Model Checklist:**
- ✅ Use **numeric surrogate keys** (customer_key, product_key) for relationships (faster than text IDs)
- ✅ Avoid **bi-directional filtering** unless absolutely necessary (performance killer)
- ✅ Separate date and time into different columns (reduces cardinality)
- ✅ Mark `dim_date` as **Date Table** (required for time intelligence functions)
- ✅ Disable **Auto Date/Time** in settings (use explicit date table instead)

**Relationship Best Practices:**
- Prefer **One-to-Many (1:*)** relationships
- Avoid **Many-to-Many (M:M)** if possible (use bridge tables or `TREATAS`)
- Use **physical relationships** over virtual (better performance)

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

## ⚠️ Common Mistakes to Avoid (Critical)

### 1. Publishing Sensitive Data to Web
❌ **NEVER** use "Publish to Web" for Torre Control dashboards  
✅ Use Power BI Service with proper access controls or export to PowerPoint for sharing

### 2. Using Auto Date/Time
❌ Auto date/time creates hidden tables that bloat your model  
✅ Disable in File → Options → Data Load, use explicit `dim_date` table

### 3. Bi-directional Filtering Everywhere
❌ Activating cross-filtering on all relationships creates ambiguous paths  
✅ Use uni-directional (1→*) relationships by default, bi-directional only when necessary

### 4. Implicit Measures
❌ Dragging numeric columns directly to visuals creates unpredictable implicit measures  
✅ Always create explicit DAX measures (e.g., `Total Sales = SUM(fact_orders[sales])`)

### 5. Converting BLANKs to Zeros
❌ Replacing `BLANK()` with 0 degrades performance on large fact tables  
✅ Let Power BI handle BLANKs naturally (auto-filters them for optimization)

### 6. Not Using Variables (VAR) in DAX
❌ Repeating the same expression multiple times in a measure  
✅ Use `VAR` to calculate once and reuse (improves readability and performance)

### 7. Over-using Iterators
❌ `SUMX` or `FILTER` on entire fact table without pre-filtering  
✅ Filter first with `CALCULATE`, then iterate over reduced dataset

---

## 🎯 Success Checklist

### Data Connection
- [ ] PostgreSQL database running (port 5433)
- [ ] ETL pipeline executed successfully
- [ ] Data exported to Parquet format
- [ ] Power BI Desktop installed (latest version)

### Data Model Configuration
- [ ] Data model relationships created (fact_orders → dim_*)
- [ ] All relationships are **One-to-Many (1:*)**
- [ ] Bi-directional filtering disabled (unless specifically needed)
- [ ] `dim_date` marked as Date Table
- [ ] Numeric surrogate keys used for relationships
- [ ] Auto Date/Time disabled in settings

### DAX Measures Created
- [ ] OTIF % (using VAR)
- [ ] Revenue at Risk
- [ ] Total Sales (explicit measure)
- [ ] Churn Rate %
- [ ] Order Count (DISTINCTCOUNT)
- [ ] Average Delay Days
- [ ] All measures use explicit DAX (no implicit measures)

### Dashboard Structure
- [ ] Landing page (Executive View) with max 5-7 visuals
- [ ] Geographic hierarchy created (Market→Region→Country→City)
- [ ] Drill-through page created for operational details
- [ ] Bookmarks configured for view switching
- [ ] KPI cards include trend sparklines
- [ ] Smart Narrative added for auto-insights

### Performance Optimization
- [ ] Variables (VAR) used in complex DAX measures
- [ ] Calculation Groups created for time intelligence (optional advanced)
- [ ] Conditional formatting applied to matrices
- [ ] Modern tooltips configured
- [ ] Incremental refresh configured for fact_orders (if >100K rows)

### Publishing & Sharing
- [ ] Dashboard tested with sample data
- [ ] Sensitive data NOT published to web
- [ ] Dashboard published to Power BI Service (optional)
- [ ] Proper access controls configured

---

**🎉 Congratulations!** Your Torre Control dashboard now follows enterprise-grade Power BI best practices!

For questions or issues, refer to:
- **Project Documentation:** `docs/` directory
- **Your Power BI Notebook:** 54 sources with advanced techniques
- **GitHub Issues:** [Torre Control Repository](https://github.com/YurgenMg/Torre_Control)
