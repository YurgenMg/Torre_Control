# Copilot Instructions - Proyecto Torre Control

## 🏢 The Business Context: Supply Chain Control Tower
**DataCo Global** is an international retail and logistics company hemorrhaging operational efficiency. The problem is not revenue generation—it's **operational blindness**.

### The Situation
- ✗ Sales data, shipping data, and customer data live in isolated silos
- ✗ Legacy ERP exports produce massive CSV files with zero data governance
- ✗ No single source of truth for on-time delivery performance
- ✗ COO has hunches about delays, but no hard data to make decisions
- ✗ Customer churn is rising; delivery complaints are at all-time highs
- ✗ Logistics costs are spiraling with no visibility into root causes

### Your Mission
Build a **centralized Control Tower** that provides real-time operational visibility and enables data-driven decision-making across the enterprise.

---

## 🎯 The 5 Strategic Questions (Your KPIs)

Every analysis, query, and dashboard must answer ONE of these questions for executive leadership:

### 1️⃣ **Visibility of Service (OTIF - On-Time In-Full)**
> *"What is our real percentage of perfect deliveries? I don't want global averages—tell me where we're failing. Are delays in 'Priority' or 'Standard' shipments?"*

**Impact:** Renegotiate carrier contracts, adjust SLA targets, identify systematic regional failures

**Metrics:**
- OTIF% = (On-Time ✓ AND In-Full ✓) / Total Orders
- OTIF by: Market, Region, Customer Segment, Product Category, Carrier (if available)
- Trend: Month-over-month, Year-over-year

**Data Source:**
- `Days for shipping (real)` ≤ `Days for shipment (scheduled)` → On-Time
- `Delivery Status` ≠ ('Canceled' | 'Suspected Fraud') → In-Full

---

### 2️⃣ **Revenue at Risk (Financial Impact)**
> *"How much revenue is at risk due to late deliveries? Are we losing $10 orders or $500 orders? Which customer segments hemorrhage the most?"*

**Impact:** Prioritize high-value dispatch routes, implement dynamic pricing penalties, focus recovery efforts on VIP customers

**Metrics:**
- Total Revenue at Risk = SUM(Sales) WHERE Late_delivery_risk = 1
- Revenue at Risk by: Market, Customer Segment, Product Category
- Average Order Value: Late vs. On-Time
- Churn Probability by Delay Duration

**Data Source:**
- `Sales`, `Benefit per order`, `Order Item Total` × `Late_delivery_risk` = revenue exposure
- Segment by `Customer Segment`, `Market`

---

### 3️⃣ **Churn Risk (Customer Retention)**
> *"Who are our Top 10% customers by sales that have experienced consecutive late deliveries in their last 2 orders? I need a list for the VIP recovery team TODAY."*

**Impact:** Prevent defection of high-value accounts to competitors (Amazon), implement proactive retention programs

**Metrics:**
- VIP Customers At Risk = Top 10% by Sales + Consecutive Late Orders
- Customer Lifetime Value (LTV) at risk
- Repeat Order Rate by Delivery Performance
- Segment analysis: Which segments have highest churn correlation with delays

**Data Source:**
- `Customer Id`, `Sales per customer` → rank Top 10%
- `Late_delivery_risk` over last 2 orders per customer
- `Delivery Status` / days late distribution

---

### 4️⃣ **Geographic Efficiency (Network Optimization)**
> *"Do we have 'Black Holes' in our network? Are there cities/regions where we systematically fail—regardless of product type—independent of time of year?"*

**Impact:** Close unprofitable routes, relocate distribution centers, negotiate local carrier partnerships, consider dropshipping alternatives

**Metrics:**
- OTIF by: Market → Region → State → City (drill-down hierarchy)
- Late Delivery Rate by Geography (% of orders late)
- Revenue Concentration vs. Performance (Pareto: are high-revenue regions also high-risk?)
- Shipping Days Analysis: Scheduled vs. Actual by Region

**Data Source:**
- Geography: `Customer Country`, `Customer State`, `Customer City` + `Order Region`, `Order State`, `Order Country`
- `Market` (Africa, Europe, LATAM, Pacific Asia, USCA)
- Group by: Market → Region → State → City
- Calculate: On-Time % and In-Full % at each level

---

### 5️⃣ **Fraud & Anomaly Detection**
> *"Are we hemorrhaging inventory through 'Lost' or 'Suspected Fraud' orders? What's our total loss? How many orders are stuck in limbo?"*

**Impact:** Internal audit, reduce shrinkage, improve inventory accuracy, identify carrier corruption

**Metrics:**
- Total Orders by Status: Canceled, Lost, Suspected Fraud, On Hold, Payment Review, etc.
- Inventory Loss Value = SUM(Sales) by suspicious status
- Anomaly Flags: Days for shipping (real) > 60 days, Orders never delivered, Refund patterns
- Carriers/Routes associated with high anomaly rates

**Data Source:**
- `Order Status` = (CANCELED, SUSPECTED_FRAUD, PENDING, LOST)
- `Days for shipping (real)` outlier detection (>60 days)
- Cross-validation: `Late_delivery_risk` vs. `Delivery Status` discrepancies

---

## Project Overview
**Torre Control** is a supply chain analytics platform that transforms raw ERP data into a centralized intelligence hub for operational decision-making. The platform's north star metric is **OTIF (On-Time In-Full)**, and all analysis radiates from the five strategic questions above.

**Core Outcome:** Replace fragmented Excel reports with a single source of truth that enables the executive team to optimize logistics, protect revenue, and retain customers.

## 📊 Data Architecture

### Raw Data Sources (`Data/Raw/`)
```
DataCoSupplyChainDataset.csv     ← Main transactional fact table
├─ ~100K+ rows of sales orders, shipments, customer interactions
├─ Grain: One row per order item
├─ Period: Historical order data (legacy ERP export)
└─ Schema: 54 fields (see DescriptionDataCoSupplyChain.csv)

DescriptionDataCoSupplyChain.csv ← Data Dictionary (Semicolon-delimited)
├─ Field names, business definitions, valid value lists
├─ Source of Truth for all field semantics
└─ MUST be consulted before any analysis

tokenized_access_logs.csv        ← System transaction log (supplementary)
└─ Access patterns, user behavior tracking
```

### Data Processing Architecture
```
┌─────────────────────────────────────────────────────────────┐
│ RAW DATA (Legacy ERP Export)                                │
│ • Messy, duplicates, nulls, mixed domains                   │
│ • Field names with spaces/special chars                     │
│ • No referential integrity                                  │
└─────────────────────────────────────────────────────────────┘
                          ⬇️ ETL Pipeline (NEEDS BUILDING)
┌─────────────────────────────────────────────────────────────┐
│ PROCESSED DATA (Single Source of Truth)                     │
│ Data/Processed/                                             │
│ ├─ dim_customer.csv          (Customer dimension)           │
│ ├─ dim_product.csv           (Product dimension)            │
│ ├─ dim_geography.csv         (Location dimension)           │
│ ├─ dim_date.csv              (Temporal dimension)           │
│ └─ fact_orders.csv           (Order transactions)           │
│                                                              │
│ Characteristics:                                            │
│ • Deduplicated, null-handled, validated                    │
│ • Consistent naming (snake_case)                           │
│ • Surrogate keys, referential integrity                    │
│ • Quality flags (data quality indicators)                  │
│ • Lineage tracking (source field mappings)                 │
└─────────────────────────────────────────────────────────────┘
                          ⬇️ Analytics Layer
┌─────────────────────────────────────────────────────────────┐
│ POWER BI DASHBOARD (Torre Control v0.1.pbix)               │
│ • 5 Executive Views (one per strategic question)           │
│ • Drill-down hierarchies: Market → Region → State → City  │
│ • Real-time slicers: Date, Segment, Product Category      │
│ • KPI cards: OTIF%, Revenue at Risk, Churn Risk Index     │
└─────────────────────────────────────────────────────────────┘
```

### Critical Dimensional Hierarchies (Star Schema)

**Geography Dimension** (Answers Q4: Geographic Efficiency)
```
Market (5 values)
├─ Africa
├─ Europe
├─ LATAM
├─ Pacific Asia
└─ USCA
    ⬇️ Region (e.g., "Southeast Asia", "North Africa", "East of USA")
        ⬇️ Country (e.g., "United States", "India", "Brazil")
            ⬇️ State (e.g., "California", "New York")
                ⬇️ City (e.g., "Los Angeles", "Manhattan")
```

**Product Dimension** (Answers Q1: OTIF by product, Q3: Revenue impact)
```
Department Name (e.g., "Office Supplies", "Technology")
    ⬇️ Category Name (e.g., "Furniture", "Phones", "Copiers")
        ⬇️ Product Name (specific SKU)
            ⬇️ Product Price, Category ID, Image Link
```

**Customer Dimension** (Answers Q3: Churn Risk, Q2: Revenue at Risk)
```
Customer Segment (3 types: Consumer, Corporate, Home Office)
    ⬇️ Customer ID
        ⬇️ Customer Name, Email, Address
        ⬇️ Sales per Customer (aggregate LTV)
```

**Date Dimension** (Temporal analysis for all questions)
```
Order Date (DateOrders)
    ⬇️ Year, Quarter, Month, Week, Day
    ⬇️ Is Holiday, Fiscal Period (if applicable)
    ⬇️ Day of Week, Week Number
```

**Fact Table: Orders** (Central measurable events)
```
PK: Order ID + Order Item ID
├─ FK: Customer ID, Product ID, Market, Region, State, City
├─ FK: Order Date
├─ Dimensions:
│  ├─ Days for shipping (real)     [NUMERIC - actual delivery time]
│  ├─ Days for shipment (scheduled) [NUMERIC - promised delivery time]
│  ├─ Delivery Status               [STRING - COMPLETE, CANCELED, etc.]
│  ├─ Late_delivery_risk            [BINARY - 1 = late, 0 = on-time]
│  ├─ Order Status                  [STRING - detailed order state]
│  └─ Order Item Discount Rate      [NUMERIC - % discount]
└─ Measures:
   ├─ Sales                         [Revenue amount]
   ├─ Benefit per order             [Profit]
   ├─ Order Item Total              [Line item amount]
   ├─ Order Item Quantity           [Units shipped]
   └─ Order Item Profit Ratio       [Margin %]
```

### Critical Fields for Analysis

| Field | Business Question | Validation Rules | Transformation |
|-------|-------------------|------------------|-----------------|
| `Late_delivery_risk` | Q1, Q2, Q3, Q5 | Binary (0/1) | Cross-validate vs. Delivery Status |
| `Days for shipping (real)` | Q1, Q4, Q5 | Numeric ≥0, flag >60 days as anomaly | Calculate delay ratio vs scheduled |
| `Days for shipment (scheduled)` | Q1, Q4 | Numeric ≥1 | Use as denominator for delay ratio |
| `Delivery Status` | Q1, Q5 | Valid: COMPLETE, CANCELED, PENDING, SUSPECTED_FRAUD, etc. | Map to Late_delivery_risk validation |
| `Order Item Discount Rate` | Q2, Q5 | Numeric 0-100% | Correlation analysis with fraud |
| `Sales`, `Benefit per order` | Q2, Q3, Q4 | Numeric ≥0 | Revenue at Risk, LTV calculations |
| `Customer Segment` | Q3, Q4 | Enum: Consumer, Corporate, Home Office | Segment performance analysis |
| `Market` | Q4, Q1, Q2 | Enum: Africa, Europe, LATAM, Pacific Asia, USCA | Drill-down hierarchy root |
| `Order Region` | Q4 | String, 20+ valid values | Geographic drill-down |
| `order date (DateOrders)` | All questions | Date field, no future dates | Temporal trend analysis, seasonality |

---

## Data Quality Standards

**Before any analysis, validate:**

✓ **No Nulls in Critical Fields** (Late_delivery_risk, Days for shipping (real), Customer ID, Order ID, Sales)

✓ **Outlier Detection:**
  - Days for shipping (real) > 60 days → Flag as potential data error
  - Order Item Discount Rate > 100% → Impossible, mark as fraud
  - Negative Sales → Data corruption

✓ **Geographic Consistency:**
  - All Market values must be in [Africa, Europe, LATAM, Pacific Asia, USCA]
  - All Regions must map to a valid Market
  - No orphaned cities without states

✓ **Temporal Logic:**
  - No future order dates
  - Delivery date (calculated) ≥ Order date
  - order date (DateOrders) must be within company operational window

✓ **Cross-Field Validation:**
  - If Late_delivery_risk = 1, then Days for shipping (real) > Days for shipment (scheduled)
  - If Delivery Status = "Canceled", then Sales may be $0
  - If Order Status = "SUSPECTED_FRAUD", cross-check with Order Item Discount Rate for anomalies

## 📈 Power BI Dashboard Architecture (`PBIX/TorreControl_v0.1.pbix`)

The dashboard is designed with **5 Executive Views**, one for each strategic question. Each view follows the same interaction pattern: corporate executives drill down from global metrics → market → region → actionable insights.

### Dashboard Structure

| View | Strategic Question | Primary Visualization | Key Slicers | Data Source |
|------|-------------------|----------------------|------------|-------------|
| **OTIF Performance** | Q1: Visibility of Service | KPI card + Matrix (Market × Segment) + Trend line | Date range, Market, Segment | fact_orders + dim_geography |
| **Revenue at Risk** | Q2: Financial Impact | Waterfall (Revenue by status) + Top Products/Markets | Date, Product Category, Customer Segment | fact_orders + Sales measure |
| **VIP Churn Risk** | Q3: Retention Crisis | Table (VIP customers + last 2 orders status) + Trend | VIP filter (Top 10%), Date | fact_orders + dim_customer |
| **Geographic Heatmap** | Q4: Network Efficiency | Map (Market → Region drill-down) + OTIF% by geography | Market, Drill-down controls | dim_geography + fact_orders |
| **Anomaly & Fraud** | Q5: Loss Detection | Scatter (Days vs. Discount) + Suspicious Order list | Order Status filter, Date range | fact_orders + quality flags |

### Brand & Assets
- **Location:** `PBIX/Emoticones/` (custom icons, company branding)
- **Current Theme:** Professional corporate (blue/gray)
- **Version Control:** `TorreControl_v0.1.pbix` incremented to v0.2, v0.3, etc. as features mature

---

## 🛠️ Development Patterns & Conventions

### 1. ETL Pipeline Development Pattern

**File Organization:**
---

## 🎯 Priority Implementation Roadmap

### Phase 1: Foundation (Build Single Source of Truth) ⚡
**Goal:** Get processed data into Data/Processed/ so dashboard can consume clean data

1. **Create ETL Pipeline** (`Data/Processed/etl_pipeline.py`)
   - Read DataCoSupplyChainDataset.csv
   - Document all 54 fields using DescriptionDataCoSupplyChain.csv
   - Implement data quality checks
   - Output: dim_customer.csv, dim_product.csv, dim_geography.csv, dim_date.csv, fact_orders.csv

2. **Build Star Schema** (Dimensional Modeling)
   - Fact table: Order transactions (grain: one row per order item)
   - Dimensions: Customer, Product, Geography (Market-Region-State-City), Date
   - Surrogate keys, referential integrity, no nulls in FKs

3. **Calculate Core Metrics**
   - OTIF% = (On-Time ✓ AND In-Full ✓) / Total Orders
   - Revenue at Risk = SUM(Sales) WHERE Late_delivery_risk = 1
   - Churn Risk Flag = Customers with 2+ consecutive late deliveries
   - Delay Ratio = Days for shipping (real) / Days for shipment (scheduled)

### Phase 2: Dashboarding (Visual Decision-Making) 📊
**Goal:** Replace Excel reports with real-time Power BI insights

1. **Refresh Power BI Data Model**
   - Import processed CSV files
   - Establish relationships (fact_orders → dim_*)
   - Create calculated columns: OTIF_flag, Revenue_at_Risk_flag, Churn_Risk_flag

2. **Build 5 Executive Views** (One per strategic question)
   - View 1: OTIF Performance (KPI + drill-down by Market, Region, Segment)
   - View 2: Revenue at Risk (Waterfall + Top risk drivers)
   - View 3: Churn Risk (VIP customers with recent late orders)
   - View 4: Geographic Heatmap (Market-Region-State-City OTIF%)
   - View 5: Anomaly Detection (Suspected fraud, >60 day delays, status outliers)

3. **Add Interactivity**
   - Date range slicer (global filter)
   - Market/Region/Segment slicers
   - Drill-down capabilities (Map visual: click region → see states → cities)
   - Export-to-Excel for VIP lists

### Phase 3: Advanced Analytics (Predictive & Prescriptive) 🔮
**Goal:** Move from "what happened?" to "what will happen?" and "what should we do?"

1. **Predictive Modeling** (for future late deliveries)
   - Features: Days for shipment (scheduled), Order Item Discount Rate, Customer History, Geographic region
   - Target: Late_delivery_risk
   - Model: Logistic Regression or Random Forest (calibrated for business use)
   - Output: Predicted probability of late delivery per order (0-100%)

2. **Prescriptive Analytics** (optimization)
   - Identify low-profit high-delay routes → consider exit
   - Identify high-profit high-delay routes → invest in carrier partner quality
   - Route optimization: suggest alternative carriers/regions for high-risk orders

3. **Scenario Planning**
   - "What if we reduce discount rates?"
   - "What if we shift orders to priority carriers?"
   - Sensitivity analysis: Impact on OTIF%, Revenue at Risk, Customer retention

---

## 📚 Reference: Field Catalog (All 54 Fields)

| Field | Type | Used In Q | Notes |
|-------|------|----------|-------|
| Type | String | Contextual | Transaction type |
| Days for shipping (real) | Numeric | Q1, Q4, Q5 | CRITICAL: Actual delivery time |
| Days for shipment (scheduled) | Numeric | Q1, Q4 | CRITICAL: Promised delivery time |
| Benefit per order | Numeric | Q2 | Profit per order |
| Sales per customer | Numeric | Q3 | Customer LTV |
| Delivery Status | String | Q1, Q5 | COMPLETE, CANCELED, etc. |
| Late_delivery_risk | Binary | Q1, Q2, Q3, Q5 | TARGET KPI |
| Category Id / Category Name | String | Q1, Q2 | Product category |
| Customer City / Country / State | String | Q4 | Geographic dimension |
| Customer Email / Fname / Lname | String | Q3 | Customer identification |
| Customer Id | String | Q3, PK | Primary key for customer |
| Customer Segment | String | Q1, Q3, Q4 | Consumer/Corporate/Home Office |
| Department Name | String | Q1 | Product department |
| Market | String | Q1, Q4 | PRIMARY: Africa, Europe, LATAM, Pacific Asia, USCA |
| Order City / Country | String | Q4 | Delivery destination |
| Order Date (DateOrders) | Date | All | PRIMARY: Time dimension |
| Order Id | String | All, PK | Order transaction ID |
| Order Item Discount / Discount Rate | Numeric | Q2, Q5 | Discount analysis |
| Order Item Product Price | Numeric | Q2 | Product cost |
| Order Item Quantity | Numeric | Q2 | Units per order |
| Sales | Numeric | Q2, Q3, Q4 | Revenue metric |
| Order Item Total | Numeric | Q2 | Line item revenue |
| Order Profit Per Order | Numeric | Q2 | Profit metric |
| Order Region | String | Q4 | Geographic region (20+ values) |
| Order State | String | Q4 | Geographic state |
| Order Status | String | Q5 | COMPLETE, PENDING, CANCELED, SUSPECTED_FRAUD, etc. |
| Product Name / Category Id | String | Q1, Q2 | Product identification |
| *[Additional 25 fields]* | * | * | See DescriptionDataCoSupplyChain.csv for full list |

---

## 📂 File Structure

```
Proyecto_TorreContol/
├── Data/
│   ├── Raw/                                  ← NEVER MODIFY
│   │   ├── DataCoSupplyChainDataset.csv
│   │   ├── DescriptionDataCoSupplyChain.csv
│   │   └── tokenized_access_logs.csv
│   └── Processed/                           ← Generated by ETL
│       ├── etl_pipeline.py                  ← Main orchestrator (BUILD THIS)
│       ├── data_ingestion.py                ← CSV reading, basic cleaning
│       ├── data_transformation.py           ← Star schema modeling
│       ├── data_validation.py               ← QA checks
│       ├── feature_engineering.py           ← OTIF, Revenue at Risk, etc.
│       ├── field_mappings.json              ← Raw → Processed name mappings
│       ├── logs/                            ← ETL execution logs
│       ├── dim_customer.csv                 ← Output: Customer dimension
│       ├── dim_product.csv                  ← Output: Product dimension
│       ├── dim_geography.csv                ← Output: Geography dimension
│       ├── dim_date.csv                     ← Output: Date dimension
│       └── fact_orders.csv                  ← Output: Main fact table
├── PBIX/
│   ├── TorreControl_v0.1.pbix              ← Power BI dashboard (refresh with processed data)
│   └── Emoticones/                         ← Custom icons & branding
├── .github/
│   └── copilot-instructions.md             ← This file
└── README.md (CREATE THIS)
   └─ Executive summary of Torre Control project
```

---

## 💡 Key Insights for AI Agents

**What makes this project unique:**
- NOT a generic ML project (is not about prediction alone)
- IS an operational intelligence platform solving real business blindness
- The 5 strategic questions are the ONLY questions worth asking
- Every transformation must trace back to one of the 5 Qs
- Data quality is existential (bad data → bad decisions → customer churn)
- Geographic hierarchy is critical (regions behave differently)
- Revenue at Risk is the business language—translate technical metrics to $$$

**Common Pitfalls to Avoid:**
- ❌ Building beautiful dashboards without solving the 5 questions
- ❌ Analyzing data at global level (missing regional patterns)
- ❌ Ignoring Late_delivery_risk vs. Delivery_Status discrepancies
- ❌ Using simple averages instead of weighted metrics (high-value orders matter more)
- ❌ Not validating geographic/market data consistency
- ❌ Forgetting that "On-Time" AND "In-Full" must BOTH be true for OTIF
# Churn Risk Score (Q3)
customer_late_orders = COUNT(*) WHERE late_delivery_risk = 1 GROUP BY customer_id
churn_candidates = customers WHERE late_orders >= 2 IN LAST 30 DAYS
churn_risk_score = churn_candidates.sales_per_customer / avg_customer_ltv

# Delivery Delay Ratio
delay_ratio = days_real / days_scheduled
avg_delay_ratio BY market, region, product_category

# Fraud Detection Anomalies
flag_fraud = (order_status = 'SUSPECTED_FRAUD') | 
             (discount_rate > 50% & sales > $1000) |
             (days_real > 60)
```

### 2. Field Naming Convention

**Raw Data:**
- Preserve original field names from CSV: `"Days for shipping (real)"`, `"Customer Id"`
- Document original → processed mapping in `field_mappings.json`

**Processed Data:**
- Convert to snake_case: `days_for_shipping_real`, `customer_id`
- Prefix dimensions: `dim_`, facts: `fact_` (e.g., `dim_customer.csv`, `fact_orders.csv`)
- Quality flags: `_is_valid`, `_is_outlier`, `_quality_flag`

**Power BI DAX Measures:**
- Prefix aggregations: `msr_`, ratios: `ratio_`, flags: `is_`
- Example: `msr_otif_pct`, `ratio_delivery_delay`, `is_churn_risk`

### 3. Validation & Data Quality Rules

**Automated Data Quality Checks (Run post-ETL):**

✓ **Completeness:** Flag any NULL in [Late_delivery_risk, Days for shipping (real), Customer ID, Order ID]

✓ **Accuracy:** 
- If Late_delivery_risk = 1 → Verify Days for shipping (real) > Days for shipment (scheduled)
- Delivery_Status ∈ [COMPLETE, CANCELED, PENDING, SUSPECTED_FRAUD, ON_HOLD, etc.]

✓ **Consistency:**
- Market ∈ [Africa, Europe, LATAM, Pacific Asia, USCA]
- Region maps to correct Market
- Customer Segment ∈ [Consumer, Corporate, Home Office]

✓ **Outlier Detection:**
- Days for shipping (real) > 60 days → Data anomaly
- Order Item Discount Rate > 100% → Impossible value
- Sales < $0 → Negative revenue (refund? cancellation?)

✓ **Lineage Tracking:**
- Every row must have source record ID from raw CSV
- Log all transformations with timestamp and data steward

### 4. Cross-Component Dependencies

**Power BI Dependency Chain:**
```
Data/Processed/* (CSV files)
    ↓ (imported via Power Query)
Power BI Data Model (relationships: dim_* ← fact_orders → *)
    ↓ (connected via relationships)
DAX Measures & Calculated Columns
    ↓ (visualized in)
Executive Dashboard Views
```

**Critical Dependency Rules:**
- If dim_geography changes, update Map visuals in PBIX
- If fact_orders schema changes, refresh all Power BI relationships
- Geographic validation MUST happen before dashboard refresh
- Revenue calculations MUST use processed Sales field, not raw

## Project-Specific Tasks

1. **Data Profiling:** Analyze distribution of `Late_delivery_risk` by market, segment, and product category
2. **Feature Engineering:** Create time-based features from `order date` (month, quarter, seasonality)
3. **Exploratory Analysis:** Identify drivers of late delivery (high discount rates, specific regions, etc.)
4. **Dashboard Iteration:** Update Power BI with new metrics and drill-down capabilities

## Cross-Component Dependencies
- Data dictionary (`DescriptionDataCoSupplyChain.csv`) is the source of truth for field semantics
- Power BI depends on processed data directory structure—ensure compatibility when modifying ETL
- Geographic validation against market list prevents downstream visualization errors

## File Structure Reference
```
Proyecto_TorreContol/
├── Data/
│   ├── Raw/                    # Source data (never modify)
│   │   ├── DataCoSupplyChainDataset.csv
│   │   ├── DescriptionDataCoSupplyChain.csv
│   │   └── tokenized_access_logs.csv
│   └── Processed/              # ETL output (create scripts here)
├── PBIX/
│   ├── TorreControl_v0.1.pbix  # Main dashboard
│   └── Emoticones/             # Custom visual assets
└── .github/
    └── copilot-instructions.md # This file
```

## Next Steps for Agents
- Create ETL pipeline to transform and enrich raw data
- Implement data quality checks and validation rules
- Develop feature engineering scripts for predictive modeling
- Extend Power BI dashboard with new visualizations based on processed data analysis
