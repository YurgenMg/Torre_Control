# Transform Data Pipeline - Technical Guide
## `scripts/transform_data.py`

**Versión:** 1.0  
**Fecha:** 4 de febrero de 2026  
**Estado:** ✅ Production Ready  

---

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Funciones Principales](#funciones-principales)
4. [Flujo ETL](#flujo-etl)
5. [Validaciones Críticas](#validaciones-críticas)
6. [Cómo Ejecutar](#cómo-ejecutar)
7. [Monitoreo y Logs](#monitoreo-y-logs)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Descripción General

`transform_data.py` es el **orquestador central del ETL** que convierte datos crudos del staging en un **Star Schema analítico** listo para Power BI.

### Flujo de Datos

```
CSV Raw (DataCoSupplyChainDataset.csv)
            ↓
    PostgreSQL Staging (dw.stg_raw_orders)
            ↓
    TRANSFORM PIPELINE (scripts/transform_data.py)
            ├─ Populate Dimensions (customer, product, geography, date)
            └─ Populate Facts (fact_orders con métricas calculadas)
            ↓
    Power BI-Ready Star Schema
            ├─ dim_customer.csv
            ├─ dim_product.csv
            ├─ dim_geography.csv
            ├─ dim_date.csv
            └─ fact_orders.csv
```

### Características Clave

✅ **Batch Processing** - Procesa miles de filas eficientemente con `tqdm`  
✅ **Transactional Integrity** - Usa transacciones explícitas para rollback en caso de error  
✅ **Audit Trail** - `etl_run_id` (UUID) para rastrear qué corre en cada ejecución  
✅ **Lookups Eficientes** - Diccionarios en memoria para mapeos FK  
✅ **Validación de Datos** - NULLs, outliers, anomalías  
✅ **Logging Detallado** - Timestamps, contadores, métricas KPI  

---

## 🏗️ Arquitectura

### Componentes

| Componente | Propósito | Salida |
|------------|-----------|--------|
| `populate_dim_customer()` | Extraer clientes únicos, calcular LTV | `{customer_id: customer_key}` lookup |
| `populate_dim_geography()` | Crear jerarquía geográfica (Market→Region→State→City) | `{(market, region, ...): geography_id}` lookup |
| `populate_dim_product()` | Extraer productos únicos | `{product_card_id: product_key}` lookup |
| `populate_dim_date()` | Generar calendario completo con atributos temporales | `{order_date: date_id}` lookup |
| `populate_fact_orders()` | JOIN staging con dims, calcular métricas, insertar hechos | Row count + KPIs |
| `run_etl_pipeline()` | Orquestar secuencia, manejo de errores, auditoría | Exit code (0=éxito) |

### Dependencias

```python
# SQLAlchemy - Database ORM
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# pandas - Data transformation
import pandas as pd

# tqdm - Progress bars
from tqdm import tqdm

# Standard library
import logging, uuid, os, pathlib, datetime
```

### Base de Datos

```sql
-- Connection
postgresql://admin:adminpassword@localhost:5433/supply_chain_dw

-- Staging Table (Input)
dw.stg_raw_orders (54 campos)

-- Dimension Tables (Output)
dw.dim_customer
dw.dim_product
dw.dim_geography
dw.dim_date

-- Fact Table (Output)
dw.fact_orders
```

---

## 🔧 Funciones Principales

### 1. `populate_dim_customer(engine)`

**Propósito:** Extraer clientes únicos del staging y crear tabla de dimensión.

**Lógica:**
1. SELECT DISTINCT customer_id, fname, lname, email, segment desde `stg_raw_orders`
2. GROUP BY customer_id y calcular `sales_per_customer = SUM(sales)`
3. Concatenar nombre completo: `customer_name = fname || ' ' || lname`
4. INSERT con UPSERT (ON CONFLICT DO UPDATE)

**Validaciones:**
- ⚠️ Si `customer_id` o `customer_name` es NULL → Skip
- ✅ Log: "{count} NULLs detected (will skip)"

**Retorna:**
```python
{
    'customer_1001': 1,      # customer_id → customer_key
    'customer_1002': 2,
    ...
}
```

**Ejemplo de Inserción:**
```sql
INSERT INTO dw.dim_customer 
(customer_id, customer_name, customer_email, customer_segment, sales_per_customer)
VALUES ('customer_1001', 'John Doe', 'john@example.com', 'Consumer', 5234.56)
ON CONFLICT (customer_id) 
DO UPDATE SET 
    customer_name = EXCLUDED.customer_name,
    sales_per_customer = EXCLUDED.sales_per_customer
RETURNING customer_key;
```

**Output del Log:**
```
🔄 [1/5] Populating dim_customer...
  📥 Read 5,234 unique customers from staging
  📌 Customer lookup dict: 5,234 entries
✅ dim_customer: 5,234 inserted/updated
```

---

### 2. `populate_dim_geography(engine)`

**Propósito:** Crear jerarquía geográfica con validación de mercados válidos.

**Lógica:**
1. SELECT DISTINCT market, order_region, customer_country, customer_state, customer_city
2. Validar `market ∈ {Africa, Europe, LATAM, Pacific Asia, USCA}`
3. Llenar NULLs en campos jerárquicos con "Unknown"
4. INSERT con clave compuesta única

**Validaciones:**
- ✅ Market blanco: Skip + warning
- ✅ Mercados inválidos: Filter + warning
- ✅ Region/Country/State/City NULL → Fill con "Unknown"

**Retorna:**
```python
{
    ('Africa', 'North Africa', 'Egypt', 'Cairo', 'Cairo'): 1,
    ('Europe', 'Western Europe', 'Spain', 'Madrid', 'Madrid'): 2,
    ...
}
```

**Unique Constraint:**
```sql
CREATE UNIQUE INDEX idx_geo_unique 
ON dw.dim_geography (market, region, country, state, city);
```

**Output del Log:**
```
🔄 [2/5] Populating dim_geography...
  📥 Read 987 unique geographic combinations
  ⚠️  Invalid markets detected: ['Unknown', 'NULL']. Filtering out.
  ✅ Validated 985 geographic records
📌 Geography lookup dict: 985 entries
✅ dim_geography: 985 inserted
```

---

### 3. `populate_dim_product(engine)`

**Propósito:** Extraer productos únicos y mapear a tabla dimensional.

**Lógica:**
1. SELECT DISTINCT product_card_id, product_name, category_name, department_name, product_price
2. Llenar NULLs: `product_name = 'Unknown'`, `category_name = 'Unknown'`
3. Validar `product_price` (numeric, default 0.0)
4. INSERT con ON CONFLICT DO NOTHING (idempotente)

**Retorna:**
```python
{
    'PROD-001': 1,      # product_card_id → product_key
    'PROD-002': 2,
    ...
}
```

**Output del Log:**
```
🔄 [3/5] Populating dim_product...
  📥 Read 1,812 unique products from staging
✅ dim_product: 1,812 inserted
  📌 Product lookup dict: 1,812 entries
```

---

### 4. `populate_dim_date(engine)`

**Propósito:** Generar dimensión de fecha completa con atributos temporales.

**Lógica:**
1. Extraer rango: MIN(order_date) y MAX(order_date) desde staging
2. Generar calendario completo con `pd.date_range()`
3. Calcular:
   - `date_id = YYYYMMDD` (ej: 20230115)
   - `year, quarter, month, week, day_of_month`
   - `day_of_week (1=Monday), month_name, day_name, is_weekend`
4. INSERT (ON CONFLICT DO NOTHING)

**Ejemplo de Datos Generados:**
```
date_id  | order_date | year | quarter | month | day_of_week | month_name | is_weekend
---------|------------|------|---------|-------|-------------|------------|------------
20230101 | 2023-01-01 | 2023 |    1    |   1   |      7      | January    |     1
20230102 | 2023-01-02 | 2023 |    1    |   1   |      1      | January    |     0
...
```

**Retorna:**
```python
{
    Timestamp('2023-01-01'): 20230101,
    Timestamp('2023-01-02'): 20230102,
    ...
}
```

**Output del Log:**
```
🔄 [4/5] Populating dim_date...
  📅 Date range: 2020-01-01 to 2024-12-31
  📅 Generated 1,826 calendar dates
✅ dim_date: 1,826 inserted
  📌 Date lookup dict: 1,826 entries
```

---

### 5. `populate_fact_orders(engine, customer_lookup, ...)`

**Propósito:** Población de la tabla de hechos con JOINs a todas las dimensiones.

**Lógica:**
1. READ staging con WHERE `is_processed = FALSE`
2. MAP foreign keys usando lookups:
   - `customer_id` → `dim_customer.customer_key`
   - `(market, region, ...) → dim_geography.geography_id`
   - `product_card_id` → `dim_product.product_key`
   - `order_date` → `dim_date.date_id`
3. VALIDAR: No permitir NULLs en FKs
4. CALCULAR métricas:
   - `is_otif = (late_delivery_risk = 0) ? 1 : 0`
   - `revenue_at_risk = sales * late_delivery_risk`
5. DETECTAR anomalías:
   - `days_for_shipping_real > 60` → Flag
   - `order_item_discount_rate > 100%` → Impossible value
6. INSERT batch con `executemany()` (rápido)

**Batch Insert Optimization:**
```python
# Procesa 1,000 filas por batch para optimizar I/O
for batch_start in range(0, len(df_facts), batch_size=1000):
    # Prepare values list
    values_list = [...]
    # Execute all at once
    conn.execute(upsert_query, values_list)
```

**Validaciones Críticas:**
| FK | Nulls Permitidos | Acción |
|----|------------------|--------|
| customer_key | ❌ No | Skip row + Warning |
| geography_key | ❌ No | Skip row + Warning |
| product_key | ❌ No | Skip row + Warning |
| date_key | ❌ No | Skip row + Warning |

**Output del Log:**
```
🔄 [5/5] Populating fact_orders...
  📥 Read 186,523 unprocessed order items from staging
  ⚠️  customer_key: 145 NULLs (rows will be skipped)
  ⚠️  geography_key: 89 NULLs (rows will be skipped)
  ✅ Valid fact rows: 186,289 (skipped: 234)
  ⚠️  Detected 34 anomalies (delay>60d or discount>100%)
  📈 OTIF%: 84.23%
  💰 Revenue at Risk: $1,234,567.89
✅ fact_orders: 186,289 inserted/updated
```

---

### 6. `run_etl_pipeline()`

**Propósito:** Orquestar la secuencia ETL completa con manejo de transacciones y auditoría.

**Algoritmo:**
```
START ETL
├─ Generate etl_run_id (UUID)
├─ Connect to PostgreSQL
├─ [1] populate_dim_customer()
├─ [2] populate_dim_geography()
├─ [3] populate_dim_product()
├─ [4] populate_dim_date()
├─ [5] populate_fact_orders(etl_run_id)
├─ COMMIT: UPDATE stg_raw_orders SET is_processed = TRUE
├─ Log: Elapsed time, metrics
└─ END ETL (exit code 0)

IF ERROR:
├─ ROLLBACK all changes
├─ Log: Full error stack + context
└─ EXIT (code 1)
```

**Transactional Safety:**
```python
try:
    engine.begin() as conn:  # Auto-commit on success, rollback on exception
        # All transforms happen here
        populate_dim_customer(engine)
        populate_fact_orders(engine, ...)
        # If ANY fails, all rollback
except Exception as e:
    logger.error(f"ETL Failed: {e}")
    return 1  # Exit with error code
finally:
    engine.dispose()  # Clean up connections
```

**Output del Log Completo:**
```
================================================================================
TORRE CONTROL - ETL PIPELINE: Stage → Star Schema
Start Time: 2026-02-04 14:30:15
ETL Run ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
================================================================================

🔄 [1/5] Populating dim_customer...
  ✅ dim_customer: 5,234 inserted/updated

🔄 [2/5] Populating dim_geography...
  ✅ dim_geography: 985 inserted

🔄 [3/5] Populating dim_product...
  ✅ dim_product: 1,812 inserted

🔄 [4/5] Populating dim_date...
  ✅ dim_date: 1,826 inserted

🔄 [5/5] Populating fact_orders...
  📈 OTIF%: 84.23%
  💰 Revenue at Risk: $1,234,567.89
  ✅ fact_orders: 186,289 inserted/updated

🔄 Marking staging as processed...
✅ Staging marked as processed

================================================================================
✅ ETL PIPELINE SUCCESSFUL
Elapsed Time: 187.4 seconds
Fact Summary: {'total_orders': 186523, 'inserted': 186289, 'skipped': 234, 'otif_pct': 84.23, 'revenue_at_risk': 1234567.89}
End Time: 2026-02-04 14:33:22
================================================================================
```

---

## 🔄 Flujo ETL Detallado

### Fase 1: Preparación
```
✓ Load environment variables (.env)
✓ Create logs directory
✓ Setup logging handlers (file + console)
✓ Connect to PostgreSQL (test connection)
```

### Fase 2: Transformación de Dimensiones
```
┌─ dim_customer
│  ├─ SELECT DISTINCT + GROUP BY
│  ├─ Calculate sales_per_customer
│  └─ INSERT (UPSERT)
│
├─ dim_geography
│  ├─ SELECT DISTINCT combinations
│  ├─ Validate markets
│  └─ INSERT (compound unique key)
│
├─ dim_product
│  ├─ SELECT DISTINCT products
│  ├─ Fill NULLs
│  └─ INSERT (DO NOTHING)
│
└─ dim_date
   ├─ Extract date range
   ├─ Generate calendar
   ├─ Calculate temporal attributes
   └─ INSERT (DO NOTHING)
```

### Fase 3: Transformación de Hechos
```
┌─ Read staging
├─ Map foreign keys (customer, geography, product, date)
├─ Validate FK referential integrity
├─ Calculate OTIF, Revenue at Risk
├─ Detect anomalies
├─ INSERT facts (batch, 1000 rows/batch)
└─ Mark staging as processed
```

### Fase 4: Post-Processing
```
✓ Calculate OTIF%, Revenue at Risk, Churn Risk
✓ Log metrics to file
✓ Close database connections
✓ Return exit code (0=success, 1=failure)
```

---

## 🛡️ Validaciones Críticas

### 1. Integridad Referencial

**Validación:** Asegurar que todos los FKs existan en dimensiones.

```python
# Si customer_id no existe en dim_customer → skip row
if row['customer_key'] is None:
    logger.warning(f"customer_id {customer_id} not in dim_customer, skipping")
    # Row no se inserta en fact_orders
```

**Output:**
```
⚠️  customer_key: 145 NULLs (rows will be skipped)
✅ Valid fact rows: 186,289 (skipped: 234)
```

### 2. Detección de Outliers

**Anómalos Detectados:**
- `days_for_shipping_real > 60` → Posible pérdida o data error
- `order_item_discount_rate > 100%` → Imposible matemáticamente

```python
anomalies = df_facts_valid[
    (df_facts_valid["days_for_shipping_real"] > 60) |
    (df_facts_valid["order_item_discount_rate"] > 100)
]
if len(anomalies) > 0:
    logger.warning(f"Detected {len(anomalies)} anomalies")
```

**Output:**
```
⚠️  Detected 34 anomalies (delay>60d or discount>100%)
```

### 3. Validación de Mercados

**Mercados Válidos:** `{Africa, Europe, LATAM, Pacific Asia, USCA}`

```python
valid_markets = {"Africa", "Europe", "LATAM", "Pacific Asia", "USCA"}
invalid = df_geo[~df_geo["market"].isin(valid_markets)]["market"].unique()
if len(invalid) > 0:
    logger.warning(f"Invalid markets: {invalid}. Filtering out.")
```

### 4. Null Checks en Campos Críticos

| Campo | Tabla | Acción |
|-------|-------|--------|
| customer_id | dim_customer, fact_orders | Skip row si NULL |
| order_id | fact_orders | Skip row si NULL |
| order_date | dim_date | Skip row si NULL |
| market | dim_geography | Skip row si NULL |

---

## 🚀 Cómo Ejecutar

### Opción 1: Via Makefile (Recomendado)

```bash
# Ejecutar todo el pipeline
make run

# Solo ejecutar la fase de transformación
make transform
```

### Opción 2: Directo desde Python

```bash
# Activar venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
source .venv/bin/activate   # Mac/Linux

# Ejecutar script
python scripts/transform_data.py
```

### Opción 3: Con Variables de Entorno Personalizadas

```bash
# .env file
export DATABASE_URL="postgresql://user:pass@host:5433/db"
export LOG_DIR="./custom_logs"

# Ejecutar
python scripts/transform_data.py
```

### Requisitos Previos

✅ PostgreSQL corriendo en puerto 5433  
✅ Base de datos `supply_chain_dw` creada  
✅ Schema `dw` con tablas staging + dimensiones + hechos  
✅ Datos cargados en `dw.stg_raw_orders`  
✅ Python 3.10+ con dependencias instaladas  

```bash
pip install -r requirements.txt
# Requiere: sqlalchemy, pandas, python-dotenv, tqdm
```

---

## 📊 Monitoreo y Logs

### Archivos de Log

```
logs/transform_data.log  ← Log principal (DEBUG + INFO + ERROR)
logs/load_data_output.txt  ← Log del ETL anterior
```

### Cómo Leer los Logs

```bash
# Ver últimas 100 líneas
tail -100 logs/transform_data.log

# Filtrar solo errores
grep "❌" logs/transform_data.log

# Ver KPIs finales
grep "OTIF%\|Revenue at Risk" logs/transform_data.log
```

### Ejemplo de Log Exitoso

```
================================================================================
✅ ETL PIPELINE SUCCESSFUL
Elapsed Time: 187.4 seconds
Fact Summary: {'total_orders': 186523, 'inserted': 186289, 'skipped': 234, 
               'otif_pct': 84.23, 'revenue_at_risk': 1234567.89}
================================================================================
```

### Ejemplo de Log con Errores

```
================================================================================
❌ Database error: (psycopg2.OperationalError) could not connect to server
ERR: Database connection failed
   Make sure PostgreSQL is running: 'docker-compose -f config/docker-compose.yml up -d'
================================================================================
```

---

## 🔧 Troubleshooting

### Problema: "Connection refused on localhost:5433"

**Causa:** PostgreSQL no está corriendo

**Solución:**
```bash
docker-compose -f config/docker-compose.yml up -d
# Esperar 5 segundos para que PostgreSQL se inicie
sleep 5
python scripts/transform_data.py
```

### Problema: "Foreign key constraint violation"

**Causa:** Dimensión faltante para una fila de hecho

**Solución:** Script lo maneja automáticamente:
```
⚠️  customer_key: 145 NULLs (rows will be skipped)
✅ Valid fact rows: 186,289 (skipped: 234)
```

Filas con FKs faltantes son **skipped**, no causan error.

### Problema: "is_processed column not found"

**Causa:** Schema `dw.stg_raw_orders` no está actualizado

**Solución:**
```bash
# Regenerar schema desde DDL
psql -U admin -d supply_chain_dw -f sql/ddl/01_schema_base.sql
```

### Problema: "Memory error on large batch"

**Causa:** Batch size demasiado grande

**Solución:** Reducir tamaño de batch en código:
```python
batch_size = 500  # Default 1000, reducir a 500
```

### Problema: "Encoding error: latin1"

**Causa:** Datos con caracteres especiales

**Solución:** Script usa UTF-8, pero CSV raw es ISO-8859-1. Asegurar que `load_data.py` convierte:
```python
df = pd.read_csv("file.csv", encoding="ISO-8859-1")
```

---

## 📈 KPIs Calculados

| KPI | Fórmula | Ubicación |
|-----|---------|-----------|
| **OTIF%** | (on_time ∧ in_full) / total_orders | fact_orders.is_otif |
| **Revenue at Risk** | SUM(sales) WHERE late_delivery_risk=1 | fact_orders.revenue_at_risk |
| **Late Delivery Rate** | COUNT(*) WHERE late_delivery_risk=1 / total | Calculado en queries |
| **Churn Risk Score** | TOP 10% by sales + ≥2 late orders | Analytics view |

### Cálculo de OTIF

```python
# En populate_fact_orders()
df_facts_valid["is_otif"] = (
    (df_facts_valid["late_delivery_risk"] == 0).astype(int)
)

# En logs finales
otif_pct = (df_facts_valid["is_otif"].sum() / len(df_facts_valid)) * 100
logger.info(f"📈 OTIF%: {otif_pct:.2f}%")
```

---

## 📚 Referencias

- [PostgreSQL 15 Documentation](https://www.postgresql.org/docs/15/)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/)
- [pandas DataFrame API](https://pandas.pydata.org/docs/)
- [Torre Control Project Structure](../CONTEXTO_ESTRATEGICO.md)

---

## ✅ Checklist Pre-Producción

- [ ] PostgreSQL corriendo en puerto 5433
- [ ] `dw.stg_raw_orders` con datos
- [ ] DDL schema completo
- [ ] `.env` con `DATABASE_URL` correcto
- [ ] `requirements.txt` instalado
- [ ] Primera ejecución exitosa (sin errores)
- [ ] Logs muestran OTIF% y Revenue at Risk
- [ ] Dimensiones en caché (lookups creados)
- [ ] Hechos insertados sin FKs faltantes
- [ ] Staging marcado como `is_processed = TRUE`

---

**Autor:** Data Engineering Team | Torre Control  
**Última Actualización:** 4 Feb 2026  
**Estado:** ✅ Production Ready
