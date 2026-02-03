# CONTEXTO ESTRATÉGICO - TORRE CONTROL
## Supply Chain Control Tower - Project Deep Context

**Documento:** Síntesis ejecutiva del contexto empresarial, preguntas estratégicas y arquitectura analítica del proyecto Torre Control

**Fecha:** 2 de Febrero de 2026  
**Estado:** Foundation Phase - Building Single Source of Truth

---

## 🎯 EL PROBLEMA EMPRESARIAL (The Business Case)

### Situación Crítica: Ceguera Operativa en DataCo Global

**DataCo Global** es una empresa internacional de retail y logística con presencia en múltiples regiones:
- ✓ Múltiples mercados activos (Africa, Europe, LATAM, Pacific Asia, USCA)
- ✓ Miles de SKUs en diferentes categorías (Furniture, Technology, Office Supplies)
- ✓ Segmentación de clientes (Consumer, Corporate, Home Office)
- ✓ Red de distribución compleja

**Pero está sangrando operativamente:**
- ❌ **Costos logísticos disparados** - Sin visibilidad de root causes
- ❌ **Entregas tardías** - % de OTIF desconocido, no hay trazabilidad
- ❌ **Quejas de clientes en máximo histórico** - Especialmente VIP (grandes cuentas corporativas)
- ❌ **Datos en silos** - ERP legacy exporta CSVs gigantes con 54 campos sin gobernanza
- ❌ **Decisiones a ciegas** - El COO (Chief Operating Officer) toma decisiones sin datos duros

### El Síntoma Inmediato
```
Legacy ERP Export (DataCoSupplyChainDataset.csv)
    ├─ 100K+ transacciones de órdenes
    ├─ Datos sin limpiar (duplicados, nulls, inconsistencias)
    ├─ Campos con espacios/caracteres especiales
    ├─ Sin referential integrity
    └─ RESULTADO: Gabinete de reportes Excel aislados e incompatibles
```

### El Impacto en Negocio
| Métrica | Estado | Impacto |
|---------|--------|--------|
| OTIF (On-Time In-Full) | **DESCONOCIDO** 🚨 | ¿Estamos entregando 80%? ¿40%? No sabemos |
| Revenue at Risk | **INVISIBLE** 🚨 | ¿Cuánto dinero perdemos en entregas tardías? |
| Customer Churn | **CRECIENDO** 📈 | Clientes VIP migrando a Amazon/competencia |
| Route Efficiency | **OPACA** 🚨 | ¿Hay "agujeros negros" de delivery en la red? |
| Fraud/Loss | **DESCONTROLADA** 🚨 | Órdenes "Lost", "Suspected Fraud" sin investigación |

---

## 🎯 LAS 5 PREGUNTAS ESTRATÉGICAS (Strategic Imperatives)

Cada pregunta responde a una decisión concreta que el COO necesita tomar **este trimestre**.

### Q1️⃣ VISIBILIDAD DE SERVICIO (OTIF)
> **"¿Cuál es nuestro porcentaje real de entregas perfectas (On-Time In-Full)? No quiero promedios globales, quiero saber dónde estamos fallando: ¿es en los envíos de 'Primera Clase' o en los 'Estándar'?"**

**Decisión:** Renegociar contratos con transportistas, ajustar SLAs, identificar portales regionales problemáticas

**Métrica Principal:**
```
OTIF% = (Entregas On-Time ✓ AND Entregas In-Full ✓) / Total de Órdenes × 100

On-Time:  Days for shipping (real) ≤ Days for shipment (scheduled)
In-Full:  Delivery Status ≠ ('Canceled' | 'Suspected Fraud')
```

**Desglose Requerido:**
- Global OTIF%
- OTIF% por Market (Africa, Europe, LATAM, Pacific Asia, USCA)
- OTIF% por Region (Southeast Asia, North Africa, East of USA, etc.)
- OTIF% por Customer Segment (Consumer vs Corporate vs Home Office)
- OTIF% por Product Category (Furniture vs Technology, etc.)
- Trend: Mes-a-mes, Año-a-año

**Dashboard View:**
```
┌─────────────────────────────────────────────┐
│ OTIF PERFORMANCE                       85.2% │
├─────────────────────────────────────────────┤
│                                             │
│  Market            OTIF%   Trend   Status  │
│  ─────────────────────────────────────────  │
│  Africa            72%      ↓ -3%   🔴 RED │
│  Europe            88%      ↑ +2%   🟢 OK  │
│  LATAM             91%      ↑ +5%   🟢 OK  │
│  Pacific Asia      78%      ↓ -1%   🟡 WARN│
│  USCA              84%      → ±0%   🟡 WARN│
│                                             │
│  [Drill-down: Click Africa → Ver Regions]  │
└─────────────────────────────────────────────┘
```

---

### Q2️⃣ FUGA DE INGRESOS (Revenue at Risk)
> **"¿Cuánto dinero estamos poniendo en riesgo por entregas tardías? ¿Son pedidos de $10 dólares o pedidos de $500 dólares los que llegan tarde?"**

**Decisión:** Priorizar despachos basados en valor monetario, implementar dinámicas de fulfillment por VIP

**Métrica Principal:**
```
Revenue at Risk ($) = SUM(Sales) WHERE Late_delivery_risk = 1

Revenue at Risk (%) = Revenue_at_Risk / Total_Revenue × 100

Average Order Value:
  - Late Orders:   $XXX
  - On-Time Orders: $YYY
  → ¿Las órdenes tardías son de menos valor? (Sistema trabajando mal con bajo valor)
```

**Desglose Requerido:**
- Total Revenue at Risk ($) - cantidad en dólares
- Revenue at Risk (%) del total
- Revenue at Risk por Market
- Revenue at Risk por Customer Segment (¿Corporate losing más que Consumer?)
- Top 10 Products/Categories perdiendo dinero por retrasos
- Customer Segment comparison: Corporate vs Consumer vs Home Office

**Dashboard View:**
```
┌──────────────────────────────────────────────────┐
│ REVENUE AT RISK                    $2.3M (-18%) │
├──────────────────────────────────────────────────┤
│                                                  │
│  Total Revenue:          $12.8M                 │
│  Revenue at Risk:        $2.3M  (18%)          │
│  Exposure per Order:     $450 avg              │
│                                                  │
│  By Segment:                                    │
│    Corporate:  $1.4M (61% at risk)  🔴 CRISIS  │
│    Consumer:   $0.7M (12% at risk)  🟡 WATCH  │
│    Home Off.:  $0.2M  (8% at risk)  🟢 OK     │
│                                                  │
│  Top Risk Markets:                              │
│    1. Africa       $680K                        │
│    2. Pacific Asia $510K                        │
│    3. LATAM        $390K                        │
└──────────────────────────────────────────────────┘
```

**Impacto:** Si Revenue at Risk baja de $2.3M a $1.8M = **$500K recuperados**

---

### Q3️⃣ RIESGO DE PÉRDIDA DE CLIENTES (Churn Risk)
> **"¿Quiénes son nuestros clientes más valiosos (Top 10% por ventas) que han sufrido retrasos en sus últimos 2 pedidos consecutivos? Necesito una lista para que Atención al Cliente los llame hoy."**

**Decisión:** Programa de retención VIP, ofertas de compensación, escalada ejecutiva

**Métrica Principal:**
```
VIP Customers at Risk = 
  WHERE Sales_per_Customer in Top 10% 
  AND Last_2_Orders.Late_delivery_risk = [1, 1]
  AND Recency < 30 days

Churn Risk Score = (Days_Late_Avg × Frequency_of_Delays) / LTV × 100
  → 0-30: Low risk
  → 30-70: Medium risk (monitor)
  → 70-100: HIGH RISK (act now)
```

**Desglose Requerido:**
- Lista de VIP clientes en riesgo (nombre, email, teléfono)
- Últimas 2 órdenes: fecha, demora (días), monto
- Total de dinero en riesgo (LTV × churn probability)
- Historial: ¿Cuántas veces ha experimentado retrasos en últimos 90 días?
- Segmento: ¿Corporate, Consumer?

**Dashboard View:**
```
┌─────────────────────────────────────────────────────┐
│ CHURN RISK - VIP AT RISK                    32 Co. │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Customer ID | Company Name   | Last 2 Orders | LTV │
│  ─────────────────────────────────────────────────  │
│  CUST-0045   | Acme Corp      | Late, Late   | $45K │
│  CUST-0127   | TechGlobal Inc | Late, Late   | $78K │
│  CUST-0089   | RetailMax      | Late, Late   | $62K │
│  CUST-0234   | BuildPro Ltd   | Late, On    | $35K │
│  ...                                            ... │
│                                                     │
│  Total LTV at Risk: $2.1M                          │
│  Recommended Action: Call today (Account Mgmt team)│
└─────────────────────────────────────────────────────┘
```

**Impacto:** Retener 1-2 cuentas VIP = preservar $50-100K revenue anual

---

### Q4️⃣ EFICIENCIA GEOGRÁFICA (Network Optimization)
> **"¿Existen 'Agujeros Negros' en nuestra red? ¿Hay mercados (ciudades/países) donde sistemáticamente fallamos los tiempos prometidos independientemente del producto?"**

**Decisión:** Cerrar rutas no rentables, reubicar centros de distribución, cambiar socios logísticos regionales

**Métrica Principal:**
```
OTIF% by Geography (drill-down):
  Market (Level 1)
    → Region (Level 2)
      → State/Country (Level 3)
        → City (Level 4)

Late Delivery Rate by Geography = Count(Late) / Count(Total) × 100

Pareto Analysis: 
  → 80% de entregas tardías vienen del 20% de ciudades/regiones?
```

**Desglose Requerido:**
- Mapa de calor: OTIF% por región (verde/amarillo/rojo)
- Drill-down: Click en mercado → Ver regiones → Click región → Ver ciudades
- Análisis: ¿La región "East of USA" tiene 100% puntualidad pero "West Africa" 45%?
- Correlación: ¿Problemas geográficos o de portista?
  - Si todas las ciudades de Brasil fallan = problema distribuidor Brasil
  - Si todas las ciudades del mismo portista fallan = cambiar portista
- Revenue concentration: ¿Está concentrado en regiones de alto riesgo?

**Dashboard View:**
```
┌────────────────────────────────────────────┐
│ GEOGRAPHIC HEATMAP                         │
├────────────────────────────────────────────┤
│                                            │
│  [Map Visual - Market Level]               │
│                                            │
│  Africa       🔴 72% (CRITICAL)           │
│    → West Africa    🔴 58%                │
│       → Lagos, Nigeria     45%            │
│       → Johannesburg, SA   72%            │
│    → North Africa   🟡 85%                │
│    → East Africa    🟢 88%                │
│                                            │
│  Europe       🟢 88% (OK)                 │
│  LATAM        🟢 91% (BEST)               │
│  Pacific Asia 🟡 78% (MONITOR)            │
│  USCA         🟡 84% (MONITOR)            │
│                                            │
│  [Click region to drill → see states/cities]
└────────────────────────────────────────────┘
```

**Impacto:** Reasignar $5M budget de logística de regiones problemáticas = mejorar OTIF global en 5-8%

---

### Q5️⃣ DETECCIÓN DE FRAUDE Y ANOMALÍAS
> **"¿Tenemos órdenes sospechosas o con estatus 'Lost' que no se están investigando? ¿Cuánto inventario estamos perdiendo?"**

**Decisión:** Auditoría interna, reducción de mermas, mejorar controles de inventario

**Métrica Principal:**
```
Inventory Loss ($) = SUM(Sales) WHERE Order_Status in ('SUSPECTED_FRAUD', 'LOST', 'CANCELED')

Anomaly Flags:
  - Days for shipping (real) > 60 days (¿en tránsito todavía?)
  - Order Item Discount Rate > 50% + Sales > $1000 (suspicious combo)
  - Status = 'SUSPECTED_FRAUD' + High discount
  - Refund patterns: Cliente recurrente de cancelaciones
```

**Desglose Requerido:**
- Total inventory loss por status
- Órdenes "Lost" sin investigación
- Órdenes sospechosas: Scatter plot (Discount % vs Order Value)
- Patrones de fraude: ¿Ciertos productos más vulnerables?
- Portistas/rutas con tasas de anomalía elevadas

**Dashboard View:**
```
┌──────────────────────────────────────────────┐
│ FRAUD & ANOMALIES                      $890K │
├──────────────────────────────────────────────┤
│                                              │
│  Total Inventory Loss:         $890K        │
│                                              │
│  By Order Status:                           │
│    SUSPECTED_FRAUD: $320K (36%) 🔴 CRITICAL│
│    LOST:            $280K (31%)            │
│    CANCELED:        $200K (22%)            │
│    PAYMENT_REVIEW:   $90K (10%)            │
│                                              │
│  Anomaly Flags:                             │
│    Days > 60 days:   [Scatter chart]       │
│      → 124 órdenes en este bucket          │
│      → Investigate: Contact carrier        │
│                                              │
│  Top Risk Products:                         │
│    1. Laptop Pro (high discount)            │
│    2. Office Chair Set                      │
│    3. Smartphone Bundle                     │
└──────────────────────────────────────────────┘
```

**Impacto:** Recuperar 30% de loss = $267K salvados

---

## 🏗️ ARQUITECTURA ANALÍTICA (Analytics Stack)

### Flujo Datos: Raw → Processed → Insights

```
LAYER 1: INGESTION (Raw Data)
┌─────────────────────────────────────────────────────────────┐
│ Data/Raw/DataCoSupplyChainDataset.csv (100K+ rows, 54 cols) │
│ • Dirty, unstructured, no governance                       │
│ • Field names: "Days for shipping (real)", etc.            │
│ • Nulls, duplicates, mixed data types                      │
└─────────────────────────────────────────────────────────────┘
                           ⬇️ ETL PIPELINE

LAYER 2: TRANSFORMATION (Single Source of Truth)
┌─────────────────────────────────────────────────────────────┐
│ Data/Processed/ - Star Schema Data Model                   │
│                                                             │
│ DIMENSIONS:                                                │
│ ├─ dim_customer.csv (customer_id, segment, ltv)           │
│ ├─ dim_product.csv (product_id, category, price)          │
│ ├─ dim_geography.csv (market, region, state, city)        │
│ └─ dim_date.csv (date_key, month, quarter, year)          │
│                                                             │
│ FACTS:                                                     │
│ └─ fact_orders.csv (order_id, customer_id, product_id,    │
│                     market_key, date_key, sales, otif_flag)│
│                                                             │
│ QUALITY:                                                   │
│ ├─ No nulls in critical fields                            │
│ ├─ Referential integrity (all FKs valid)                 │
│ ├─ Quality flags: _is_valid, _is_outlier                 │
│ └─ Lineage tracking: Source record ID                     │
└─────────────────────────────────────────────────────────────┘
                           ⬇️ POWER BI

LAYER 3: VISUALIZATION (Executive Decision Layer)
┌─────────────────────────────────────────────────────────────┐
│ PBIX/TorreControl_v0.1.pbix - 5 Executive Dashboards       │
│                                                             │
│ View 1: OTIF Performance    (Q1)                          │
│ View 2: Revenue at Risk     (Q2)                          │
│ View 3: Churn Risk (VIP)    (Q3)                          │
│ View 4: Geographic Heatmap  (Q4)                          │
│ View 5: Anomaly Detection   (Q5)                          │
│                                                             │
│ Interactivity:                                            │
│ • Date range slicer (global)                             │
│ • Market/Region/Segment filters                          │
│ • Drill-down: Map (click market → regions → cities)      │
│ • Export to Excel: VIP lists, detailed reports           │
└─────────────────────────────────────────────────────────────┘
                           ⬇️ ACTION

LAYER 4: DECISION & ACTION (Business Outcomes)
┌─────────────────────────────────────────────────────────────┐
│ Executive Decisions Made:                                  │
│ • COO renegociates carrier contracts (Q1 insight)          │
│ • Operations prioritizes high-value routes (Q2)            │
│ • Account management calls VIP clients (Q3)                │
│ • Supply chain adjusts distribution network (Q4)           │
│ • Finance audits suspected fraud (Q5)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📅 ROADMAP DE IMPLEMENTACIÓN

### PHASE 1: FOUNDATION (Semanas 1-3)
**Objetivo:** Construir Single Source of Truth

**Hitos:**
1. ✅ Crear ETL pipeline base (etl_pipeline.py)
2. ✅ Modelar star schema (dim_* + fact_orders)
3. ✅ Implementar data quality checks
4. ✅ Exportar Data/Processed/* CSVs
5. ✅ Documentar field mappings (raw → processed)

**Success Criteria:**
- [ ] fact_orders.csv ready for Power BI import
- [ ] 0 nulls in critical fields (Late_delivery_risk, Customer ID, Sales)
- [ ] Geographic validation passed (all markets valid)
- [ ] ETL runs daily without errors

---

### PHASE 2: DASHBOARDING (Semanas 4-6)
**Objetivo:** Reemplazar Excel con Power BI real-time insights

**Hitos:**
1. ✅ Refresh Power BI data model (import CSVs)
2. ✅ Build 5 executive views (one per Q)
3. ✅ Add interactivity (slicers, drill-down)
4. ✅ Configure auto-refresh schedule
5. ✅ Train executive team on dashboard usage

**Success Criteria:**
- [ ] All 5 views operational
- [ ] Dashboard loaded in <5 seconds
- [ ] Drill-down working (Market → Region → State → City)
- [ ] Executives using dashboard daily

---

### PHASE 3: ADVANCED ANALYTICS (Semanas 7+)
**Objetivo:** Predictive & prescriptive intelligence

**Hitos:**
1. ✅ Build predictive model (Late delivery risk)
2. ✅ Scenario planning (What-if analysis)
3. ✅ Route optimization recommendations
4. ✅ Automated alerts (OTIF drops below 80%, etc.)

---

## 🔑 CONCEPTOS CLAVE PARA AGENTES IA

### 1. OTIF es la Brújula Estratégica
- No es solo un KPI, es la métrica de salud operativa
- On-Time AND In-Full (ambas condiciones deben cumplirse)
- Desglosable por geografía, segmento, categoría
- El objetivo: 95%+ OTIF global

### 2. Revenue at Risk es el Lenguaje del Negocio
- Los ejecutivos entienden $$$, no percentages
- $2.3M at risk = equivale a renegociar contratos
- $500K recovered = invertir en mejor servicio se justifica
- Corporate segment es más sensible a retrasos (presión a pagar premium)

### 3. Geografía es un Cristal de Expectativas Diferentes
- Cada mercado tiene dinámicas diferentes (carrier capacity, infrastructure)
- Africa 72% OTIF ≠ LATAM 91% OTIF por misma razón
- No es "nuestro sistema está roto globalmente", es "roto en X región"
- Soluciones geográficas: Cambiar distribuidor, inversión local, ajustar SLA

### 4. Churn Paradoja: Los Clientes Más Grandes Son los Más Vulnerables
- Corporate segment es 61% de Revenue at Risk
- Son también clientes más valiosos (LTV más alto)
- "Llama a este cliente HOY" lista es operación de salvamento
- Alternativa: Amazon/Alibaba listos para robar accounts

### 5. Data Quality es Existencial
- Garbage in = Garbage out
- Si Days for shipping (real) > 60 days, ¿qué pasó? ¿Perdida? ¿Carrier delay?
- Un solo Late_delivery_risk = 0 mal codificado contamina análisis completo
- Validación cruzada: Late_delivery_risk vs Delivery_Status (¿son consistentes?)

### 6. Descentralización Deliberada: Mercados Independientes
- No es "un algoritmo para toda la empresa"
- Es "5 algoritmos, uno por mercado" + decisiones ajustadas regionalmente
- Central Tower ← Reporta a → Operaciones Regionales
- Flexibilidad > Homogeneidad en este contexto

---

## 💡 REFLEXIONES FINALES

**¿Por qué esto es más que "hacer gráficas"?**

Esta es una **misión de remediación operativa**. DataCo está en crisis de servicio. Sin esta Torre de Control:
- El COO sigue tomando decisiones a ciega
- El cliente VIP se va con Amazon
- La logística gasta $$ sin saber dónde
- El fraud crece sin detección

Con Torre de Control:
- COO tiene el tablero de mandos operativo
- Operaciones puede actuar sobre datos, no intuición
- VIP retention se activa proactivamente
- Logistics cost optimizes by data, not tradition

**El verdadero éxito no es un dashboard bonito. Es cuando el COO dice:**

> *"La semana pasada, vi que Africa estaba en 72% OTIF. Llamé al distribuidor regional, renegociamos el contrato. Hoy estamos en 81%. Revenue at Risk bajó $150K. Y mis cuentas VIP dejan de quejar"*

Eso es éxito. Todo lo demás es medio.

---

**Última actualización:** 2 de Febrero de 2026  
**Autor:** Lead Data Analyst (You)  
**Próxima revisión:** Después de Phase 1 completion
