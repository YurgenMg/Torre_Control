-- ===================================================================
-- FASE 2.2: TRANSFORMACIÓN A STAR SCHEMA (VERSIÓN POSTGRES-COMPATIBLE)
-- ===================================================================

-- PASO 1: DIMENSIONES

-- 📅 dim_date ya existe (verificar)
SELECT COUNT(*) FROM dw.dim_date;

-- 👤 1.2 DIMENSIÓN CLIENTE
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
    customer_id,
    UPPER(TRIM(COALESCE(customer_fname, 'UNKNOWN'))), 
    UPPER(TRIM(COALESCE(customer_lname, 'UNKNOWN'))), 
    COALESCE(customer_email, 'UNKNOWN'),
    COALESCE(customer_segment, 'UNKNOWN'), 
    UPPER(TRIM(COALESCE(customer_city, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(customer_state, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(customer_country, 'UNKNOWN')))
FROM dw.stg_raw_orders
WHERE customer_id IS NOT NULL;

-- 📦 1.3 DIMENSIÓN PRODUCTO
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
    COALESCE(product_card_id, 'UNKNOWN'),
    UPPER(TRIM(COALESCE(product_name, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(category_name, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(department_name, 'UNKNOWN'))),
    NULLIF(product_price, '')::DECIMAL(12,2)
FROM dw.stg_raw_orders;

-- 🌍 1.4 DIMENSIÓN GEOGRAFÍA
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

-- PASO 2: FACT TABLE

DROP TABLE IF EXISTS dw.fact_orders CASCADE;

CREATE TABLE dw.fact_orders (
    fact_id SERIAL PRIMARY KEY,
    order_id VARCHAR(50),
    order_item_id VARCHAR(50),
    
    date_key INT,
    customer_key INT,
    product_key INT,
    geo_key INT,
    
    sales_amount DECIMAL(12,2),
    profit_amount DECIMAL(12,2),
    discount_amount DECIMAL(12,2),
    order_quantity INT,
    days_scheduled INT,
    days_real INT,
    delivery_status VARCHAR(50),
    
    is_late BOOLEAN,
    is_otif BOOLEAN
);

-- Insertar con tratamiento seguro de tipos
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
        CAST(
            CASE 
                WHEN s.order_date_dateorders ~ '^\d{1,2}/\d{1,2}/\d{4}' 
                THEN TO_CHAR(TO_TIMESTAMP(s.order_date_dateorders, 'MM/DD/YYYY HH24:MI'), 'YYYYMMDD')
                ELSE '20260101'
            END
            AS INT
        ),
        20260101
    ) AS date_key,
    COALESCE(c.customer_key, 0) AS customer_key,
    COALESCE(p.product_key, 0) AS product_key,
    COALESCE(g.geo_key, 0) AS geo_key,
    
    COALESCE((NULLIF(s.sales, '')::DECIMAL(12,2)), 0),
    COALESCE((NULLIF(s.benefit_per_order, '')::DECIMAL(12,2)), 0),
    COALESCE((NULLIF(s.order_item_discount, '')::DECIMAL(12,2)), 0),
    COALESCE((NULLIF(s.order_item_quantity, '')::INT), 0),
    COALESCE((NULLIF(s.days_for_shipment_scheduled, '')::INT), 0),
    COALESCE((NULLIF(s.days_for_shipping_real, '')::INT), 0),
    COALESCE(s.delivery_status, 'UNKNOWN'),
    
    -- is_late
    CASE 
        WHEN (NULLIF(s.days_for_shipping_real, '')::INT) > (NULLIF(s.days_for_shipment_scheduled, '')::INT)
        THEN TRUE 
        ELSE FALSE 
    END,
    
    -- is_otif
    CASE 
        WHEN (NULLIF(s.days_for_shipping_real, '')::INT) <= (NULLIF(s.days_for_shipment_scheduled, '')::INT)
             AND s.order_status NOT IN ('CANCELED', 'SUSPECTED_FRAUD')
        THEN TRUE 
        ELSE FALSE 
    END

FROM dw.stg_raw_orders s
LEFT JOIN dw.dim_customers c ON s.customer_id = c.source_customer_id
LEFT JOIN dw.dim_products p ON s.product_card_id = p.source_product_id
LEFT JOIN dw.dim_geography g ON 
    UPPER(TRIM(COALESCE(s.order_city, 'UNKNOWN'))) = UPPER(TRIM(g.city)) AND
    UPPER(TRIM(COALESCE(s.order_country, 'UNKNOWN'))) = UPPER(TRIM(g.country))
WHERE s.order_item_id IS NOT NULL;

-- Índices
CREATE INDEX idx_fact_orders_date ON dw.fact_orders(date_key);
CREATE INDEX idx_fact_orders_customer ON dw.fact_orders(customer_key);
CREATE INDEX idx_fact_orders_product ON dw.fact_orders(product_key);
CREATE INDEX idx_fact_orders_geo ON dw.fact_orders(geo_key);
CREATE INDEX idx_fact_orders_otif ON dw.fact_orders(is_otif);
CREATE INDEX idx_fact_orders_late ON dw.fact_orders(is_late);

-- PASO 3: VALIDACIÓN

SELECT '[RESULT] OTIF Global' AS test,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN is_otif THEN 1 ELSE 0 END) AS perfect_orders,
    ROUND((SUM(CASE WHEN is_otif THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100, 2) AS otif_percentage
FROM dw.fact_orders;

SELECT '[RESULT] Late Deliveries' AS test,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN is_late THEN 1 ELSE 0 END) AS late_orders,
    ROUND((SUM(CASE WHEN is_late THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100, 2) AS late_percentage
FROM dw.fact_orders;

SELECT '[RESULT] Revenue at Risk' AS test,
    SUM(sales_amount)::NUMERIC AS total_revenue,
    SUM(CASE WHEN is_late THEN sales_amount ELSE 0 END)::NUMERIC AS revenue_at_risk,
    ROUND((SUM(CASE WHEN is_late THEN sales_amount ELSE 0 END)::NUMERIC / SUM(sales_amount)) * 100, 2) AS risk_percentage
FROM dw.fact_orders;

SELECT '[RESULT] Top Markets' AS test,
    g.market,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN f.is_late THEN 1 ELSE 0 END) AS late_orders,
    ROUND((SUM(CASE WHEN f.is_late THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)) * 100, 2) AS late_percentage
FROM dw.fact_orders f
JOIN dw.dim_geography g ON f.geo_key = g.geo_key
GROUP BY g.market
ORDER BY late_orders DESC
LIMIT 5;

SELECT '[RESULT] Table Counts' AS test,
    'dim_date' AS tabla,
    COUNT(*)::TEXT AS count FROM dw.dim_date
UNION ALL
SELECT '[RESULT] Table Counts', 'dim_customers', COUNT(*)::TEXT FROM dw.dim_customers
UNION ALL
SELECT '[RESULT] Table Counts', 'dim_products', COUNT(*)::TEXT FROM dw.dim_products
UNION ALL
SELECT '[RESULT] Table Counts', 'dim_geography', COUNT(*)::TEXT FROM dw.dim_geography
UNION ALL
SELECT '[RESULT] Table Counts', 'fact_orders', COUNT(*)::TEXT FROM dw.fact_orders;
