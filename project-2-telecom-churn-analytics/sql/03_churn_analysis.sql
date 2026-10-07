-- =====================================================================
-- 03_churn_analysis.sql  |  Telecom Churn Analytics
-- Business questions answered with CTEs, window functions, conditional aggregation.
-- =====================================================================

-- name: q01_churn_overview
SELECT COUNT(*)                                              AS customers,
       SUM(churned)                                          AS churned_customers,
       ROUND(100.0 * AVG(churned), 1)                        AS churn_rate_pct,
       ROUND(SUM(CASE WHEN churned = 1 THEN monthly_charges END), 0) AS monthly_revenue_lost,
       ROUND(SUM(CASE WHEN churned = 0 THEN monthly_charges END), 0) AS monthly_revenue_retained
FROM vw_customer_360;

-- name: q02_churn_by_contract
SELECT contract,
       COUNT(*)                                       AS customers,
       ROUND(100.0 * AVG(churned), 1)                 AS churn_rate_pct,
       ROUND(100.0 * AVG(churned) / (SELECT AVG(churned) FROM customers), 2) AS churn_index_vs_avg,
       ROUND(AVG(monthly_charges), 1)                 AS avg_monthly_charges,
       ROUND(AVG(tenure_months), 1)                   AS avg_tenure
FROM vw_customer_360 GROUP BY contract ORDER BY churn_rate_pct DESC;

-- name: q03_churn_by_tenure_band
SELECT tenure_band, COUNT(*) AS customers, SUM(churned) AS churned_customers,
       ROUND(100.0 * AVG(churned), 1) AS churn_rate_pct,
       ROUND(100.0 * SUM(SUM(churned)) OVER (ORDER BY MIN(tenure_months)) / SUM(SUM(churned)) OVER (), 1) AS cumulative_share_of_all_churn_pct
FROM vw_customer_360 GROUP BY tenure_band ORDER BY MIN(tenure_months);

-- name: q04_internet_x_techsupport
SELECT internet_service, tech_support,
       COUNT(*) AS customers,
       ROUND(100.0 * AVG(churned), 1) AS churn_rate_pct
FROM vw_customer_360
GROUP BY internet_service, tech_support
ORDER BY internet_service, churn_rate_pct DESC;

-- name: q05_churn_by_payment_method
SELECT payment_method, COUNT(*) AS customers, ROUND(100.0 * AVG(churned), 1) AS churn_rate_pct,
       RANK() OVER (ORDER BY AVG(churned) DESC) AS churn_rank
FROM vw_customer_360 GROUP BY payment_method;

-- name: q06_ticket_impact
SELECT CASE WHEN ticket_count = 0 THEN '0 tickets'
            WHEN ticket_count = 1 THEN '1 ticket'
            WHEN ticket_count = 2 THEN '2 tickets'
            ELSE '3+ tickets' END AS ticket_bucket,
       COUNT(*) AS customers,
       ROUND(100.0 * AVG(churned), 1) AS churn_rate_pct,
       ROUND(AVG(avg_satisfaction), 2) AS avg_satisfaction
FROM vw_customer_360 GROUP BY ticket_bucket ORDER BY MIN(ticket_count);

-- name: q07_satisfaction_vs_churn
SELECT c.churned,
       COUNT(*) AS tickets,
       ROUND(AVG(t.satisfaction_score), 2) AS avg_satisfaction,
       ROUND(AVG(t.resolution_hours), 1)   AS avg_resolution_hours
FROM tickets t JOIN customers c USING (customer_id)
GROUP BY c.churned;

-- name: q08_high_risk_segments
WITH seg AS (
    SELECT contract, internet_service, tenure_band,
           COUNT(*) AS customers,
           SUM(churned) AS churned_customers,
           ROUND(100.0 * AVG(churned), 1) AS churn_rate_pct,
           ROUND(SUM(CASE WHEN churned = 1 THEN monthly_charges END), 0) AS monthly_revenue_lost
    FROM vw_customer_360
    GROUP BY contract, internet_service, tenure_band
    HAVING COUNT(*) >= 40                      -- ignore tiny segments (noise)
)
SELECT *, RANK() OVER (ORDER BY churn_rate_pct DESC) AS risk_rank
FROM seg ORDER BY risk_rank LIMIT 10;

-- name: q09_rule_based_risk_flag
-- Simple, explainable rule BEFORE any ML: how many ACTIVE customers match the worst profile?
WITH flagged AS (
    SELECT *, CASE WHEN contract = 'Month-to-month' AND internet_service = 'Fiber optic'
                    AND tenure_months <= 12 AND tech_support <> 'Yes' THEN 1 ELSE 0 END AS high_risk_flag
    FROM vw_customer_360
)
SELECT high_risk_flag,
       COUNT(*) AS customers,
       ROUND(100.0 * AVG(churned), 1) AS churn_rate_pct,
       SUM(CASE WHEN churned = 0 THEN 1 END) AS still_active,
       ROUND(SUM(CASE WHEN churned = 0 THEN monthly_charges END), 0) AS active_monthly_revenue
FROM flagged GROUP BY high_risk_flag;

-- name: q10_lifetime_value_by_contract
SELECT contract,
       ROUND(AVG(total_charges), 0)                       AS avg_revenue_to_date,
       ROUND(AVG(CASE WHEN churned = 1 THEN total_charges END), 0) AS avg_revenue_churned,
       ROUND(AVG(CASE WHEN churned = 0 THEN total_charges END), 0) AS avg_revenue_retained
FROM vw_customer_360 GROUP BY contract;

-- name: q11_early_life_churn
-- Do customers leave in the first year? (survival-style view using window functions)
SELECT tenure_months,
       COUNT(*) AS customers,
       SUM(churned) AS churned_customers,
       ROUND(100.0 * SUM(SUM(churned)) OVER (ORDER BY tenure_months) / SUM(SUM(churned)) OVER (), 1) AS cum_pct_of_all_churn
FROM vw_customer_360 WHERE tenure_months <= 24
GROUP BY tenure_months ORDER BY tenure_months;
