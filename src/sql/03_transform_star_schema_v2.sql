-- ===================================================================
-- FASE 2.2: TRANSFORMACIÓN A STAR SCHEMA (VERSIÓN CORREGIDA)
-- ===================================================================

-- ===================================================================
-- PASO 1: CREAR DIMENSIONES (CORREGIDAS)
-- ===================================================================

-- 📅 dim_date ya está creada, verificar
SELECT COUNT(*) as dim_date_count FROM dw.dim_date;

-- 👤 1.2 RECREAR DIMENSIÓN CLIENTE
DROP TABLE IF EXISTS dw.dim_customers CASCADE;

CREATE TABLE dw.dim_customers (
    customer_key SERIAL PRIMARY KEY,
    source_customer_id VARCHAR(50),
    fname VARCHAR(100),
    lname VARCHAR(100),
    email VARCHAR(100),
    segment VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(100)
);

INSERT INTO dw.dim_customers (source_customer_id, fname, lname, email, segment, city, state, country)
SELECT DISTINCT 
    CAST(customer_id AS VARCHAR(50)),
    UPPER(TRIM(COALESCE(customer_fname, 'UNKNOWN'))), 
    UPPER(TRIM(COALESCE(customer_lname, 'UNKNOWN'))), 
    COALESCE(customer_email, 'UNKNOWN'),
    customer_segment, 
    UPPER(TRIM(COALESCE(customer_city, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(customer_state, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(customer_country, 'UNKNOWN')))
FROM dw.stg_raw_orders
WHERE customer_id IS NOT NULL;

-- 📦 1.3 RECREAR DIMENSIÓN PRODUCTO (FIX: mantener como VARCHAR)
DROP TABLE IF EXISTS dw.dim_products CASCADE;

CREATE TABLE dw.dim_products (
    product_key SERIAL PRIMARY KEY,
    source_product_id VARCHAR(50),
    product_name VARCHAR(255),
    category_name VARCHAR(100),
    department_name VARCHAR(100),
    product_price DECIMAL(12,2)
);

INSERT INTO dw.dim_products (source_product_id, product_name, category_name, department_name, product_price)
SELECT DISTINCT 
    CAST(COALESCE(product_card_id, 'UNKNOWN') AS VARCHAR(50)),
    UPPER(TRIM(COALESCE(product_name, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(category_name, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(department_name, 'UNKNOWN'))),
    TRY_CAST(product_price AS DECIMAL(12,2))
FROM dw.stg_raw_orders;

-- 🌍 1.4 RECREAR DIMENSIÓN GEOGRAFÍA
DROP TABLE IF EXISTS dw.dim_geography CASCADE;

CREATE TABLE dw.dim_geography (
    geo_key SERIAL PRIMARY KEY,
    market VARCHAR(50),
    region VARCHAR(100),
    country VARCHAR(100),
    city VARCHAR(100)
);

INSERT INTO dw.dim_geography (market, region, country, city)
SELECT DISTINCT 
    UPPER(TRIM(COALESCE(market, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(order_region, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(order_country, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(order_city, 'UNKNOWN')))
FROM dw.stg_raw_orders
WHERE market IS NOT NULL AND order_city IS NOT NULL;

-- ===================================================================
-- PASO 2: CREAR FACT TABLE CORREGIDA
-- ===================================================================

DROP TABLE IF EXISTS dw.fact_orders CASCADE;

CREATE TABLE dw.fact_orders (
    fact_id SERIAL PRIMARY KEY,
    order_id VARCHAR(50),
    order_item_id VARCHAR(50),
    
    -- Foreign Keys
    date_key INT,
    customer_key INT,
    product_key INT,
    geo_key INT,
    
    -- Métricas Financieras
    sales_amount DECIMAL(12,2),
    profit_amount DECIMAL(12,2),
    discount_amount DECIMAL(12,2),
    
    -- Métricas Logísticas
    order_quantity INT,
    days_scheduled INT,
    days_real INT,
    delivery_status VARCHAR(50),
    
    -- KPIs (Calculated)
    is_late BOOLEAN,
    is_otif BOOLEAN,
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insertar con conversión de tipos segura
INSERT INTO dw.fact_orders (
    order_id, order_item_id, date_key, customer_key, product_key, geo_key,
    sales_amount, profit_amount, discount_amount,
    order_quantity, days_scheduled, days_real, delivery_status,
    is_late, is_otif
)
SELECT 
    s.order_id,
    s.order_item_id,
    COALESCE(
        TRY_CAST(TO_CHAR(TO_TIMESTAMP(s.order_date_dateorders, 'MM/DD/YYYY HH24:MI'), 'YYYYMMDD') AS INT),
        20260101
    ) AS date_key,
    COALESCE(c.customer_key, 1) AS customer_key,
    COALESCE(p.product_key, 1) AS product_key,
    COALESCE(g.geo_key, 1) AS geo_key,
    
    -- Métricas Financieras
    COALESCE(TRY_CAST(s.sales AS DECIMAL(12,2)), 0) AS sales_amount,
    COALESCE(TRY_CAST(s.benefit_per_order AS DECIMAL(12,2)), 0) AS profit_amount,
    COALESCE(TRY_CAST(s.order_item_discount AS DECIMAL(12,2)), 0) AS discount_amount,
    
    -- Métricas Logísticas
    COALESCE(TRY_CAST(s.order_item_quantity AS INT), 0) AS order_quantity,
    COALESCE(TRY_CAST(s.days_for_shipment_scheduled AS INT), 0) AS days_scheduled,
    COALESCE(TRY_CAST(s.days_for_shipping_real AS INT), 0) AS days_real,
    COALESCE(s.delivery_status, 'UNKNOWN') AS delivery_status,
    
    -- KPI: ¿Llegó tarde?
    CASE 
        WHEN COALESCE(TRY_CAST(s.days_for_shipping_real AS INT), 999) > 
             COALESCE(TRY_CAST(s.days_for_shipment_scheduled AS INT), 0)
        THEN TRUE 
        ELSE FALSE 
    END AS is_late,
    
    -- KPI: OTIF (A tiempo AND No cancelado)
    CASE 
        WHEN COALESCE(TRY_CAST(s.days_for_shipping_real AS INT), 999) <= 
             COALESCE(TRY_CAST(s.days_for_shipment_scheduled AS INT), 0)
             AND s.order_status NOT IN ('CANCELED', 'SUSPECTED_FRAUD')
        THEN TRUE 
        ELSE FALSE 
    END AS is_otif

FROM dw.stg_raw_orders s
LEFT JOIN dw.dim_customers c ON CAST(s.customer_id AS VARCHAR(50)) = c.source_customer_id
LEFT JOIN dw.dim_products p ON CAST(COALESCE(s.product_card_id, 'UNKNOWN') AS VARCHAR(50)) = p.source_product_id
LEFT JOIN dw.dim_geography g ON 
    UPPER(TRIM(COALESCE(s.order_city, 'UNKNOWN'))) = UPPER(TRIM(g.city)) AND
    UPPER(TRIM(COALESCE(s.order_country, 'UNKNOWN'))) = UPPER(TRIM(g.country))
WHERE s.order_item_id IS NOT NULL;

-- Crear índices
CREATE INDEX idx_fact_orders_date ON dw.fact_orders(date_key);
CREATE INDEX idx_fact_orders_customer ON dw.fact_orders(customer_key);
CREATE INDEX idx_fact_orders_product ON dw.fact_orders(product_key);
CREATE INDEX idx_fact_orders_geo ON dw.fact_orders(geo_key);
CREATE INDEX idx_fact_orders_otif ON dw.fact_orders(is_otif);
CREATE INDEX idx_fact_orders_late ON dw.fact_orders(is_late);

-- ===================================================================
-- PASO 3: VALIDACIÓN DE CALIDAD
-- ===================================================================

-- 📊 3.1 TASA OTIF GLOBAL
SELECT 
    'OTIF Global' AS metrica,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN is_otif THEN 1 ELSE 0 END) AS perfect_orders,
    ROUND((SUM(CASE WHEN is_otif THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 2) AS otif_percentage
FROM dw.fact_orders;

-- 📊 3.2 ENTREGAS TARDE
SELECT 
    'Late Deliveries' AS metrica,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN is_late THEN 1 ELSE 0 END) AS late_orders,
    ROUND((SUM(CASE WHEN is_late THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 2) AS late_percentage
FROM dw.fact_orders;

-- 📊 3.3 REVENUE AT RISK
SELECT 
    'Revenue at Risk' AS metrica,
    SUM(sales_amount)::DECIMAL(12,2) AS total_revenue,
    SUM(CASE WHEN is_late THEN sales_amount ELSE 0 END)::DECIMAL(12,2) AS revenue_at_risk,
    ROUND((SUM(CASE WHEN is_late THEN sales_amount ELSE 0 END)::DECIMAL / SUM(sales_amount)) * 100, 2) AS risk_percentage
FROM dw.fact_orders;

-- 📊 3.4 TOP 5 MERCADOS
SELECT 
    'Market: ' || g.market AS metrica,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN f.is_late THEN 1 ELSE 0 END) AS late_orders,
    ROUND((SUM(CASE WHEN f.is_late THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 2) AS late_percentage,
    SUM(CASE WHEN f.is_late THEN f.sales_amount ELSE 0 END)::DECIMAL(12,2) AS revenue_at_risk
FROM dw.fact_orders f
JOIN dw.dim_geography g ON f.geo_key = g.geo_key
GROUP BY g.market
ORDER BY revenue_at_risk DESC
LIMIT 5;

-- 📊 3.5 ESTATUS DE ENTREGAS
SELECT 
    'Delivery Status: ' || delivery_status AS metrica,
    COUNT(*) AS count
FROM dw.fact_orders
GROUP BY delivery_status
ORDER BY count DESC;

-- 📊 3.6 CONTEO DE TABLAS
SELECT 
    'dim_date' AS tabla,
    COUNT(*)::TEXT AS registros
FROM dw.dim_date
UNION ALL
SELECT 'dim_customers', COUNT(*)::TEXT FROM dw.dim_customers
UNION ALL
SELECT 'dim_products', COUNT(*)::TEXT FROM dw.dim_products
UNION ALL
SELECT 'dim_geography', COUNT(*)::TEXT FROM dw.dim_geography
UNION ALL
SELECT 'fact_orders', COUNT(*)::TEXT FROM dw.fact_orders;
