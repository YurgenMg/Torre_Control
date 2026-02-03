# ⚡ FASE 4 EXECUTION SUMMARY
## Ready-to-Go Power BI Dashboard Implementation

**Status:** Ready to Begin (All data prepared)  
**Time Required:** 45 minutes  
**Difficulty:** Moderate (Detailed step-by-step provided)

---

## 📋 BEFORE YOU START

### ✅ Checklist: Do You Have These?

```bash
# 1. PostgreSQL running
docker ps | findstr "supply_chain_db"
→ Should show: supply_chain_db ... 0.0.0.0:5433->5432/tcp

# 2. Verify data exists
docker exec supply_chain_db psql -U admin -d supply_chain_dw -c "SELECT COUNT(*) FROM dw.vw_vip_churn_risk;"
→ Should show: 3658

# 3. Power BI Desktop installed
→ Check Applications or search "Power BI" in Start menu

# 4. PostgreSQL ODBC Driver installed (for Windows)
→ If missing: https://www.postgresql.org/ftp/odbc/versions/msi/
```

**If all green, proceed to Step 1.**

---

## 🚀 STEP-BY-STEP EXECUTION

### STEP 1: Launch Power BI Desktop

```
1. Open Power BI Desktop
2. Click File → New
3. Close welcome screens
```

**Screenshot Point:** Title bar shows "Power BI Desktop"

---

### STEP 2: Get Data from PostgreSQL

```
1. In ribbon, click: Get Data
2. Search: "PostgreSQL"
3. Click: PostgreSQL database
4. Click: Connect
```

**Input Dialog:**

```
Server:             localhost:5433
Database:           supply_chain_dw
Port:               (auto-populated: 5433)
Data Connectivity:  Import ← SELECT THIS
```

Click: **OK**

**Authentication Dialog:**

```
Username:   admin
Password:   admin123
□ Use Windows authentication (leave unchecked)
```

Click: **Connect**

**Result:** ✅ "Connection successful"

---

### STEP 3: Select Tables to Import

**Navigator window shows list:**

Expand: `dw` (schema)

**Check THESE 4 views:**

```
☑ dw.vw_vip_churn_risk
☑ dw.vw_pareto_delays
☑ dw.vw_market_diagnostics
☑ dw.vw_temporal_trends
```

**Optional (leave unchecked):**
```
☐ dim_customers
☐ dim_geography
☐ dim_date
☐ fact_orders
☐ stg_raw_orders
```

Click: **Load**

---

### STEP 4: Wait for Data Import

**Power Query Editor opens automatically**

You should see 4 tables:
```
✓ dw_vw_vip_churn_risk
✓ dw_vw_pareto_delays
✓ dw_vw_market_diagnostics
✓ dw_vw_temporal_trends
```

**Important:** Verify column data types. For each table:

1. Click table name
2. Check **Applied Steps** on right
3. Review **Column Types** (should already be correct):
   - Numeric fields → "Whole Number" or "Fixed Decimal"
   - Text fields → "Text"
   - Dates → "Date" or "Text" (okay either way)

**If types are wrong:** Right-click column → **Change Type** → Select correct type

Click: **Close & Apply**

---

### STEP 5: Build Dashboard Layout (4 Zones)

**You're now in Power BI Report Editor (blank report)**

#### ZONE 1: KPI Metrics (Top Row)

**Add 4 Cards**

**Card 1: OTIF %**
1. Insert → Card (visual type)
2. Drag to position: Top-left, width 25%
3. Fields panel: Drag `vw_temporal_trends` → `otif_pct`
4. Format:
   - Data labels: ON, Font size 48pt, Bold
   - Title: "OTIF %"
   - Background: Light gray

**Card 2: Revenue at Risk**
1. Insert → Card
2. Position: Top, 25-50%
3. Create DAX measure first:
   ```dax
   Revenue@Risk = SUMPRODUCT(dw_vw_market_diagnostics[revenue_at_risk])
   ```
4. Fields: Drag measure
5. Format: Title "Revenue@Risk", Currency format, 48pt
6. Background: Light gray

**Card 3: Late Orders**
1. Insert → Card
2. Position: Top, 50-75%
3. Create DAX measure:
   ```dax
   Total Late = 
     SUMPRODUCT(
       dw_vw_pareto_delays[late_orders]
     )
   ```
4. Fields: Drag measure
5. Format: 48pt, title "Late Orders"

**Card 4: VIP Count**
1. Insert → Card
2. Position: Top-right, 75-100%
3. Fields: Drag `vw_vip_churn_risk` → any field, Count
4. Format: 48pt, title "VIPs@Risk"

---

#### ZONE 2: Market Performance (Left 50%)

1. Insert → **Horizontal Bar Chart**
2. Position: Left side, below KPI row
3. Fields:
   - **Axis:** `vw_market_diagnostics` → `market`
   - **Value:** `vw_market_diagnostics` → `late_rate_pct`
4. Sort: Value descending (worst on top)
5. Format:
   - Title: "Market Performance"
   - Data labels: ON
   - Color scale: Green (30%) → Red (70%)

---

#### ZONE 3: VIP Action List (Right 50%)

1. Insert → **Table**
2. Position: Right side, below KPI row
3. Fields (in this order):
   - `vw_vip_churn_risk` → `full_name`
   - `vw_vip_churn_risk` → `segment`
   - `vw_vip_churn_risk` → `total_spent_usd`
   - `vw_vip_churn_risk` → `failure_rate_pct`
   - `vw_vip_churn_risk` → `risk_level`
4. Format:
   - Title: "VIP Churn Risk List"
   - Sort: `total_spent_usd` descending
   - Conditional formatting on `risk_level`:
     - "CRITICAL" → Red background
     - "HIGH" → Orange background
   - Rows to display: 15

---

#### ZONE 4: Pareto Root Cause (Bottom Full Width)

1. Insert → **Combo Chart** (Clustered Column + Line)
2. Position: Bottom, full width
3. Shared Axis (X-axis):
   - `vw_pareto_delays` → `product_name` (limit to top 15)
4. Column Values:
   - `vw_pareto_delays` → `late_orders`
5. Line Values:
   - `vw_pareto_delays` → `cumulative_pct`
6. Format:
   - Title: "Pareto: 7 Products = 80% of Delays"
   - Sort X: `late_orders` descending
   - Line color: Red, thickness 3pt
   - Column color: Blue

---

### STEP 6: Add Interactive Slicers

**Add 3 filters at the very top**

**Slicer 1: Market Filter**
1. Insert → Slicer (Dropdown type)
2. Field: `vw_market_diagnostics` → `market`
3. Position: Top-left, width 20%
4. Format: Title "Filter by Market"
5. Connect to: All visuals (slicers auto-connect usually)

**Slicer 2: Risk Level Filter**
1. Insert → Slicer (Buttons type)
2. Field: `vw_vip_churn_risk` → `risk_level`
3. Position: Top-center, width 30%
4. Format: Horizontal buttons, selectable multiple
5. Title: "Filter by VIP Risk Level"

**Slicer 3: Month Selector (optional)**
1. Insert → Slicer (Dropdown type)
2. Field: `vw_temporal_trends` → `month_year`
3. Position: Top-right, width 20%
4. Format: Title "Date Range"

---

### STEP 7: Validate Numbers

**Compare Dashboard to Expected Results**

| Visual | Expected Value | Dashboard Shows | Match? |
|--------|-----------------|-----------------|--------|
| OTIF Card | 40.86% | ? | ✓/✗ |
| Revenue@Risk | $21,720,882.82 | ? | ✓/✗ |
| Late Orders | 106,927 | ? | ✓/✗ |
| VIP Count | 3,658 | ? | ✓/✗ |
| Top Product | Perfect Fitness... | ? | ✓/✗ |

**If all match:** ✅ Dashboard validated!

**If something doesn't match:** 
- Right-click visual → "Drill through" to investigate
- Check measure definitions
- Verify PostgreSQL connection is live

---

### STEP 8: Save Dashboard

```
File → Save As
Filename:      TorreControl_Dashboard_Phase4.pbix
Location:      C:\Proyecto_TorreControl\PBIX\
```

**Expected:** File saved, 20-50 MB

---

### STEP 9: Take Screenshot for Portfolio

```
1. View → Reading View (removes editing toolbar)
2. Windows + Shift + S (Screenshot tool)
3. Drag to select entire dashboard
4. Save as: dashboard_screenshot.png
5. Location: C:\Proyecto_TorreControl\PBIX\
```

---

## 🎯 FINAL CHECKLIST

```
Dashboard Creation:
[ ] Connected to PostgreSQL (localhost:5433)
[ ] Imported 4 views (vw_vip_churn_risk, vw_pareto_delays, etc.)
[ ] Power Query validated (correct data types)

Layout & Visuals:
[ ] Zone 1 KPI Cards: OTIF, Revenue@Risk, Late Orders, VIPs (4 cards)
[ ] Zone 2 Market Bar Chart: Shows all 5 markets, sorted descending
[ ] Zone 3 VIP Table: Shows 15 VIPs, sorted by spend descending
[ ] Zone 4 Pareto Combo: Shows product late orders + cumulative %

Interactivity:
[ ] Market slicer working (filters bar chart + table)
[ ] Risk level slicer working (filters VIP table)
[ ] Month slicer working (if added)

Validation:
[ ] OTIF % = 40.86%
[ ] Revenue@Risk = $21,720,882.82 (or similar scale)
[ ] Late Orders = 106,927 (or match query)
[ ] VIP Count = 3,658
[ ] Top product = Perfect Fitness Rip Deck

Deliverables:
[ ] File saved: TorreControl_Dashboard_Phase4.pbix
[ ] Screenshot saved: dashboard_screenshot.png
[ ] Both files in: C:\Proyecto_TorreContol\PBIX\
```

---

## 🔧 TROUBLESHOOTING

**Problem:** "PostgreSQL driver not found"

```
Solution:
1. Download: https://www.postgresql.org/ftp/odbc/versions/msi/
2. Install: psqlodbc_15_00_0000-x64.msi
3. Restart Power BI Desktop
4. Try again
```

---

**Problem:** "Connection timeout"

```
Solution:
1. Check Docker: docker ps
2. If missing, restart: docker-compose -f docker-compose.yml up -d
3. Wait 30 seconds
4. Retry connection in Power BI
```

---

**Problem:** "Table not found" or "Empty results"

```
Solution:
1. Verify views exist:
   docker exec supply_chain_db psql -U admin -d supply_chain_dw -c "
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'dw' AND table_name LIKE 'vw_%';"

2. Should show 4 results (vw_vip_churn_risk, etc.)
3. If missing, run: cat sql/queries/05_deep_dive_analytics.sql | docker exec -i supply_chain_db psql -U admin -d supply_chain_dw
```

---

**Problem:** "Numbers don't match between dashboard and expected"

```
Solution:
1. Refresh data: Click Data view → Right-click table → Refresh
2. Wait 30 seconds
3. Return to Report view
4. Check if numbers updated
5. If still wrong, verify PostgreSQL data:
   docker exec supply_chain_db psql -U admin -d supply_chain_dw -c "SELECT * FROM dw.vw_pareto_delays LIMIT 1;"
```

---

## 📞 SUPPORT

**All queries are well-tested and ready.** If you encounter issues:

1. **Check PostgreSQL connection first** (most common issue)
2. **Verify views exist** in database
3. **Refresh Power BI data**
4. **Check data types** in Power Query
5. **Validate DAX measures** if using custom calculations

---

## 🏆 SUCCESS CRITERIA

**Phase 4 is complete when:**

✅ Power BI dashboard displays all 4 zones  
✅ Numbers match database queries  
✅ Pareto chart clearly shows 7 products = 80% delays  
✅ VIP table shows top 15 customers at risk  
✅ All slicers work interactively  
✅ File saved and screenshot captured  

---

**Time to Completion:** 45-60 minutes  
**Difficulty Level:** Intermediate  
**Portfolio Value:** ⭐⭐⭐⭐⭐ (Executive dashboard = strong hire signal)

**Go build! 🚀**

---

*Fase 4 Execution Guide - Torre Control Project*  
*Status: READY TO EXECUTE*
