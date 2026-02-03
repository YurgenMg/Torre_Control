# 📊 GUÍA: CONECTAR POWER BI A POSTGRESQL - FASE 4

**Objetivo:** Importar vistas SQL a Power BI y crear dashboard ejecutivo  
**Tiempo Estimado:** 45 minutos  
**Status:** Listo para ejecutar

---

## ✅ PRE-REQUISITOS

Verificar que tengas:

```bash
# Terminal: Verificar que PostgreSQL está corriendo en puerto 5433
docker ps | findstr "supply_chain_db"
# Debe mostrar: ... supply_chain_db ... ports: 0.0.0.0:5433->5432/tcp

# Terminal: Verificar conexión a BD
docker exec supply_chain_db psql -U admin -d supply_chain_dw -c "SELECT COUNT(*) FROM dw.fact_orders;"
# Debe mostrar: 186638
```

**Instalados Localmente:**
- ✅ Power BI Desktop (versión actual)
- ✅ PostgreSQL ODBC Driver (para Windows)
- ✅ Credenciales: User: `admin`, Pass: `admin123`

---

## 📥 PASO 1: CONECTAR A POSTGRESQL DESDE POWER BI

### 1.1 Abre Power BI Desktop

1. Click **File** → **New**
2. En la pantalla inicial, click **Get Data**
3. En search box, busca **"PostgreSQL"**
4. Click **PostgreSQL database** → **Connect**

### 1.2 Ingresa Credenciales de Conexión

```
Server:          localhost:5433
Database:        supply_chain_dw
Port:            5433 (default)
Username:        admin
Password:        admin123
Data Connectivity mode: Import  ← IMPORTANTE: Import, no DirectQuery
```

**Resultado esperado:** "Connection successful" ✅

---

## 🔗 PASO 2: SELECCIONAR VISTAS PARA IMPORTAR

Una vez conectado, verás lista de todas las tablas y vistas.

**Selecciona SOLO estas 4 vistas** (hacer check mark):

```
☑ dw.vw_vip_churn_risk
☑ dw.vw_pareto_delays
☑ dw.vw_market_diagnostics
☑ dw.vw_temporal_trends
```

**Opcional (para referencia):**
```
☑ dw.dim_customers
☑ dw.dim_geography
☐ dw.dim_date (si necesitas)
☐ dw.fact_orders (muy grande - solo si necesitas granular)
```

Click **Load** para importar.

---

## ⏳ PASO 3: POWER QUERY TRANSFORMATIONS (Mínimas)

Una vez que se importan las vistas:

1. Power BI abre **Power Query Editor**
2. Para cada vista, click **Applied Steps** en lado derecho
3. Verificar que todas las columnas tienen **tipos de datos correctos**:

```
dw.vw_vip_churn_risk:
  ✓ customer_key     → Whole Number
  ✓ full_name        → Text
  ✓ total_spent_usd  → Fixed Decimal
  ✓ failure_rate_pct → Fixed Decimal
  ✓ risk_level       → Text
  
dw.vw_pareto_delays:
  ✓ product_name     → Text
  ✓ late_orders      → Whole Number
  ✓ contribution_pct → Fixed Decimal
  ✓ cumulative_pct   → Fixed Decimal
  
dw.vw_market_diagnostics:
  ✓ market           → Text
  ✓ revenue_at_risk  → Fixed Decimal
  ✓ late_rate_pct    → Fixed Decimal
  
dw.vw_temporal_trends:
  ✓ month_year       → Text (o Date si es posible)
  ✓ otif_pct         → Fixed Decimal
```

**Acción:** Si alguna columna tiene tipo errado, click columna → **Change Type** → seleccionar tipo correcto.

Click **Close & Apply** cuando termines.

---

## 🎨 PASO 4: CREAR ESTRUCTURA DE DASHBOARD (4 Zonas)

### Dashboard Layout

```
┌────────────────────────────────────────────────────────────────┐
│ ZONA 1: KPI METRICS (Top Row)                                  │
├──────────────────┬──────────────────┬──────────────────┬────────┤
│ OTIF %           │ Revenue at Risk  │ Late Orders      │ VIPs   │
│ 40.86%           │ $21.7M           │ 106,927          │ 3,658  │
│ 🔴 RED (Critical) │ 🔴 RED          │ 🟠 ORANGE        │ 🔴 RED │
└──────────────────┴──────────────────┴──────────────────┴────────┘

┌────────────────────────────────────────────────────────────────┐
│ ZONA 2: DIAGNOSTICS (Left 50%)                                 │
├──────────────────────────────────┬──────────────────────────────┤
│ Market Performance               │ ZONA 3: ACTION LIST           │
│ (Horizontal Bar Chart)           │ (VIP Churn Risk Table)        │
│                                  │                              │
│ Europe    ███████ 57.69%        │ Rank │ Customer │ Spent │   │
│ LATAM     ███████ 57.02%        │ 1    │ Mary H.  │$9.7K  │   │
│ Pacific   ███████ 57.32%        │ 2    │ Teresa G │$10.2K │   │
│ USCA      ███████ 57.24%        │ 3    │ Paul S.  │$11.0K │   │
│ Africa    ███████ 56.81%        │ ...  │  ...     │  ...  │   │
│                                  │ 15   │ Judy M.  │$9.6K  │   │
└──────────────────────────────────┴──────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ ZONA 4: ROOT CAUSE ANALYSIS (Bottom Full Width)               │
├────────────────────────────────────────────────────────────────┤
│ Pareto Chart: Top 10 Productos Causando Retrasos              │
│                                                               │
│ Perfect Fitness Rip   ██████████████ 13.60%  Cumul: 13.60%   │
│ Nike CJ Elite Cleat   █████████████  12.26%  Cumul: 25.86%   │
│ Nike Dri-FIT Polo     ███████████    11.67%  Cumul: 37.52%   │
│ O'Brien Life Vest     ██████████     10.72%  Cumul: 48.24%   │
│ Field & Stream Safe   █████████      9.63%   Cumul: 57.87%   │
│ [... 5 más productos...]                                     │
│                                                               │
│ → Total: 7 productos = 74% de TODOS los retrasos             │
└────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ PASO 5: CREAR VISUALIZACIONES (Detailed Instructions)

### ZONA 1: KPI Cards (Top Row)

**Card 1: OTIF %**

1. Click **Insert** → **Card** (visual type)
2. Drag to top-left corner
3. In **Fields**, drag: `vw_market_diagnostics` → `otif_pct` (pero primero necesitas crear medida)
4. Click **Format** → **Data Labels** → Font size 60pt, Bold

*Nota: Si no tienes `otif_pct` directo, crear medida:*

```dax
OTIF % = 
  DIVIDE(
    COUNTROWS(FILTER(dw_fact_orders, [is_otif] = TRUE)),
    COUNTROWS(dw_fact_orders)
  ) * 100
```

**Card 2: Revenue at Risk**

```dax
Revenue@Risk = 
  SUMPRODUCT(
    dw_vw_market_diagnostics[revenue_at_risk]
  )
```

**Card 3: Late Orders Count**

```dax
Late Orders = 
  COUNTROWS(FILTER(dw_fact_orders, [is_late] = TRUE))
```

**Card 4: VIP Count**

```dax
VIPs@Risk = COUNTROWS(dw_vw_vip_churn_risk)
```

---

### ZONA 2: Market Performance (Horizontal Bar Chart)

1. Click **Insert** → **Horizontal Bar Chart**
2. Axis: `vw_market_diagnostics` → `market`
3. Value: `vw_market_diagnostics` → `late_rate_pct`
4. Sort: Descending (worst on top)
5. Format: Color scale from 🟢 Green (30%) → 🔴 Red (60%)

---

### ZONA 3: VIP Action List (Table Visual)

1. Click **Insert** → **Table**
2. Fields:
   - `vw_vip_churn_risk` → `full_name`
   - `vw_vip_churn_risk` → `segment`
   - `vw_vip_churn_risk` → `total_spent_usd` (formato: Currency)
   - `vw_vip_churn_risk` → `failure_rate_pct` (formato: Decimal, 1 lugar)
   - `vw_vip_churn_risk` → `risk_level`

3. Sort: `total_spent_usd` Descending (VIPs de mayor gasto arriba)
4. Filter: `risk_level` = "CRITICAL" o "HIGH" (optional)
5. Conditional Formatting en `risk_level`:
   - "CRITICAL" → Red background
   - "HIGH" → Orange background
   - "MEDIUM" → Yellow background

---

### ZONA 4: Pareto Chart (Clustered Column + Line)

1. Click **Insert** → **Combo Chart**
2. Shared Axis (X): `vw_pareto_delays` → `product_name` (top 10)
3. Column Values: `vw_pareto_delays` → `late_orders`
4. Line Values: `vw_pareto_delays` → `cumulative_pct`
5. Sort X axis: `late_orders` Descending

**Result:** Columns decrecientes con línea roja mostrando acumulado (sube hasta ~80%)

---

## 🎯 PASO 6: AGREGAR SLICERS (Filtros Interactivos)

En la parte superior del dashboard, agregar:

1. **Date Slicer** (para filtrar por mes)
   - Visual: **Slicer** → Type: **Between**
   - Field: `vw_temporal_trends` → `month_year`

2. **Market Slicer**
   - Visual: **Slicer** → Type: **Dropdown**
   - Field: `vw_market_diagnostics` → `market`
   - Selectable: Multiple

3. **Risk Level Slicer**
   - Visual: **Slicer** → Type: **Buttons**
   - Field: `vw_vip_churn_risk` → `risk_level`

---

## 💾 PASO 7: GUARDAR Y PUBLICAR

1. Click **File** → **Save As**
2. Nombre: `TorreControl_Dashboard_Phase4.pbix`
3. Ubicación: `C:\Proyecto_TorreContol\PBIX\`

```
✅ Local file saved: TorreControl_Dashboard_Phase4.pbix (15-50 MB)
```

**Opcional - Publicar a Power BI Service:**

```
File → Publish → Select Workspace → [Esperar 2-3 min]
Resultado: Dashboard disponible en app.powerbi.com
```

---

## 🔍 PASO 8: VALIDAR DATOS EN DASHBOARD

Una vez que el dashboard está hecho, verificar números:

| Métrica | Dashboard | Base de Datos | Status |
|---------|-----------|---------------|--------|
| OTIF % | ? | 40.86% | ✓ Match? |
| Revenue@Risk | ? | $21.7M | ✓ Match? |
| Late Orders | ? | 106,927 | ✓ Match? |
| VIPs@Risk | ? | 3,658 | ✓ Match? |
| Top Product | ? | Perfect Fitness Rip | ✓ Match? |

Si todos los números coinciden → ✅ **Dashboard validado**

---

## 🎉 PASO 9: SCREENSHOT PARA PORTFOLIO

Una vez que el dashboard se ve bien:

1. Click **View** → **Reading View** (presentation mode)
2. Press **Windows + Shift + S** (screenshot tool)
3. Seleccionar toda el área del dashboard
4. Guardar como: `dashboard_screenshot.png`
5. Copiar a: `Proyecto_TorreContol/PBIX/`

---

## 📋 CHECKLIST DE FINALIZACIÓN

```
[ ] PostgreSQL corriendo en puerto 5433
[ ] 4 vistas importadas a Power BI (OK)
[ ] Tipos de datos correctos en Power Query (OK)
[ ] 4 Zonas de visualización creadas:
    [ ] Zone 1: KPI Cards (OTIF, Revenue@Risk, Late Orders, VIPs)
    [ ] Zone 2: Market Performance (Bar chart)
    [ ] Zone 3: VIP Action List (Table)
    [ ] Zone 4: Pareto Chart (Root causes)
[ ] Slicers añadidos (Date, Market, Risk Level)
[ ] Números validados vs Base de Datos
[ ] Dashboard guardado: TorreControl_Dashboard_Phase4.pbix
[ ] Screenshot tomado: dashboard_screenshot.png
[ ] Versión lista para portfolio ✅
```

---

## 🚀 SI ALGO FALLA

### Error: "PostgreSQL driver not found"

```powershell
# Descargar ODBC Driver from:
# https://www.postgresql.org/ftp/odbc/versions/msi/

# Instalar: psqlodbc_15_00_0000-x64.msi
# Reiniciar Power BI Desktop
```

### Error: "Connection timeout"

```bash
# Verificar que Docker está corriendo:
docker ps

# Si no, reiniciar:
docker-compose -f docker-compose.yml up -d
```

### Error: "Table not found"

```bash
# Verificar que las vistas existen:
docker exec supply_chain_db psql -U admin -d supply_chain_dw -c "
  SELECT table_schema, table_name FROM information_schema.tables 
  WHERE table_schema = 'dw' AND table_name LIKE 'vw_%';"
```

---

**¡Estás listo! Procede con los 9 pasos y habrás completado Fase 4 con honors! 🏆**

*Documento: Power BI Connection Guide - Torre Control Project*  
*Fase: 4 Visualization (READY TO EXECUTE)*
