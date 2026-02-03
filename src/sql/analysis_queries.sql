-- ============================================================================
-- TORRE CONTROL: CONSOLIDATED ANALYSIS QUERIES
-- Phase 3 - Deep Dive Analytics
-- ============================================================================
-- Purpose: Execute these queries to validate that all analytical views are
-- working correctly and return expected business insights.
--
-- All views are already created in PostgreSQL (dw schema)
-- These queries demonstrate the key business findings.
-- ============================================================================

-- ============================================================================
-- QUERY SET 1: VIP CHURN RISK ANALYSIS (3,658 VIPs at risk)
-- ============================================================================

-- Top 15 VIP Customers by Risk (Highest failure rates)
SELECT 
    full_name,
    segment,
    order_frequency,
    total_spent_usd,
    ROUND(failure_rate_pct::NUMERIC, 2) as failure_rate_pct,
    risk_level
FROM dw.vw_vip_churn_risk
LIMIT 15;

-- Count of VIPs by Risk Level
SELECT 
    risk_level,
    COUNT(*) as customer_count,
    ROUND(AVG(failure_rate_pct::NUMERIC), 2) as avg_failure_rate,
    ROUND(SUM(total_spent_usd::NUMERIC), 2) as total_spent
FROM dw.vw_vip_churn_risk
GROUP BY risk_level
ORDER BY CASE 
    WHEN risk_level = 'CRITICAL' THEN 1
    WHEN risk_level = 'HIGH' THEN 2
    WHEN risk_level = 'MEDIUM' THEN 3
    ELSE 4
END;

-- Total VIP customers at risk
SELECT COUNT(*) as total_vips_at_risk FROM dw.vw_vip_churn_risk;

-- ============================================================================
-- QUERY SET 2: PARETO ANALYSIS (7 Products = 80% of delays)
-- ============================================================================

-- Products causing 80% of all supply chain delays (Pareto Top 20)
SELECT 
    product_name,
    category_name,
    late_orders,
    ROUND(late_rate_pct::NUMERIC, 2) as late_rate_pct,
    ROUND(contribution_pct::NUMERIC, 2) as contribution_pct,
    ROUND(cumulative_pareto_pct::NUMERIC, 2) as cumulative_pct
FROM dw.vw_pareto_delays
WHERE cumulative_pareto_pct <= 80
LIMIT 20;

-- Summary: How many products needed to reach 80%?
WITH pareto_summary AS (
    SELECT 
        COUNT(*) as products_count,
        ROUND(SUM(contribution_pct::NUMERIC), 2) as total_contribution_pct,
        ROUND(SUM(late_orders::NUMERIC), 0) as total_late_orders
    FROM dw.vw_pareto_delays
    WHERE cumulative_pareto_pct <= 80
)
SELECT 
    products_count,
    total_contribution_pct,
    total_late_orders,
    ROUND((total_late_orders / 
        (SELECT SUM(late_orders::NUMERIC) FROM dw.vw_pareto_delays)) * 100, 2) as pct_of_all_delays
FROM pareto_summary;

-- ============================================================================
-- QUERY SET 3: MARKET DIAGNOSTICS (Geographic Performance)
-- ============================================================================

-- Market Performance: Revenue at Risk by Market
SELECT 
    market,
    order_count,
    late_order_count,
    ROUND(late_rate_pct::NUMERIC, 2) as late_rate_pct,
    ROUND(revenue_at_risk::NUMERIC, 2) as revenue_at_risk,
    ROUND((revenue_at_risk::NUMERIC / 
        (SELECT SUM(revenue_at_risk::NUMERIC) FROM dw.vw_market_diagnostics)) * 100, 2) as pct_of_total_risk
FROM dw.vw_market_diagnostics
ORDER BY revenue_at_risk DESC;

-- Uniform late rate across markets (key finding: problem is global, not regional)
SELECT 
    ROUND(AVG(late_rate_pct::NUMERIC), 2) as avg_market_late_rate,
    ROUND(MIN(late_rate_pct::NUMERIC), 2) as min_market_late_rate,
    ROUND(MAX(late_rate_pct::NUMERIC), 2) as max_market_late_rate,
    ROUND(MAX(late_rate_pct::NUMERIC) - MIN(late_rate_pct::NUMERIC), 2) as market_variance
FROM dw.vw_market_diagnostics;

-- ============================================================================
-- QUERY SET 4: TEMPORAL TRENDS (Monthly OTIF Tracking)
-- ============================================================================

-- OTIF Trend by Month
SELECT 
    month_year,
    order_count,
    otif_count,
    ROUND(otif_pct::NUMERIC, 2) as otif_pct,
    late_order_count
FROM dw.vw_temporal_trends
ORDER BY month_year DESC;

-- ============================================================================
-- QUERY SET 5: KEY BUSINESS METRICS (Consolidated KPIs)
-- ============================================================================

-- Global OTIF % (On-Time In-Full)
SELECT 
    'Global OTIF %' as metric,
    ROUND(AVG(otif_pct::NUMERIC), 2) as value
FROM dw.vw_temporal_trends;

-- Total Revenue at Risk
SELECT 
    'Revenue@Risk' as metric,
    ROUND(SUM(revenue_at_risk::NUMERIC), 2) as value
FROM dw.vw_market_diagnostics;

-- Total Late Orders
SELECT 
    'Late Orders' as metric,
    SUM(late_order_count::NUMERIC) as value
FROM dw.vw_market_diagnostics;

-- VIPs at Risk Count
SELECT 
    'VIPs@Risk' as metric,
    COUNT(*) as value
FROM dw.vw_vip_churn_risk;

-- ============================================================================
-- QUERY SET 6: VALIDATION QUERIES (Data Quality Checks)
-- ============================================================================

-- Verify data integrity: Check for NULL values in critical fields
SELECT 
    COUNT(*) as total_rows,
    COUNT(CASE WHEN full_name IS NULL THEN 1 END) as nulls_in_name,
    COUNT(CASE WHEN total_spent_usd IS NULL THEN 1 END) as nulls_in_spent,
    COUNT(CASE WHEN failure_rate_pct IS NULL THEN 1 END) as nulls_in_failure_rate
FROM dw.vw_vip_churn_risk;

-- Verify Pareto distribution
SELECT 
    COUNT(*) as total_products,
    MIN(cumulative_pareto_pct) as min_cumulative,
    MAX(cumulative_pareto_pct) as max_cumulative
FROM dw.vw_pareto_delays;

-- Verify market data completeness
SELECT 
    COUNT(DISTINCT market) as unique_markets,
    SUM(order_count) as total_orders,
    SUM(late_order_count) as total_late_orders
FROM dw.vw_market_diagnostics;

-- ============================================================================
-- QUERY SET 7: EXECUTIVE SUMMARY (One-Liner KPIs)
-- ============================================================================

-- All critical KPIs in one query (for executive dashboard)
SELECT 
    'OTIF %' as kpi_name,
    (SELECT ROUND(AVG(otif_pct::NUMERIC), 2) FROM dw.vw_temporal_trends) as value,
    'Should be 90%+' as benchmark
UNION ALL
SELECT 
    'Revenue@Risk',
    (SELECT ROUND(SUM(revenue_at_risk::NUMERIC) / 1000000, 1) FROM dw.vw_market_diagnostics),
    'Should be <$5M'
UNION ALL
SELECT 
    'VIPs@Risk',
    (SELECT COUNT(*) FROM dw.vw_vip_churn_risk),
    'Should be <500'
UNION ALL
SELECT 
    'Products causing 80%',
    (SELECT COUNT(*) FROM dw.vw_pareto_delays WHERE cumulative_pareto_pct <= 80),
    'Pareto focus'
UNION ALL
SELECT 
    'Late Order Rate',
    (SELECT ROUND(SUM(late_order_count::NUMERIC) / SUM(order_count::NUMERIC) * 100, 2) FROM dw.vw_market_diagnostics),
    'Should be <20%';

-- ============================================================================
-- QUERY SET 8: ROOT CAUSE DRILL-DOWN (Investigation Queries)
-- ============================================================================

-- Which category has most problems?
SELECT 
    category_name,
    COUNT(*) as products_in_category,
    SUM(late_orders) as total_late_orders,
    ROUND(AVG(late_rate_pct::NUMERIC), 2) as avg_late_rate_pct
FROM dw.vw_pareto_delays
GROUP BY category_name
ORDER BY total_late_orders DESC;

-- Which customer segments are most at risk?
SELECT 
    segment,
    COUNT(*) as customer_count,
    ROUND(AVG(failure_rate_pct::NUMERIC), 2) as avg_failure_rate,
    COUNT(CASE WHEN risk_level IN ('CRITICAL', 'HIGH') THEN 1 END) as at_risk_count
FROM dw.vw_vip_churn_risk
GROUP BY segment
ORDER BY at_risk_count DESC;

-- Which market needs most attention (by revenue impact)?
SELECT 
    market,
    order_count,
    late_order_count,
    ROUND(revenue_at_risk::NUMERIC, 0) as revenue_at_risk,
    ROUND(revenue_at_risk::NUMERIC / order_count, 2) as revenue_at_risk_per_order
FROM dw.vw_market_diagnostics
ORDER BY revenue_at_risk DESC;

-- ============================================================================
-- EXECUTION INSTRUCTIONS:
-- ============================================================================
--
-- Option 1: Run all queries in SQL Editor (VS Code SQLTools)
-- - Select all text
-- - Right-click → Execute Query
--
-- Option 2: Run via Docker terminal
-- docker exec supply_chain_db psql -U admin -d supply_chain_dw -f analysis_queries.sql
--
-- Option 3: Run individual query sets
-- Example: Copy QUERY SET 1 and execute in power shell:
-- Get-Content 'analysis_queries.sql' | docker exec -i supply_chain_db psql -U admin -d supply_chain_dw
--
-- ============================================================================
-- EXPECTED RESULTS:
-- ============================================================================
--
-- Query Set 1 (VIP Churn Risk):
--   - Returns 15 VIP customers with highest failure rates
--   - Top customer: Mary Harding with 94.87% failure rate
--   - Total VIPs at risk: 3,658
--
-- Query Set 2 (Pareto Analysis):
--   - Returns 7 products (those with cumulative_pct ≤ 80%)
--   - Perfect Fitness Rip Deck: 14,540 late orders (13.6%)
--   - These 7 products = 74% of ALL delays
--
-- Query Set 3 (Market Diagnostics):
--   - 5 markets: Europe ($6.2M risk), LATAM ($5.8M), Pacific ($4.7M), USCA ($3.5M), Africa ($1.2M)
--   - All markets have ~57% late rate (uniformity proves global problem, not regional)
--
-- Query Set 4 (Temporal Trends):
--   - 1 month available (January 2026)
--   - OTIF: 40.86%
--   - Late orders: 106,927
--
-- Query Set 5 (KPIs):
--   - OTIF %: 40.86%
--   - Revenue@Risk: $21.7M
--   - Late Orders: 106,927
--   - VIPs@Risk: 3,658
--
-- Query Set 6 (Validation):
--   - All NULL counts should be 0
--   - Data quality: 100%
--
-- Query Set 7 (Executive Summary):
--   - All critical metrics in single result set
--   - Ready for dashboard import
--
-- Query Set 8 (Root Cause):
--   - Drill-down by category, segment, market
--   - Identifies specific focus areas
--
-- ============================================================================

-- QUICK COMMAND: Run this to validate everything works
-- SELECT 'OTIF: ' || ROUND(AVG(otif_pct::NUMERIC), 2) || '%' as status
-- FROM dw.vw_temporal_trends;
-- Expected: OTIF: 40.86%

-- ============================================================================
