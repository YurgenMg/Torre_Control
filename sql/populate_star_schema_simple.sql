-- Simple SQL script to populate star schema from staging
-- Proyecto Torre Control
-- Author: AI Assistant
-- Date: 2026-02-04

BEGIN;

-- 1. Populate dim_customer (CORREGIDO: usa customer_id para dedup)
INSERT INTO dw.dim_customer (customer_id, fname, lname, segment)
SELECT DISTINCT
    customer_id::VARCHAR,
    customer_fname,
    customer_lname,
    customer_segment
FROM dw.stg_raw_orders
WHERE customer_id IS NOT NULL
ON CONFLICT (customer_id) DO NOTHING;

-- 2. Populate dim_geography (CORREGIDO: usa combo único market+region+country)
INSERT INTO dw.dim_geography (market, region, country)
SELECT DISTINCT
    market,
    order_region,
    customer_country
FROM dw.stg_raw_orders
WHERE market IS NOT NULL
    AND order_region IS NOT NULL
    AND customer_country IS NOT NULL
ON CONFLICT (market, region, country) DO NOTHING;

-- 3. Populate dim_product (CORREGIDO: usa product_id para dedup)
INSERT INTO dw.dim_product (product_id, product_name, category)
SELECT DISTINCT
    product_card_id::VARCHAR,
    product_name,
    category_name
FROM dw.stg_raw_orders
WHERE product_card_id IS NOT NULL
ON CONFLICT (product_id) DO NOTHING;

-- 4. dim_date ya tiene datos (1127 registros)

-- 5. Populate fact_orders
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
    stg.order_id::VARCHAR,
    dd.date_key,
    dc.customer_key,
    dp.product_key,
    dg.geo_key,
    COALESCE(stg.sales, 0)::NUMERIC(10,2),
    COALESCE(stg.late_delivery_risk, 0)::INTEGER
FROM dw.stg_raw_orders stg
LEFT JOIN dw.dim_customer dc ON stg.customer_id::VARCHAR = dc.customer_id
LEFT JOIN dw.dim_date dd ON DATE(stg."order_date_(dateorders)") = dd.order_date
LEFT JOIN dw.dim_product dp ON stg.product_card_id::VARCHAR = dp.product_id
LEFT JOIN dw.dim_geography dg ON stg.market = dg.market 
    AND stg.order_region = dg.region
    AND stg.customer_country = dg.country
WHERE dc.customer_key IS NOT NULL
    AND dd.date_key IS NOT NULL
    AND dp.product_key IS NOT NULL
    AND dg.geo_key IS NOT NULL;

COMMIT;

-- Verificación
SELECT 'dim_customer' AS tabla, COUNT(*) AS registros FROM dw.dim_customer
UNION ALL
SELECT 'dim_geography', COUNT(*) FROM dw.dim_geography
UNION ALL
SELECT 'dim_product', COUNT(*) FROM dw.dim_product
UNION ALL
SELECT 'dim_date', COUNT(*) FROM dw.dim_date
UNION ALL
SELECT 'fact_orders', COUNT(*) FROM dw.fact_orders;
