-- ============================================================================
-- TORRE CONTROL - SQL Queries
-- Respondiendo las 5 Preguntas Estratégicas
-- ============================================================================

-- ============================================================================
-- Q1: VISIBILITY OF SERVICE (OTIF - On-Time In-Full)
-- ============================================================================
-- Pregunta: "¿Cuál es nuestro porcentaje real de entregas perfectas?"
-- Respuesta: OTIF% global y por mercado/región/segmento

SELECT 
    '--- Q1: OTIF GLOBAL ---' as question;

-- Q1a: OTIF Global
SELECT 
    'GLOBAL' as level,
    COUNT(*) as total_orders,
    SUM(CASE WHEN late_delivery_risk = 0 AND delivery_status != 'Canceled' 
             THEN 1 ELSE 0 END) as otif_count,
    ROUND(100.0 * SUM(CASE WHEN late_delivery_risk = 0 AND delivery_status != 'Canceled' 
                           THEN 1 ELSE 0 END) / COUNT(*), 2) as otif_percentage
FROM dw.fact_orders
WHERE is_valid = TRUE;

-- Q1b: OTIF by Market
SELECT 
    g.market,
    COUNT(*) as total_orders,
    SUM(CASE WHEN f.late_delivery_risk = 0 AND f.delivery_status != 'Canceled' 
             THEN 1 ELSE 0 END) as otif_count,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 0 AND f.delivery_status != 'Canceled' 
                           THEN 1 ELSE 0 END) / COUNT(*), 2) as otif_percentage,
    ROUND(AVG(f.days_for_shipping_real), 1) as avg_days_real,
    ROUND(AVG(f.days_for_shipment_scheduled), 1) as avg_days_scheduled,
    ROUND(AVG(f.days_for_shipping_real) / NULLIF(AVG(f.days_for_shipment_scheduled), 0), 2) as delay_ratio
FROM dw.fact_orders f
JOIN dw.dim_geography g ON f.geography_id = g.geography_id
WHERE f.is_valid = TRUE
GROUP BY g.market
ORDER BY otif_percentage ASC;

-- Q1c: OTIF by Customer Segment
SELECT 
    c.customer_segment,
    COUNT(*) as total_orders,
    SUM(CASE WHEN f.late_delivery_risk = 0 AND f.delivery_status != 'Canceled' 
             THEN 1 ELSE 0 END) as otif_count,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 0 AND f.delivery_status != 'Canceled' 
                           THEN 1 ELSE 0 END) / COUNT(*), 2) as otif_percentage
FROM dw.fact_orders f
JOIN dw.dim_customer c ON f.customer_id = c.customer_id
WHERE f.is_valid = TRUE
GROUP BY c.customer_segment
ORDER BY otif_percentage ASC;

-- Q1d: OTIF by Product Category
SELECT 
    p.category_name,
    COUNT(*) as total_orders,
    SUM(CASE WHEN f.late_delivery_risk = 0 AND f.delivery_status != 'Canceled' 
             THEN 1 ELSE 0 END) as otif_count,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 0 AND f.delivery_status != 'Canceled' 
                           THEN 1 ELSE 0 END) / COUNT(*), 2) as otif_percentage
FROM dw.fact_orders f
JOIN dw.dim_product p ON f.product_id = p.product_id
WHERE f.is_valid = TRUE
GROUP BY p.category_name
ORDER BY otif_percentage ASC;

-- ============================================================================
-- Q2: REVENUE AT RISK (Financial Impact)
-- ============================================================================
-- Pregunta: "¿Cuánto dinero estamos poniendo en riesgo por entregas tardías?"
-- Respuesta: Revenue at risk por mercado, segmento, categoría

SELECT 
    '--- Q2: REVENUE AT RISK ---' as question;

-- Q2a: Revenue at Risk Global
SELECT 
    'GLOBAL' as segment,
    ROUND(SUM(sales), 2) as total_revenue,
    ROUND(SUM(CASE WHEN late_delivery_risk = 1 THEN sales ELSE 0 END), 2) as revenue_at_risk,
    ROUND(100.0 * SUM(CASE WHEN late_delivery_risk = 1 THEN sales ELSE 0 END) / 
          NULLIF(SUM(sales), 0), 2) as revenue_at_risk_pct,
    ROUND(AVG(CASE WHEN late_delivery_risk = 0 THEN sales ELSE NULL END), 2) as avg_on_time_order,
    ROUND(AVG(CASE WHEN late_delivery_risk = 1 THEN sales ELSE NULL END), 2) as avg_late_order
FROM dw.fact_orders
WHERE is_valid = TRUE;

-- Q2b: Revenue at Risk by Customer Segment
SELECT 
    c.customer_segment,
    COUNT(*) as order_count,
    ROUND(SUM(f.sales), 2) as total_revenue,
    ROUND(SUM(CASE WHEN f.late_delivery_risk = 1 THEN f.sales ELSE 0 END), 2) as revenue_at_risk,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 1 THEN f.sales ELSE 0 END) / 
          NULLIF(SUM(f.sales), 0), 2) as revenue_at_risk_pct
FROM dw.fact_orders f
JOIN dw.dim_customer c ON f.customer_id = c.customer_id
WHERE f.is_valid = TRUE
GROUP BY c.customer_segment
ORDER BY revenue_at_risk DESC;

-- Q2c: Revenue at Risk by Market
SELECT 
    g.market,
    ROUND(SUM(f.sales), 2) as total_revenue,
    ROUND(SUM(CASE WHEN f.late_delivery_risk = 1 THEN f.sales ELSE 0 END), 2) as revenue_at_risk,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 1 THEN f.sales ELSE 0 END) / 
          NULLIF(SUM(f.sales), 0), 2) as revenue_at_risk_pct
FROM dw.fact_orders f
JOIN dw.dim_geography g ON f.geography_id = g.geography_id
WHERE f.is_valid = TRUE
GROUP BY g.market
ORDER BY revenue_at_risk DESC;

-- Q2d: Top 10 Products/Categories at Risk
SELECT 
    p.category_name,
    p.product_name,
    COUNT(*) as order_count,
    ROUND(SUM(f.sales), 2) as total_revenue,
    ROUND(SUM(CASE WHEN f.late_delivery_risk = 1 THEN f.sales ELSE 0 END), 2) as revenue_at_risk,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 1 THEN f.sales ELSE 0 END) / 
          NULLIF(SUM(f.sales), 0), 2) as revenue_at_risk_pct
FROM dw.fact_orders f
JOIN dw.dim_product p ON f.product_id = p.product_id
WHERE f.is_valid = TRUE
GROUP BY p.category_name, p.product_name
HAVING SUM(CASE WHEN f.late_delivery_risk = 1 THEN f.sales ELSE 0 END) > 0
ORDER BY revenue_at_risk DESC
LIMIT 10;

-- ============================================================================
-- Q3: CHURN RISK (Customer Retention)
-- ============================================================================
-- Pregunta: "¿Quiénes son nuestros clientes VIP en riesgo de irse?"
-- Respuesta: Top 10% customers con 2+ órdenes tardías

SELECT 
    '--- Q3: CHURN RISK - VIP AT RISK ---' as question;

-- Q3a: VIP Customers at Churn Risk (Top 10% by LTV)
WITH top_10pct_customers AS (
    SELECT 
        customer_id,
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY sales_per_customer) as ltv_90th_pctl
    FROM dw.dim_customer
    WHERE is_valid = TRUE
    GROUP BY customer_id
)
SELECT 
    c.customer_id,
    c.customer_name,
    c.customer_email,
    c.customer_segment,
    c.sales_per_customer as ltv,
    COUNT(f.order_id) as total_orders,
    SUM(CASE WHEN f.late_delivery_risk = 1 THEN 1 ELSE 0 END) as late_orders_count,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 1 THEN 1 ELSE 0 END) / 
          NULLIF(COUNT(*), 0), 2) as late_order_pct,
    MAX(f.days_for_shipping_real - f.days_for_shipment_scheduled) as max_days_late
FROM dw.dim_customer c
JOIN dw.fact_orders f ON c.customer_id = f.customer_id
WHERE c.is_valid = TRUE 
  AND f.is_valid = TRUE
  AND c.sales_per_customer >= (SELECT ltv_90th_pctl FROM top_10pct_customers LIMIT 1)
  AND SUM(CASE WHEN f.late_delivery_risk = 1 THEN 1 ELSE 0 END) >= 2
GROUP BY c.customer_id, c.customer_name, c.customer_email, c.customer_segment, c.sales_per_customer
ORDER BY c.sales_per_customer DESC;

-- Q3b: Churn Risk Score (Recent Late Orders)
SELECT 
    c.customer_id,
    c.customer_name,
    c.customer_email,
    c.customer_segment,
    c.sales_per_customer,
    COUNT(DISTINCT DATE_TRUNC('month', d.order_date)) as months_with_orders,
    COUNT(f.order_id) as last_n_orders,
    SUM(CASE WHEN f.late_delivery_risk = 1 THEN 1 ELSE 0 END) as late_in_last_orders,
    CASE 
        WHEN SUM(CASE WHEN f.late_delivery_risk = 1 THEN 1 ELSE 0 END) >= 2 
         AND c.sales_per_customer >= 10000 THEN 'CRITICAL'
        WHEN SUM(CASE WHEN f.late_delivery_risk = 1 THEN 1 ELSE 0 END) >= 2 
         AND c.sales_per_customer >= 5000 THEN 'HIGH'
        WHEN SUM(CASE WHEN f.late_delivery_risk = 1 THEN 1 ELSE 0 END) = 1 
         AND c.sales_per_customer >= 5000 THEN 'MEDIUM'
        ELSE 'LOW'
    END as churn_risk_level,
    'CALL TODAY FOR RETENTION' as recommended_action
FROM dw.dim_customer c
JOIN dw.fact_orders f ON c.customer_id = f.customer_id
JOIN dw.dim_date d ON f.date_id = d.date_id
WHERE c.is_valid = TRUE 
  AND f.is_valid = TRUE
  AND d.order_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY c.customer_id, c.customer_name, c.customer_email, c.customer_segment, c.sales_per_customer
HAVING SUM(CASE WHEN f.late_delivery_risk = 1 THEN 1 ELSE 0 END) >= 1
ORDER BY c.sales_per_customer DESC;

-- ============================================================================
-- Q4: GEOGRAPHIC EFFICIENCY (Network Optimization)
-- ============================================================================
-- Pregunta: "¿Existen 'agujeros negros' en nuestra red?"
-- Respuesta: OTIF% drill-down: Market → Region → State → City

SELECT 
    '--- Q4: GEOGRAPHIC HEATMAP ---' as question;

-- Q4a: OTIF by Market → Region (Drill-down Level 1)
SELECT 
    g.market,
    g.region,
    COUNT(*) as total_orders,
    SUM(CASE WHEN f.late_delivery_risk = 0 AND f.delivery_status != 'Canceled' 
             THEN 1 ELSE 0 END) as otif_count,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 0 AND f.delivery_status != 'Canceled' 
                           THEN 1 ELSE 0 END) / COUNT(*), 2) as otif_percentage,
    ROUND(SUM(f.sales), 2) as total_revenue,
    CASE 
        WHEN ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) >= 90 THEN '🟢 OK'
        WHEN ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) >= 80 THEN '🟡 WARN'
        ELSE '🔴 CRITICAL'
    END as status
FROM dw.fact_orders f
JOIN dw.dim_geography g ON f.geography_id = g.geography_id
WHERE f.is_valid = TRUE
GROUP BY g.market, g.region
ORDER BY otif_percentage ASC;

-- Q4b: OTIF by State (Geographic Drill-down Level 2)
SELECT 
    g.market,
    g.region,
    g.state,
    COUNT(*) as total_orders,
    SUM(CASE WHEN f.late_delivery_risk = 0 AND f.delivery_status != 'Canceled' 
             THEN 1 ELSE 0 END) as otif_count,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 0 AND f.delivery_status != 'Canceled' 
                           THEN 1 ELSE 0 END) / COUNT(*), 2) as otif_percentage
FROM dw.fact_orders f
JOIN dw.dim_geography g ON f.geography_id = g.geography_id
WHERE f.is_valid = TRUE
GROUP BY g.market, g.region, g.state
ORDER BY otif_percentage ASC;

-- Q4c: Problem Areas (Markets with OTIF < 80%)
SELECT 
    g.market,
    g.region,
    COUNT(*) as order_count,
    ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as otif_pct,
    ROUND(SUM(f.sales), 2) as revenue,
    'INVESTIGATE & IMPROVE' as recommendation
FROM dw.fact_orders f
JOIN dw.dim_geography g ON f.geography_id = g.geography_id
WHERE f.is_valid = TRUE
GROUP BY g.market, g.region
HAVING ROUND(100.0 * SUM(CASE WHEN f.late_delivery_risk = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) < 80
ORDER BY otif_pct ASC;

-- ============================================================================
-- Q5: FRAUD & ANOMALY DETECTION
-- ============================================================================
-- Pregunta: "¿Cuánto inventario estamos perdiendo por fraude/anomalías?"
-- Respuesta: Loss ($) por status + flags de anomalías

SELECT 
    '--- Q5: FRAUD & ANOMALIES ---' as question;

-- Q5a: Inventory Loss by Order Status
SELECT 
    COALESCE(order_status, 'UNKNOWN') as order_status,
    COUNT(*) as order_count,
    ROUND(SUM(sales), 2) as total_loss,
    ROUND(AVG(sales), 2) as avg_loss_per_order,
    CASE 
        WHEN order_status IN ('SUSPECTED_FRAUD', 'LOST') THEN 'HIGH PRIORITY'
        WHEN order_status IN ('CANCELED', 'PENDING_PAYMENT') THEN 'MEDIUM'
        ELSE 'LOW'
    END as priority
FROM dw.fact_orders
WHERE is_valid = TRUE 
  AND order_status IN ('SUSPECTED_FRAUD', 'LOST', 'CANCELED', 'PENDING', 'ON_HOLD', 'PAYMENT_REVIEW')
GROUP BY order_status
ORDER BY total_loss DESC;

-- Q5b: Anomalies (Days > 60 or high discount + high value)
SELECT 
    order_id,
    order_item_id,
    COALESCE(order_status, 'UNKNOWN') as order_status,
    days_for_shipping_real,
    days_for_shipment_scheduled,
    order_item_discount_rate,
    ROUND(sales, 2) as sales_value,
    CASE 
        WHEN days_for_shipping_real > 60 THEN 'DAYS_OUTLIER'
        WHEN order_item_discount_rate > 50 AND sales > 1000 THEN 'DISCOUNT_VALUE_COMBO'
        WHEN order_status = 'SUSPECTED_FRAUD' THEN 'FRAUD_FLAG'
        ELSE 'OTHER'
    END as anomaly_type,
    CASE 
        WHEN days_for_shipping_real > 60 THEN 'CRITICAL'
        WHEN order_status = 'SUSPECTED_FRAUD' THEN 'HIGH'
        ELSE 'MEDIUM'
    END as risk_level
FROM dw.fact_orders
WHERE is_valid = TRUE 
  AND (days_for_shipping_real > 60 
       OR (order_item_discount_rate > 50 AND sales > 1000)
       OR order_status = 'SUSPECTED_FRAUD')
ORDER BY sales DESC
LIMIT 50;

-- Q5c: Total Inventory Loss Summary
SELECT 
    ROUND(SUM(CASE WHEN order_status IN ('SUSPECTED_FRAUD', 'LOST') THEN sales ELSE 0 END), 2) as fraud_loss,
    ROUND(SUM(CASE WHEN order_status = 'CANCELED' THEN sales ELSE 0 END), 2) as canceled_loss,
    ROUND(SUM(CASE WHEN days_for_shipping_real > 60 THEN sales ELSE 0 END), 2) as delayed_anomaly_loss,
    ROUND(SUM(CASE WHEN order_status IN ('SUSPECTED_FRAUD', 'LOST', 'CANCELED') 
                    OR days_for_shipping_real > 60 THEN sales ELSE 0 END), 2) as total_loss
FROM dw.fact_orders
WHERE is_valid = TRUE;

-- ============================================================================
-- Fin de queries
-- ============================================================================
\echo '✅ Queries Q1-Q5 listas para ejecución'
