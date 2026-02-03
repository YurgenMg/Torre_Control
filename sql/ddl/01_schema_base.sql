-- ============================================================================
-- TORRE CONTROL - Data Warehouse Schema
-- DDL (Data Definition Language) - Definición de tablas dimensionales y de hechos
-- ============================================================================
-- Ejecución: psql -U admin -d supply_chain_dw -f sql/ddl/01_schema_base.sql

-- Crear esquema
CREATE SCHEMA IF NOT EXISTS dw;

-- ============================================================================
-- DIMENSION: dim_customer (Clientes)
-- ============================================================================
DROP TABLE IF EXISTS dw.dim_customer CASCADE;
CREATE TABLE dw.dim_customer (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    customer_fname VARCHAR(100),
    customer_lname VARCHAR(100),
    customer_email VARCHAR(100),
    customer_segment VARCHAR(50) NOT NULL,  -- Consumer, Corporate, Home Office
    customer_country VARCHAR(100),
    customer_state VARCHAR(100),
    customer_city VARCHAR(100),
    customer_street VARCHAR(255),
    customer_zipcode VARCHAR(20),
    sales_per_customer NUMERIC(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_customer_segment ON dw.dim_customer(customer_segment);
CREATE INDEX idx_customer_country ON dw.dim_customer(customer_country);

-- ============================================================================
-- DIMENSION: dim_geography (Geografía - Jerarquía Market→Region→State→City)
-- ============================================================================
DROP TABLE IF EXISTS dw.dim_geography CASCADE;
CREATE TABLE dw.dim_geography (
    geography_id SERIAL PRIMARY KEY,
    market VARCHAR(50) NOT NULL,  -- Africa, Europe, LATAM, Pacific Asia, USCA
    region VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    state VARCHAR(100),
    city VARCHAR(100),
    latitude NUMERIC(10,6),
    longitude NUMERIC(10,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(market, region, country, state, city)
);

CREATE INDEX idx_market ON dw.dim_geography(market);
CREATE INDEX idx_region ON dw.dim_geography(region);
CREATE INDEX idx_country ON dw.dim_geography(country);

-- ============================================================================
-- DIMENSION: dim_product (Productos)
-- ============================================================================
DROP TABLE IF EXISTS dw.dim_product CASCADE;
CREATE TABLE dw.dim_product (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    product_description TEXT,
    category_id VARCHAR(50),
    category_name VARCHAR(100),
    department_id VARCHAR(50),
    department_name VARCHAR(100),
    product_price NUMERIC(15,2),
    product_image VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_product_category ON dw.dim_product(category_name);
CREATE INDEX idx_product_department ON dw.dim_product(department_name);

-- ============================================================================
-- DIMENSION: dim_date (Fecha - Dimensión temporal)
-- ============================================================================
DROP TABLE IF EXISTS dw.dim_date CASCADE;
CREATE TABLE dw.dim_date (
    date_id INTEGER PRIMARY KEY,
    order_date DATE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    week INTEGER,
    day_of_month INTEGER,
    day_of_week INTEGER,
    month_name VARCHAR(20),
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN DEFAULT FALSE,
    UNIQUE(order_date)
);

CREATE INDEX idx_order_date ON dw.dim_date(order_date);
CREATE INDEX idx_year_month ON dw.dim_date(year, month);

-- ============================================================================
-- FACT TABLE: fact_orders (Órdenes - Grano: Order Item)
-- ============================================================================
DROP TABLE IF EXISTS dw.fact_orders CASCADE;
CREATE TABLE dw.fact_orders (
    order_id VARCHAR(50) NOT NULL,
    order_item_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    geography_id INTEGER NOT NULL,
    date_id INTEGER NOT NULL,
    
    -- Dimensiones de envío
    days_for_shipping_real INTEGER,
    days_for_shipment_scheduled INTEGER,
    delivery_status VARCHAR(50),
    order_status VARCHAR(50),
    late_delivery_risk INTEGER,  -- 0 = on-time, 1 = late
    
    -- Dimensiones de descuento/promoción
    order_item_discount NUMERIC(15,2),
    order_item_discount_rate NUMERIC(5,2),
    
    -- Medidas financieras
    sales NUMERIC(15,2),
    benefit_per_order NUMERIC(15,2),
    order_item_total NUMERIC(15,2),
    order_profit_per_order NUMERIC(15,2),
    order_item_profit_ratio NUMERIC(5,2),
    
    -- Medidas de cantidad
    order_item_quantity INTEGER,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE,
    is_outlier BOOLEAN DEFAULT FALSE,
    quality_flag VARCHAR(100),
    
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (customer_id) REFERENCES dw.dim_customer(customer_id),
    FOREIGN KEY (product_id) REFERENCES dw.dim_product(product_id),
    FOREIGN KEY (geography_id) REFERENCES dw.dim_geography(geography_id),
    FOREIGN KEY (date_id) REFERENCES dw.dim_date(date_id)
);

-- Índices para performance
CREATE INDEX idx_fact_customer ON dw.fact_orders(customer_id);
CREATE INDEX idx_fact_product ON dw.fact_orders(product_id);
CREATE INDEX idx_fact_geography ON dw.fact_orders(geography_id);
CREATE INDEX idx_fact_date ON dw.fact_orders(date_id);
CREATE INDEX idx_fact_late_delivery ON dw.fact_orders(late_delivery_risk);
CREATE INDEX idx_fact_delivery_status ON dw.fact_orders(delivery_status);
CREATE INDEX idx_fact_order_status ON dw.fact_orders(order_status);

-- ============================================================================
-- TABLA DE AUDITORÍA: etl_log (Registro de ejecuciones ETL)
-- ============================================================================
DROP TABLE IF EXISTS dw.etl_log CASCADE;
CREATE TABLE dw.etl_log (
    etl_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    operation VARCHAR(50),  -- INSERT, UPDATE, DELETE
    rows_affected INTEGER,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(50),  -- SUCCESS, FAILED, PARTIAL
    error_message TEXT,
    processed_records INTEGER,
    failed_records INTEGER
);

-- ============================================================================
-- VISTAS ANALÍTICAS (Aggregated views para queries rápidas)
-- ============================================================================

-- Vista: OTIF Summary by Market
CREATE OR REPLACE VIEW dw.v_otif_by_market AS
SELECT 
    g.market,
    COUNT(*) as total_orders,
    SUM(CASE WHEN f.late_delivery_risk = 0 AND f.delivery_status != 'Canceled' 
             THEN 1 ELSE 0 END) as otif_count,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 0 AND f.delivery_status != 'Canceled' 
                           THEN 1 ELSE 0 END) / COUNT(*), 2) as otif_percentage,
    ROUND(AVG(f.days_for_shipping_real), 1) as avg_days_real,
    ROUND(AVG(f.days_for_shipment_scheduled), 1) as avg_days_scheduled
FROM dw.fact_orders f
JOIN dw.dim_geography g ON f.geography_id = g.geography_id
WHERE f.is_valid = TRUE
GROUP BY g.market
ORDER BY otif_percentage DESC;

-- Vista: Revenue at Risk
CREATE OR REPLACE VIEW dw.v_revenue_at_risk AS
SELECT 
    'Total' as segment,
    SUM(f.sales) as total_revenue,
    SUM(CASE WHEN f.late_delivery_risk = 1 THEN f.sales ELSE 0 END) as revenue_at_risk,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 1 THEN f.sales ELSE 0 END) / 
          SUM(f.sales), 2) as revenue_at_risk_pct
FROM dw.fact_orders f
WHERE f.is_valid = TRUE;

-- Vista: VIP Customers at Churn Risk
CREATE OR REPLACE VIEW dw.v_churn_risk_vip AS
SELECT 
    c.customer_id,
    c.customer_name,
    c.customer_email,
    c.customer_segment,
    c.sales_per_customer,
    COUNT(f.order_id) as total_orders,
    SUM(CASE WHEN f.late_delivery_risk = 1 THEN 1 ELSE 0 END) as late_orders_count,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 1 THEN 1 ELSE 0 END) / 
          COUNT(*), 2) as late_order_pct
FROM dw.dim_customer c
JOIN dw.fact_orders f ON c.customer_id = f.customer_id
WHERE c.is_valid = TRUE AND f.is_valid = TRUE
GROUP BY c.customer_id, c.customer_name, c.customer_email, c.customer_segment, c.sales_per_customer
HAVING COUNT(f.order_id) >= 2 AND SUM(CASE WHEN f.late_delivery_risk = 1 THEN 1 ELSE 0 END) >= 2
ORDER BY c.sales_per_customer DESC;

-- Vista: Fraud & Anomalies
CREATE OR REPLACE VIEW dw.v_fraud_anomalies AS
SELECT 
    f.order_id,
    f.order_item_id,
    f.delivery_status,
    f.order_status,
    f.days_for_shipping_real,
    f.order_item_discount_rate,
    f.sales,
    f.quality_flag,
    CASE 
        WHEN f.order_status = 'SUSPECTED_FRAUD' THEN 'HIGH'
        WHEN f.days_for_shipping_real > 60 THEN 'HIGH'
        WHEN f.order_item_discount_rate > 50 AND f.sales > 1000 THEN 'MEDIUM'
        ELSE 'LOW'
    END as risk_level
FROM dw.fact_orders f
WHERE f.is_valid = TRUE AND (
    f.order_status IN ('SUSPECTED_FRAUD', 'LOST', 'PENDING')
    OR f.days_for_shipping_real > 60
    OR (f.order_item_discount_rate > 50 AND f.sales > 1000)
)
ORDER BY f.sales DESC;

-- ============================================================================
-- TABLA STAGING: stg_raw_orders (Datos crudos antes de transformación)
-- ============================================================================
DROP TABLE IF EXISTS dw.stg_raw_orders CASCADE;
CREATE TABLE dw.stg_raw_orders (
    -- Raw fields (mapeados 1:1 desde CSV)
    type VARCHAR(50),
    days_for_shipping_real INTEGER,
    days_for_shipment_scheduled INTEGER,
    benefit_per_order NUMERIC(15,2),
    sales_per_customer NUMERIC(15,2),
    delivery_status VARCHAR(50),
    late_delivery_risk INTEGER,
    category_id VARCHAR(50),
    category_name VARCHAR(100),
    customer_city VARCHAR(100),
    customer_country VARCHAR(100),
    customer_email VARCHAR(100),
    customer_fname VARCHAR(100),
    customer_id VARCHAR(50),
    customer_lname VARCHAR(100),
    customer_segment VARCHAR(50),
    customer_state VARCHAR(100),
    customer_street VARCHAR(255),
    customer_zipcode VARCHAR(20),
    department_id VARCHAR(50),
    department_name VARCHAR(100),
    latitude NUMERIC(10,6),
    longitude NUMERIC(10,6),
    market VARCHAR(50),
    order_city VARCHAR(100),
    order_country VARCHAR(100),
    order_customer_id VARCHAR(50),
    order_date DATE,
    order_id VARCHAR(50),
    order_item_cardprod_id VARCHAR(50),
    order_item_discount NUMERIC(15,2),
    order_item_discount_rate NUMERIC(5,2),
    order_item_id VARCHAR(50),
    order_item_product_price NUMERIC(15,2),
    order_item_profit_ratio NUMERIC(5,2),
    order_item_quantity INTEGER,
    sales NUMERIC(15,2),
    order_item_total NUMERIC(15,2),
    order_profit_per_order NUMERIC(15,2),
    order_region VARCHAR(100),
    order_state VARCHAR(100),
    order_status VARCHAR(50),
    product_card_id VARCHAR(50),
    product_category_id VARCHAR(50),
    product_description TEXT,
    product_image VARCHAR(500),
    product_name VARCHAR(255),
    product_price NUMERIC(15,2),
    
    -- Auditoría
    source_file VARCHAR(255),
    load_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_processed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_stg_order_id ON dw.stg_raw_orders(order_id);
CREATE INDEX idx_stg_customer_id ON dw.stg_raw_orders(customer_id);
CREATE INDEX idx_stg_is_processed ON dw.stg_raw_orders(is_processed);

-- ============================================================================
-- Mensaje de confirmación
-- ============================================================================
\echo '✅ Schema DDL ejecutado exitosamente'
\echo '📊 Tablas creadas:'
\echo '   - dim_customer'
\echo '   - dim_geography'
\echo '   - dim_product'
\echo '   - dim_date'
\echo '   - fact_orders'
\echo '   - etl_log'
\echo '   - stg_raw_orders'
\echo '🔍 Vistas creadas:'
\echo '   - v_otif_by_market'
\echo '   - v_revenue_at_risk'
\echo '   - v_churn_risk_vip'
\echo '   - v_fraud_anomalies'
