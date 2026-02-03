-- ===================================================================
-- CARGA DIRECTA DE CSV A STAGING USANDO COPY (Fase 2.1)
-- ===================================================================
-- Método: PostgreSQL COPY command (mucho más rápido que inserts)
-- Tiempo estimado: < 30 segundos para 100K+ filas

-- 1. Recrear tabla stg_raw_orders (borrar + crear)
DROP TABLE IF EXISTS dw.stg_raw_orders CASCADE;

CREATE TABLE dw.stg_raw_orders (
    order_id VARCHAR(255),
    order_date_datefulfilled TIMESTAMP,
    ship_date_dateordered TIMESTAMP,
    ship_date_dateshipment TIMESTAMP,
    delivery_date TIMESTAMP,
    delivery_status VARCHAR(255),
    sales_per_customer NUMERIC,
    benefit_per_order NUMERIC,
    sales_in_product_category VARCHAR(255),
    profit_ratio NUMERIC,
    sales NUMERIC,
    profit NUMERIC,
    quantity_ordered INTEGER,
    quantity_shipped INTEGER,
    profit_per_order NUMERIC,
    customer_id VARCHAR(255),
    customer_fname VARCHAR(255),
    customer_lname VARCHAR(255),
    customer_email VARCHAR(255),
    customer_password VARCHAR(255),
    customer_segment VARCHAR(255),
    customer_address VARCHAR(255),
    customer_city VARCHAR(255),
    customer_state VARCHAR(255),
    customer_postal_code VARCHAR(255),
    customer_country VARCHAR(255),
    market VARCHAR(255),
    region VARCHAR(255),
    product_card_id VARCHAR(255),
    product_name VARCHAR(255),
    product_image_url VARCHAR(1024),
    department_name VARCHAR(255),
    category_id VARCHAR(255),
    category_name VARCHAR(255),
    product_description VARCHAR(1024),
    product_image_file_name VARCHAR(255),
    product_price NUMERIC,
    product_status VARCHAR(255),
    type VARCHAR(255),
    days_for_shipment_scheduled INTEGER,
    days_for_shipping_real INTEGER,
    order_item_discount NUMERIC,
    order_item_discount_rate NUMERIC,
    order_item_profit_ratio NUMERIC,
    order_item_quantity INTEGER,
    sales_per_order NUMERIC,
    order_item_total NUMERIC,
    order_profit_per_order NUMERIC,
    order_region VARCHAR(255),
    order_country VARCHAR(255),
    order_city VARCHAR(255),
    order_state VARCHAR(255),
    order_zipcode VARCHAR(255),
    order_item_id VARCHAR(255),
    order_item_cardid VARCHAR(255),
    late_delivery_risk INTEGER,
    order_status VARCHAR(255),
    product_image_last_updated TIMESTAMP
);

-- 2. Crear índices antes de la carga (para validación post-carga)
CREATE INDEX idx_stg_order_id ON dw.stg_raw_orders(order_id);
CREATE INDEX idx_stg_order_item_id ON dw.stg_raw_orders(order_item_id);
CREATE INDEX idx_stg_customer_id ON dw.stg_raw_orders(customer_id);

-- 3. Cargar CSV usando COPY (método nativo PostgreSQL - MÁS RÁPIDO)
-- NOTA: Ajusta la ruta según tu SO. Para Windows, use forward slashes
COPY dw.stg_raw_orders FROM '/data/raw/DataCoSupplyChainDataset.csv'
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'ISO88591');

-- 4. Validaciones post-carga
SELECT COUNT(*) as total_rows_loaded FROM dw.stg_raw_orders;

-- 5. Mostrar muestra de datos
SELECT 
    order_id,
    order_item_id,
    customer_id,
    product_name,
    sales,
    late_delivery_risk,
    delivery_status
FROM dw.stg_raw_orders 
LIMIT 10;

-- 6. Verificar duplicados en order_item_id (clave única)
SELECT 
    order_item_id, 
    COUNT(*) as count
FROM dw.stg_raw_orders 
GROUP BY order_item_id 
HAVING COUNT(*) > 1
LIMIT 20;
