-- Dimensión Clientes
CREATE TABLE dw.dim_customers (
    customer_key SERIAL PRIMARY KEY,
    source_customer_id BIGINT,
    fname VARCHAR(100),
    lname VARCHAR(100),
    segment VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(100)
);

INSERT INTO dw.dim_customers (source_customer_id, fname, lname, segment, state, country)
SELECT DISTINCT 
    customer_id,
    COALESCE(customer_fname, 'UNKNOWN'), 
    COALESCE(customer_lname, 'UNKNOWN'), 
    customer_segment, 
    customer_state,
    customer_country
FROM dw.stg_raw_orders
WHERE customer_id IS NOT NULL;

-- Dimensión Productos
CREATE TABLE dw.dim_products (
    product_key SERIAL PRIMARY KEY,
    source_product_id BIGINT,
    product_name VARCHAR(255),
    category_name VARCHAR(100),
    department_name VARCHAR(100),
    product_price DECIMAL(10,2)
);

INSERT INTO dw.dim_products (source_product_id, product_name, category_name, department_name, product_price)
SELECT DISTINCT 
    product_card_id,
    product_name, 
    category_name, 
    department_name, 
    product_price::DECIMAL(10,2)
FROM dw.stg_raw_orders
WHERE product_card_id IS NOT NULL;

-- Dimensión Geografía
CREATE TABLE dw.dim_geography (
    geo_key SERIAL PRIMARY KEY,
    market VARCHAR(50),
    region VARCHAR(100),
    country VARCHAR(100),
    city VARCHAR(100)
);

INSERT INTO dw.dim_geography (market, region, country, city)
SELECT DISTINCT 
    market, 
    order_region, 
    order_country, 
    order_city
FROM dw.stg_raw_orders
WHERE market IS NOT NULL AND order_city IS NOT NULL;

-- Fact Table
CREATE TABLE dw.fact_orders (
    fact_id SERIAL PRIMARY KEY,
    order_id VARCHAR(50),
    order_item_id BIGINT,
    
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

-- Insert data
INSERT INTO dw.fact_orders (
    order_id, order_item_id, date_key, customer_key, product_key, geo_key,
    sales_amount, profit_amount, discount_amount,
    order_quantity, days_scheduled, days_real, delivery_status,
    is_late, is_otif
)
SELECT 
    s.order_id,
    s.order_item_id,
    20260131::INT,
    COALESCE(c.customer_key, 0),
    COALESCE(p.product_key, 0),
    COALESCE(g.geo_key, 0),
    
    s.sales::DECIMAL(12,2),
    s.benefit_per_order::DECIMAL(12,2),
    s.order_item_discount::DECIMAL(12,2),
    
    s.order_item_quantity::INT,
    s.days_for_shipment_scheduled::INT,
    s.days_for_shipping_real::INT,
    s.delivery_status,
    
    s.days_for_shipping_real::INT > s.days_for_shipment_scheduled::INT,
    
    s.days_for_shipping_real::INT <= s.days_for_shipment_scheduled::INT 
    AND s.order_status NOT IN ('CANCELED', 'SUSPECTED_FRAUD')

FROM dw.stg_raw_orders s
LEFT JOIN dw.dim_customers c ON s.customer_id = c.source_customer_id
LEFT JOIN dw.dim_products p ON s.product_card_id = p.source_product_id
LEFT JOIN dw.dim_geography g ON 
    s.order_city = g.city AND
    s.order_country = g.country
WHERE s.order_item_id IS NOT NULL;

-- Índices
CREATE INDEX idx_fact_orders_date ON dw.fact_orders(date_key);
CREATE INDEX idx_fact_orders_customer ON dw.fact_orders(customer_key);
CREATE INDEX idx_fact_orders_product ON dw.fact_orders(product_key);
CREATE INDEX idx_fact_orders_geo ON dw.fact_orders(geo_key);
CREATE INDEX idx_fact_orders_otif ON dw.fact_orders(is_otif);
CREATE INDEX idx_fact_orders_late ON dw.fact_orders(is_late);
