-- ============================================================================
-- TORRE CONTROL - Transformación ETL: Staging → Star Schema
-- Ejecutado: 2026-02-04
-- ============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. POBLAR dim_customer (Clientes únicos)
-- ---------------------------------------------------------------------------
INSERT INTO dw.dim_customer (
    customer_id,
    fname,
    lname,
    segment
)
SELECT DISTINCT
    customer_id,
    customer_fname as fname,
    customer_lname as lname,
    customer_segment as segment
FROM dw.stg_raw_orders
WHERE customer_id IS NOT NULL
  AND customer_id::VARCHAR NOT IN (SELECT customer_id FROM dw.dim_customer WHERE customer_id IS NOT NULL);

-- ---------------------------------------------------------------------------
-- 2. POBLAR dim_geography (Jerarquía Market → Region → Country)
-- ---------------------------------------------------------------------------
INSERT INTO dw.dim_geography (
    market,
    region,
    country
)
SELECT DISTINCT
    market,
    order_region as region,
    order_country as country
FROM dw.stg_raw_orders
WHERE market IS NOT NULL
  AND order_region IS NOT NULL
  AND order_country IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM dw.dim_geography g 
    WHERE g.market = dw.stg_raw_orders.market 
      AND g.region = dw.stg_raw_orders.order_region 
      AND g.country = dw.stg_raw_orders.order_country
  );

-- ---------------------------------------------------------------------------
-- 3. POBLAR dim_product (Catálogo de productos)
-- ---------------------------------------------------------------------------
INSERT INTO dw.dim_product (
    product_id,
    product_name,
    category
)
SELECT DISTINCT
    product_card_id as product_id,
    product_name,
    category_name as category
FROM dw.stg_raw_orders
WHERE product_card_id IS NOT NULL
  AND product_card_id::VARCHAR NOT IN (SELECT product_id FROM dw.dim_product WHERE product_id IS NOT NULL);

-- ---------------------------------------------------------------------------
-- 4. POBLAR dim_date (Dimensión calendario)
-- ---------------------------------------------------------------------------
INSERT INTO dw.dim_date (
    order_date,
    year,
    month,
    day
)
SELECT DISTINCT
    s."order_date_(dateorders)"::DATE as order_date,
    EXTRACT(YEAR FROM s."order_date_(dateorders)"::DATE)::INTEGER as year,
    EXTRACT(MONTH FROM s."order_date_(dateorders)"::DATE)::INTEGER as month,
    EXTRACT(DAY FROM s."order_date_(dateorders)"::DATE)::INTEGER as day
FROM dw.stg_raw_orders s
WHERE s."order_date_(dateorders)" IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM dw.dim_date d WHERE d.order_date = s."order_date_(dateorders)"::DATE);

-- ---------------------------------------------------------------------------
-- 5. POBLAR fact_orders (Tabla de hechos - Transacciones)
-- ---------------------------------------------------------------------------
INSERT INTO dw.fact_orders (
    order_id,
    date_key,
    customer_key,
    product_key,
    geo_key,
    sales,
    late_delivery_risk
)
SELECT
    s.order_id::VARCHAR as order_id,
    d.date_key,
    c.customer_key,
    p.product_key,
    g.geo_key,
    COALESCE(s.sales::NUMERIC, 0) as sales,
    COALESCE(s.late_delivery_risk, 0) as late_delivery_risk
FROM dw.stg_raw_orders s
INNER JOIN dw.dim_customer c ON s.customer_id::VARCHAR = c.customer_id::VARCHAR
INNER JOIN dw.dim_product p ON s.product_card_id::VARCHAR = p.product_id::VARCHAR
INNER JOIN dw.dim_geography g ON (
    s.market = g.market AND
    s.order_region = g.region AND
    s.order_country = g.country
)
INNER JOIN dw.dim_date d ON s."order_date_(dateorders)"::DATE = d.order_date
WHERE s.order_id IS NOT NULL
  AND s.customer_id IS NOT NULL
  AND s.product_card_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM dw.fact_orders f WHERE f.order_id = s.order_id::VARCHAR);

-- ---------------------------------------------------------------------------
-- Marcar staging como procesado (opcional - campo no existe en esta versión)
-- ---------------------------------------------------------------------------
-- UPDATE dw.stg_raw_orders SET is_processed = TRUE;

COMMIT;

-- ---------------------------------------------------------------------------
-- REPORTE DE VERIFICACIÓN
-- ---------------------------------------------------------------------------
\echo ''
\echo '═══════════════════════════════════════════════════════════'
\echo '  ✅ TRANSFORMACIÓN COMPLETADA'
\echo '═══════════════════════════════════════════════════════════'
\echo ''

SELECT 
    'dim_customer' as tabla, 
    COUNT(*) as registros,
    '👥 Clientes únicos' as descripcion
FROM dw.dim_customer
UNION ALL
SELECT 
    'dim_geography', 
    COUNT(*),
    '🌍 Ubicaciones (Market→City)'
FROM dw.dim_geography
UNION ALL
SELECT 
    'dim_product', 
    COUNT(*),
    '📦 Productos del catálogo'
FROM dw.dim_product
UNION ALL
SELECT 
    'dim_date', 
    COUNT(*),
    '📅 Fechas del calendario'
FROM dw.dim_date
UNION ALL
SELECT 
    'fact_orders', 
    COUNT(*),
    '🎯 Transacciones (fact table)'
FROM dw.fact_orders;

\echo ''
\echo 'Próximos pasos:'
\echo '  1. Refrescar Power BI Desktop'
\echo '  2. Verificar relaciones en Model View'
\echo '  3. Crear medidas DAX para KPIs'
\echo ''
