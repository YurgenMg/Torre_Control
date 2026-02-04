# Transform Data Script - Quick Start

## ⚡ Ejecución Rápida

### Opción 1: Via Makefile (Recomendado)

```bash
# Ejecutar solo la fase de transformación
make transform

# O ejecutar el pipeline completo (load + transform + export + validate)
make run
```

### Opción 2: Directo con Python

```bash
# Activar entorno virtual
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Ejecutar transformación
python scripts/transform_data.py
```

---

## 📋 Qué Hace El Script

El script **convierte datos crudos del staging en un Star Schema analítico** listo para Power BI.

### Flujo Interno

```
1. populate_dim_customer()     → 5,000+ clientes únicos
2. populate_dim_geography()    → 985 combinaciones geográficas (Market→Region→State→City)
3. populate_dim_product()      → 1,800+ productos únicos
4. populate_dim_date()         → Calendario completo (años, trimestres, etc.)
5. populate_fact_orders()      → 186,000+ transacciones de órdenes
```

### KPIs Calculados

✅ **OTIF%** (On-Time In-Full) - Porcentaje de entregas perfectas  
✅ **Revenue at Risk** - Ingresos en riesgo por entregas tardías  
✅ **Anomalías** - Retrasos >60 días, descuentos >100%  

---

## 📊 Logs y Salida Esperada

El script genera logs detallados:

```
================================================================================
TORRE CONTROL - ETL PIPELINE: Stage → Star Schema
Start Time: 2026-02-04 14:30:15
ETL Run ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
================================================================================

🔄 [1/5] Populating dim_customer...
  📥 Read 5,234 unique customers from staging
✅ dim_customer: 5,234 inserted/updated

🔄 [2/5] Populating dim_geography...
  📥 Read 987 unique geographic combinations
✅ dim_geography: 985 inserted

🔄 [3/5] Populating dim_product...
  📥 Read 1,812 unique products from staging
✅ dim_product: 1,812 inserted

🔄 [4/5] Populating dim_date...
  📅 Date range: 2020-01-01 to 2024-12-31
  📅 Generated 1,826 calendar dates
✅ dim_date: 1,826 inserted

🔄 [5/5] Populating fact_orders...
  📥 Read 186,523 unprocessed order items from staging
  ✅ Valid fact rows: 186,289 (skipped: 234)
  📈 OTIF%: 84.23%
  💰 Revenue at Risk: $1,234,567.89
✅ fact_orders: 186,289 inserted/updated

================================================================================
✅ ETL PIPELINE SUCCESSFUL
Elapsed Time: 187.4 seconds
End Time: 2026-02-04 14:33:22
================================================================================
```

---

## 🔍 Monitoreo

**Ver logs en vivo:**
```bash
tail -f logs/transform_data.log
```

**Ver solo KPIs finales:**
```bash
grep "OTIF%\|Revenue at Risk" logs/transform_data.log
```

---

## 🛡️ Validaciones Automáticas

El script **automáticamente:**

✅ Valida mercados válidos: `{Africa, Europe, LATAM, Pacific Asia, USCA}`  
✅ Detecta NULLs en FKs y **skipa** filas problemáticas  
✅ Identifica anomalías: retrasos >60 días, descuentos >100%  
✅ Calcula OTIF% y Revenue at Risk  
✅ Marca staging como "processed" al completar  

---

## ⚠️ Requisitos Previos

✅ PostgreSQL corriendo en puerto 5433  
✅ Base de datos `supply_chain_dw` existente  
✅ Schema `dw` con tablas creadas (DDL)  
✅ `dw.stg_raw_orders` con datos  
✅ Python 3.10+ con `requirements.txt` instalado  

```bash
# Verificar que todo está listo
make health
```

---

## 🚨 Troubleshooting

### Error: "Connection refused on localhost:5433"
```bash
# PostgreSQL no está corriendo, iniciar:
docker-compose -f config/docker-compose.yml up -d
```

### Error: "is_processed column not found"
```bash
# Schema no está actualizado, regenerar:
psql -U admin -d supply_chain_dw -f sql/ddl/01_schema_base.sql
```

### Rows skipped con "customer_key: NULLs"
→ Normal, el script filtra FKs faltantes automáticamente  

---

## 📚 Documentación Completa

Para detalles técnicos, ver: [TRANSFORM_DATA_GUIDE.md](TRANSFORM_DATA_GUIDE.md)

---

**Versión:** 1.0  
**Última Actualización:** 4 Feb 2026  
**Estado:** ✅ Production Ready
