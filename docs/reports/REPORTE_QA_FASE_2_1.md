# ✅ REPORTE QA - FASE 2.1: INGESTA CSV COMPLETADA

**Fecha:** 02 de Febrero de 2026  
**Hora:** ~20:15 UTC-5  
**Estado:** ✅ **ÉXITO - LISTO PARA FASE 2.2**

---

## 📊 RESULTADOS DE CARGA

### Métricas Generales
```
Total de Filas Cargadas:           180,519
Columnas en Tabla:                 53
Archivo Fuente:                    data/raw/DataCoSupplyChainDataset.csv
Tamaño Archivo:                    96 MB
Encoding:                          ISO-8859-1
Método de Carga:                   Pandas + SQLAlchemy COPY
Tiempo Total:                      ~3 minutos
```

### Análisis de Claves Primarias
```
Órdenes Únicas (order_id):         65,752
Artículos de Orden Únicos (order_item_id):  180,519 ✅
Clientes Únicos (customer_id):     20,652

Análisis de Duplicados:            ❌ NINGUNO ENCONTRADO
  - order_item_id: 0 duplicados (tabla limpia)
  - Conclusión: order_item_id es CLAVE ÚNICA viable
```

### Muestra de Datos (5 primeras filas)
```sql
order_id | order_item_id | customer_id | product_name                              | sales      | late_delivery_risk | delivery_status | market
---------|---------------|-------------|-------------------------------------------|------------|--------------------|-----------------|--------
18488    | 46216         | 6395        | Nike Men's CJ Elite 2 TD Football Cleat   | 129.99     | 1                  | Late delivery   | Europe
17589    | 43977         | 7834        | Nike Men's CJ Elite 2 TD Football Cleat   | 129.99     | 1                  | Late delivery   | Europe
71367    | 174682        | 14920       | Porcelain crafts                           | 461.48     | 1                  | Late delivery   | Europe
17589    | 43976         | 7834        | Nike Men's CJ Elite 2 TD Football Cleat   | 129.99     | 1                  | Late delivery   | Europe
62950    | 157418        | 10075       | Nike Men's CJ Elite 2 TD Football Cleat   | 129.99     | 1                  | Late delivery   | Europe
```

---

## 🔍 VERIFICACIONES COMPLETADAS

✅ **Tabla Creada:** `dw.stg_raw_orders`  
✅ **Filas Cargadas:** 180,519 (100% del CSV)  
✅ **Integridad de Datos:** Validada  
✅ **Duplicados:** 0 encontrados  
✅ **Claves Primarias:** order_item_id es ÚNICA  
✅ **Columnas:** 53 (todas normalizadas a snake_case)  
✅ **Índices:** 3 creados (order_id, order_item_id, customer_id)  
✅ **Encoding:** Caracteres latinos procesados correctamente  

---

## 📋 CAMPOS DISPONIBLES EN stg_raw_orders

Nombres normalizados (snake_case):
```
type
days_for_shipping_real
days_for_shipment_scheduled
benefit_per_order
sales_per_customer
delivery_status
late_delivery_risk
category_id
category_name
customer_city
customer_country
customer_email
customer_fname
customer_id
customer_lname
customer_password
customer_segment
customer_state
customer_street
customer_zipcode
department_id
department_name
latitude
longitude
market
order_city
order_country
order_customer_id
order_date_dateorders
order_id
order_item_cardprod_id
order_item_discount
order_item_discount_rate
order_item_id
order_item_product_price
order_item_profit_ratio
order_item_quantity
sales
order_item_total
order_profit_per_order
order_region
order_state
order_status
order_zipcode
product_card_id
product_category_id
product_description
product_image
product_name
product_price
product_status
shipping_date_dateorders
shipping_mode
```

---

## ✨ PRÓXIMOS PASOS - FASE 2.2: TRANSFORMACIÓN A STAR SCHEMA

### Tarea 2.2.1: Crear Dimensiones
```sql
-- dim_customer: Deduplicar clientes (20,652 únicos de 180K filas)
INSERT INTO dw.dim_customer (customer_id, fname, lname, email, segment, city, state, country)
SELECT DISTINCT 
    customer_id, customer_fname, customer_lname, customer_email, 
    customer_segment, customer_city, customer_state, customer_country
FROM dw.stg_raw_orders;

-- dim_geography: Crear jerarquía Market → Region → State → City
-- dim_product: Deduplicar productos
-- dim_date: Generar calendario (2015-2026)
```

### Tarea 2.2.2: Transformar a Fact Table
```sql
INSERT INTO dw.fact_orders (...)
SELECT 
    order_item_id,
    customer_id,
    product_id,
    geography_id,
    date_id,
    CAST(sales AS NUMERIC) as sales,
    CAST(benefit_per_order AS NUMERIC) as benefit,
    CAST(order_item_quantity AS INTEGER) as quantity,
    CAST(late_delivery_risk AS INTEGER) as is_late,
    ...
FROM dw.stg_raw_orders;
```

### Tarea 2.2.3: Validar Queries Estratégicas
```sql
-- Q1: OTIF por Market
SELECT * FROM dw.v_otif_by_market;

-- Q2: Revenue at Risk
SELECT * FROM dw.v_revenue_at_risk;

-- Q3: VIP Churn Risk
SELECT * FROM dw.v_churn_risk_vip;

-- Q4: Geographic Efficiency
-- Q5: Fraud/Anomaly Detection
```

---

## 🎯 HITOS COMPLETADOS

| Fase | Tarea | Estado | Comentarios |
|------|-------|--------|------------|
| 1.0 | Infraestructura (Docker, PostgreSQL) | ✅ COMPLETADO | Puerto 5433, schema dw creado |
| 2.1 | **Ingesta CSV a Staging** | ✅ **COMPLETADO** | 180,519 filas cargadas, sin duplicados |
| 2.2 | Transformación a Star Schema | 📌 LISTO PARA INICIAR | SQL queries preparadas en `sql/queries/` |
| 2.3 | Validación de Datos | 📌 LISTO | Health checks preparados |
| 3.0 | Conexión Power BI | ⏳ PRÓXIMO | Dashboard 5 vistas |

---

## 🛠️ COMANDOS DE REFERENCIA

### Verificar Datos
```bash
docker exec supply_chain_db psql -U admin -d supply_chain_dw -c \
  "SELECT COUNT(*) FROM dw.stg_raw_orders;"
```

### Ver Muestra
```bash
docker exec supply_chain_db psql -U admin -d supply_chain_dw -c \
  "SELECT * FROM dw.stg_raw_orders LIMIT 10;"
```

### Estadísticas por Market
```bash
docker exec supply_chain_db psql -U admin -d supply_chain_dw -c \
  "SELECT market, COUNT(*) as count FROM dw.stg_raw_orders GROUP BY market ORDER BY count DESC;"
```

---

## 📝 DECISIONES TÉCNICAS DOCUMENTADAS

1. **Tabla Staging con tipos TEXT**: Se creó `stg_raw_orders` con todos los campos como TEXT para evitar errores de conversión de tipo durante la carga. Las transformaciones a tipos correctos ocurrirán en el paso de Star Schema.

2. **order_item_id como PK**: Se validó que es 100% único (180,519 registros sin duplicados), adecuado como clave primaria en fact_orders.

3. **Encoding ISO-8859-1**: Necesario para procesar caracteres latinos en el dataset de DataCo (ciudades, nombres, etc.).

4. **Chunking 50K filas**: Se usó para optimizar memoria durante INSERT (pandas to_sql con chunksize=50000).

---

## ✅ BANDERAZO CONFIRMADO

```
Estado: ✅ LISTO PARA FASE 2.2
CSV:    ✅ 180,519 filas en BD
Schema: ✅ Normalizado (53 columnas)
QA:     ✅ Sin duplicados, sin nulos críticos
Índices: ✅ 3 índices estratégicos creados

PRÓXIMO: Ejecutar transformación a Star Schema (dim_customer, fact_orders, etc.)
```

---

*Generado por: GitHub Copilot Data Engineering Pipeline*  
*Proyecto: Torre Control - Supply Chain Data Warehouse*  
*Fase: 2.1 Extract & Load (COMPLETADA)*
