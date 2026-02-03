-- ===================================================================
-- FASE 2.2: TRANSFORMACIÓN A STAR SCHEMA
-- ===================================================================
-- Propósito: Convertir stg_raw_orders plana en modelo dimensional
-- Paso 1: Crear Dimensiones (dim_date, dim_customers, dim_products, dim_geography)
-- Paso 2: Crear Fact Table con lógica de negocio
-- Paso 3: Verificar calidad

-- ===================================================================
-- PASO 1: CREAR DIMENSIONES
-- ===================================================================

-- 📅 1.1 DIMENSIÓN TIEMPO (2015-2030)
DROP TABLE IF EXISTS dw.dim_date CASCADE;

CREATE TABLE dw.dim_date (
    date_id INT PRIMARY KEY,
    date DATE,
    year INT,
    month INT,
    month_name VARCHAR(20),
    quarter INT,
    week_of_year INT,
    day_name VARCHAR(20),
    is_weekend BOOLEAN
);

-- Generar fechas automáticamente
INSERT INTO dw.dim_date
SELECT 
    TO_CHAR(datum, 'yyyymmdd')::INT AS date_id,
    datum AS date,
    EXTRACT(YEAR FROM datum) AS year,
    EXTRACT(MONTH FROM datum) AS month,
    TO_CHAR(datum, 'Month') AS month_name,
    EXTRACT(QUARTER FROM datum) AS quarter,
    EXTRACT(WEEK FROM datum) AS week_of_year,
    TO_CHAR(datum, 'Day') AS day_name,
    CASE WHEN EXTRACT(ISODOW FROM datum) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM (SELECT '2015-01-01'::DATE + SEQUENCE.DAY AS datum
      FROM GENERATE_SERIES(0, 5475) AS SEQUENCE(DAY)) DQ
ORDER BY 1;

COMMIT;

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
    customer_segment, 
    UPPER(TRIM(COALESCE(customer_city, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(customer_state, 'UNKNOWN'))),
    UPPER(TRIM(COALESCE(customer_country, 'UNKNOWN')))
FROM dw.stg_raw_orders
WHERE customer_id IS NOT NULL;

COMMIT;

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
    CAST(COALESCE(product_price, 0) AS DECIMAL(12,2))
FROM dw.stg_raw_orders;

COMMIT;

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

COMMIT;

-- ===================================================================
-- PASO 2: CREAR FACT TABLE CON LÓGICA DE NEGOCIO
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
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    FOREIGN KEY (date_key) REFERENCES dw.dim_date(date_id),
    FOREIGN KEY (customer_key) REFERENCES dw.dim_customers(customer_key),
    FOREIGN KEY (product_key) REFERENCES dw.dim_products(product_key),
    FOREIGN KEY (geo_key) REFERENCES dw.dim_geography(geo_key)
);

-- Insertar datos con transformación de tipos y cálculo de KPIs
INSERT INTO dw.fact_orders (
    order_id, order_item_id, date_key, customer_key, product_key, geo_key,
    sales_amount, profit_amount, discount_amount,
    order_quantity, days_scheduled, days_real, delivery_status,
    is_late, is_otif
)
SELECT 
    s.order_id,
    s.order_item_id,
    TO_CHAR(TO_TIMESTAMP(s.order_date_dateorders, 'MM/DD/YYYY HH24:MI'), 'YYYYMMDD')::INT AS date_key,
    c.customer_key,
    p.product_key,
    g.geo_key,
    
    -- Métricas Financieras
    CAST(COALESCE(s.sales, 0) AS DECIMAL(12,2)) AS sales_amount,
    CAST(COALESCE(s.benefit_per_order, 0) AS DECIMAL(12,2)) AS profit_amount,
    CAST(COALESCE(s.order_item_discount, 0) AS DECIMAL(12,2)) AS discount_amount,
    
    -- Métricas Logísticas
    CAST(COALESCE(s.order_item_quantity, 0) AS INT) AS order_quantity,
    CAST(COALESCE(s.days_for_shipment_scheduled, 0) AS INT) AS days_scheduled,
    CAST(COALESCE(s.days_for_shipping_real, 0) AS INT) AS days_real,
    COALESCE(s.delivery_status, 'UNKNOWN') AS delivery_status,
    
    -- KPI: ¿Llegó tarde?
    CASE 
        WHEN CAST(COALESCE(s.days_for_shipping_real, 999) AS INT) > 
             CAST(COALESCE(s.days_for_shipment_scheduled, 0) AS INT)
        THEN TRUE 
        ELSE FALSE 
    END AS is_late,
    
    -- KPI: OTIF (A tiempo AND No cancelado)
    CASE 
        WHEN CAST(COALESCE(s.days_for_shipping_real, 999) AS INT) <= 
             CAST(COALESCE(s.days_for_shipment_scheduled, 0) AS INT)
             AND s.order_status NOT IN ('CANCELED', 'SUSPECTED_FRAUD', 'PENDING')
        THEN TRUE 
        ELSE FALSE 
    END AS is_otif

FROM dw.stg_raw_orders s
LEFT JOIN dw.dim_customers c ON s.customer_id = c.source_customer_id
LEFT JOIN dw.dim_products p ON s.product_card_id = p.source_product_id
LEFT JOIN dw.dim_geography g ON 
    UPPER(TRIM(COALESCE(s.order_city, 'UNKNOWN'))) = UPPER(TRIM(g.city)) AND
    UPPER(TRIM(COALESCE(s.order_country, 'UNKNOWN'))) = UPPER(TRIM(g.country))
WHERE s.order_item_id IS NOT NULL;

COMMIT;

-- Crear índices para optimización
CREATE INDEX idx_fact_orders_date ON dw.fact_orders(date_key);
CREATE INDEX idx_fact_orders_customer ON dw.fact_orders(customer_key);
CREATE INDEX idx_fact_orders_product ON dw.fact_orders(product_key);
CREATE INDEX idx_fact_orders_geo ON dw.fact_orders(geo_key);
CREATE INDEX idx_fact_orders_otif ON dw.fact_orders(is_otif);
CREATE INDEX idx_fact_orders_late ON dw.fact_orders(is_late);

COMMIT;

-- ===================================================================
-- PASO 3: VALIDACIÓN DE CALIDAD
-- ===================================================================

-- 📊 3.1 TASA OTIF GLOBAL
SELECT 
    '[QA] OTIF Global' AS metrica,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN is_otif THEN 1 ELSE 0 END) AS perfect_orders,
    ROUND((SUM(CASE WHEN is_otif THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 2) AS otif_percentage
FROM dw.fact_orders;

-- 📊 3.2 ENTREGAS TARDE
SELECT 
    '[QA] Late Deliveries' AS metrica,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN is_late THEN 1 ELSE 0 END) AS late_orders,
    ROUND((SUM(CASE WHEN is_late THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 2) AS late_percentage
FROM dw.fact_orders;

-- 📊 3.3 REVENUE AT RISK (Pérdida por entregas tardías)
SELECT 
    '[QA] Revenue at Risk' AS metrica,
    SUM(sales_amount)::DECIMAL(12,2) AS total_revenue,
    SUM(CASE WHEN is_late THEN sales_amount ELSE 0 END)::DECIMAL(12,2) AS revenue_at_risk,
    ROUND((SUM(CASE WHEN is_late THEN sales_amount ELSE 0 END)::DECIMAL / SUM(sales_amount)) * 100, 2) AS risk_percentage
FROM dw.fact_orders;

-- 📊 3.4 TOP 5 MERCADOS PROBLEMÁTICOS
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
    COUNT(*) AS count,
    ROUND((COUNT(*)::DECIMAL / (SELECT COUNT(*) FROM dw.fact_orders)) * 100, 2) AS percentage
FROM dw.fact_orders
GROUP BY delivery_status
ORDER BY count DESC;

-- 📊 3.6 CONTAR RECORDS EN TABLAS
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
