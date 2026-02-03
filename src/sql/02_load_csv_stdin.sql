-- ===================================================================
-- CARGA ROBUSTA DE CSV A STAGING (Fase 2.1 - Versión 2)
-- ===================================================================
-- Estrategia: Crear tabla con columnas TEXTO, luego cargar con COPY
-- Esto evita problemas de tipo de dato en el CSV

-- 1. Borrar tabla antigua
DROP TABLE IF EXISTS dw.stg_raw_orders CASCADE;

-- 2. Crear tabla SIMPLE con todos los campos como TEXT (no validar tipos aún)
CREATE TABLE dw.stg_raw_orders (
    type TEXT,
    days_for_shipping_real TEXT,
    days_for_shipment_scheduled TEXT,
    benefit_per_order TEXT,
    sales_per_customer TEXT,
    delivery_status TEXT,
    late_delivery_risk TEXT,
    category_id TEXT,
    category_name TEXT,
    customer_city TEXT,
    customer_country TEXT,
    customer_email TEXT,
    customer_fname TEXT,
    customer_id TEXT,
    customer_lname TEXT,
    customer_password TEXT,
    customer_segment TEXT,
    customer_state TEXT,
    customer_street TEXT,
    customer_zipcode TEXT,
    department_id TEXT,
    department_name TEXT,
    latitude TEXT,
    longitude TEXT,
    market TEXT,
    order_city TEXT,
    order_country TEXT,
    order_customer_id TEXT,
    order_date_dateorders TEXT,
    order_id TEXT,
    order_item_cardprod_id TEXT,
    order_item_discount TEXT,
    order_item_discount_rate TEXT,
    order_item_id TEXT,
    order_item_product_price TEXT,
    order_item_profit_ratio TEXT,
    order_item_quantity TEXT,
    sales TEXT,
    order_item_total TEXT,
    order_profit_per_order TEXT,
    order_region TEXT,
    order_state TEXT,
    order_status TEXT,
    order_zipcode TEXT,
    product_card_id TEXT,
    product_category_id TEXT,
    product_description TEXT,
    product_image TEXT,
    product_name TEXT,
    product_price TEXT,
    product_status TEXT,
    shipping_date_dateorders TEXT,
    shipping_mode TEXT
);

-- 3. Cargar CSV usando COPY
-- PostgreSQL puede montarlo desde /data si está configurado en docker-compose
-- Alternativa: Usar stdin piped desde host
COPY dw.stg_raw_orders FROM stdin
    WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'ISO88591', QUOTE '"', ESCAPE '\');

-- 4. Crear índices
CREATE INDEX idx_stg_order_id ON dw.stg_raw_orders(order_id);
CREATE INDEX idx_stg_order_item_id ON dw.stg_raw_orders(order_item_id);
CREATE INDEX idx_stg_customer_id ON dw.stg_raw_orders(customer_id);

-- 5. Validaciones post-carga
SELECT COUNT(*) as total_rows_loaded FROM dw.stg_raw_orders;

-- 6. Mostrar muestra de 5 primeras filas
SELECT 
    order_id,
    order_item_id,
    customer_id,
    product_name,
    sales,
    late_delivery_risk,
    delivery_status
FROM dw.stg_raw_orders 
LIMIT 5;

-- 7. Verificar si hay duplicados en order_item_id
SELECT 
    order_item_id, 
    COUNT(*) as count
FROM dw.stg_raw_orders 
GROUP BY order_item_id 
HAVING COUNT(*) > 1
LIMIT 10;
