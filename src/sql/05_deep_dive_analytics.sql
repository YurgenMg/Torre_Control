-- ===================================================================
-- FASE 3: DEEP DIVE ANALYTICS - VISTAS AVANZADAS
-- ===================================================================
-- Propósito: Análisis diagnóstico para descubrir raíces del problema
-- Tarea 3.1: VIP Churn Risk (RFM - Recency, Frequency, Monetary)
-- Tarea 3.2: Pareto Analysis (80/20 - Qué causa el 80% de retrasos)

-- ===================================================================
-- 3.1 VIP CHURN RISK - VISTA RFM SIMPLIFICADA
-- ===================================================================

CREATE OR REPLACE VIEW dw.vw_vip_churn_risk AS
WITH CustomerMetrics AS (
    SELECT 
        c.customer_key,
        c.fname || ' ' || c.lname as full_name,
        c.segment,
        MAX(d.date) as last_order_date,
        COUNT(DISTINCT f.order_id) as order_frequency,
        SUM(f.sales_amount) as total_monetary,
        ROUND((SUM(CASE WHEN f.is_late THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 2) as failure_rate_pct
    FROM dw.fact_orders f
    JOIN dw.dim_customers c ON f.customer_key = c.customer_key
    JOIN dw.dim_date d ON f.date_key = d.date_id
    GROUP BY 1, 2, 3
),
RiskClassification AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY total_monetary DESC) as monetary_quintile,
        CASE 
            WHEN failure_rate_pct >= 50 THEN 'CRITICAL'
            WHEN failure_rate_pct >= 30 THEN 'HIGH'
            ELSE 'NORMAL' 
        END as risk_level
    FROM CustomerMetrics
)
SELECT 
    full_name,
    segment,
    order_frequency,
    ROUND(total_monetary::NUMERIC, 2) as total_spent,
    failure_rate_pct,
    risk_level,
    last_order_date,
    'VIP' as status
FROM RiskClassification
WHERE monetary_quintile = 1 -- Top 20% por gasto
  AND risk_level IN ('CRITICAL', 'HIGH') -- Con alto riesgo de fuga
ORDER BY total_monetary DESC;

-- ===================================================================
-- 3.2 PARETO ANALYSIS - PRODUCTOS PROBLEMÁTICOS (80/20)
-- ===================================================================

CREATE OR REPLACE VIEW dw.vw_pareto_delays AS
WITH ProductDelays AS (
    SELECT 
        p.product_name,
        p.category_name,
        p.department_name,
        COUNT(*) as total_orders,
        SUM(CASE WHEN f.is_late THEN 1 ELSE 0 END) as late_orders,
        ROUND((SUM(CASE WHEN f.is_late THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 2) as late_rate_pct
    FROM dw.fact_orders f
    JOIN dw.dim_products p ON f.product_key = p.product_key
    GROUP BY 1, 2, 3
),
CumulativeCalc AS (
    SELECT *,
        late_orders::DECIMAL / SUM(late_orders) OVER () as pct_of_total_delays,
        SUM(late_orders) OVER (ORDER BY late_orders DESC) as running_late_sum,
        SUM(late_orders) OVER () as grand_total_delays
    FROM ProductDelays
    WHERE late_orders > 0
)
SELECT 
    product_name,
    category_name,
    department_name,
    total_orders,
    late_orders,
    ROUND(late_rate_pct, 2) as late_rate_pct,
    ROUND(pct_of_total_delays * 100, 2) as contribution_pct,
    ROUND((running_late_sum::DECIMAL / grand_total_delays) * 100, 2) as cumulative_pareto_pct
FROM CumulativeCalc
ORDER BY late_orders DESC;

-- ===================================================================
-- 3.3 MARKET-LEVEL DIAGNOSTICS
-- ===================================================================

CREATE OR REPLACE VIEW dw.vw_market_diagnostics AS
SELECT 
    g.market,
    COUNT(*) as total_orders,
    SUM(CASE WHEN f.is_late THEN 1 ELSE 0 END) as late_orders,
    ROUND((SUM(CASE WHEN f.is_late THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 2) as late_rate_pct,
    ROUND(SUM(f.sales_amount)::NUMERIC, 2) as total_revenue,
    ROUND(SUM(CASE WHEN f.is_late THEN f.sales_amount ELSE 0 END)::NUMERIC, 2) as revenue_at_risk,
    COUNT(DISTINCT f.customer_key) as unique_customers,
    COUNT(DISTINCT f.product_key) as unique_products
FROM dw.fact_orders f
JOIN dw.dim_geography g ON f.geo_key = g.geo_key
GROUP BY 1
ORDER BY revenue_at_risk DESC;

-- ===================================================================
-- 3.4 TEMPORAL TRENDS (OTIF por mes)
-- ===================================================================

CREATE OR REPLACE VIEW dw.vw_temporal_trends AS
SELECT 
    d.year,
    d.month,
    d.month_name,
    COUNT(*) as total_orders,
    SUM(CASE WHEN f.is_late THEN 1 ELSE 0 END) as late_orders,
    ROUND((SUM(CASE WHEN f.is_late THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 2) as late_rate_pct,
    SUM(CASE WHEN f.is_otif THEN 1 ELSE 0 END) as perfect_orders,
    ROUND((SUM(CASE WHEN f.is_otif THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 2) as otif_rate_pct,
    ROUND(SUM(f.sales_amount)::NUMERIC, 2) as total_revenue
FROM dw.fact_orders f
JOIN dw.dim_date d ON f.date_key = d.date_id
GROUP BY 1, 2, 3
ORDER BY d.year DESC, d.month DESC;

-- ===================================================================
-- VALIDACIÓN Y EJECUCIÓN DE QUERIES
-- ===================================================================

-- QA 1: VIP Churn Risk
SELECT '[QA] VIP CHURN RISK' as test, COUNT(*) as vip_at_risk FROM dw.vw_vip_churn_risk;

-- QA 2: Pareto Top 10 Productos
SELECT '[QA] PARETO TOP 10' as test, COUNT(*) as problematic_products 
FROM (SELECT * FROM dw.vw_pareto_delays LIMIT 10) x;

-- QA 3: Market Diagnostics
SELECT '[QA] MARKET DIAGNOSTICS' as test, COUNT(*) as markets FROM dw.vw_market_diagnostics;

-- QA 4: Temporal Trends
SELECT '[QA] TEMPORAL TRENDS' as test, COUNT(*) as months FROM dw.vw_temporal_trends;

-- ===================================================================
-- DETALLE: TOP 5 VIP EN RIESGO CRÍTICO
-- ===================================================================
SELECT 
    full_name,
    segment,
    order_frequency,
    total_spent,
    failure_rate_pct,
    risk_level
FROM dw.vw_vip_churn_risk
WHERE risk_level = 'CRITICAL'
LIMIT 5;

-- ===================================================================
-- DETALLE: PARETO - PRODUCTOS QUE CAUSAN 80% DEL PROBLEMA
-- ===================================================================
SELECT 
    product_name,
    category_name,
    late_orders,
    late_rate_pct,
    contribution_pct,
    cumulative_pareto_pct
FROM dw.vw_pareto_delays
WHERE cumulative_pareto_pct <= 80
ORDER BY late_orders DESC
LIMIT 20;

-- ===================================================================
-- DETALLE: MERCADOS PROBLEMÁTICOS
-- ===================================================================
SELECT * FROM dw.vw_market_diagnostics;

-- ===================================================================
-- DETALLE: TENDENCIAS TEMPORALES
-- ===================================================================
SELECT * FROM dw.vw_temporal_trends LIMIT 12;
