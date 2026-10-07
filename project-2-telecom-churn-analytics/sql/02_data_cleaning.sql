-- =====================================================================
-- 02_data_cleaning.sql  |  Telecom Churn Analytics
--   1. 25 duplicate customer rows            -> ROW_NUMBER() de-duplication
--   2. Blank total_charges (brand-new, tenure = 0 customers) -> set to 0
--   3. churn 'Yes'/'No' text                 -> 1/0 flag for modelling
-- =====================================================================

-- name: dq_audit
SELECT 'duplicate_customer_rows' AS issue, COUNT(*) - COUNT(DISTINCT customer_id) AS rows_affected FROM stg_customers
UNION ALL
SELECT 'blank_total_charges', COUNT(*) FROM stg_customers WHERE total_charges IS NULL
UNION ALL
SELECT 'orphan_tickets', COUNT(*) FROM stg_support_tickets t
WHERE NOT EXISTS (SELECT 1 FROM stg_customers c WHERE c.customer_id = t.customer_id);

INSERT INTO customers
SELECT customer_id, gender, senior_citizen, partner, dependents, tenure_months, phone_service,
       internet_service, online_security, tech_support, streaming_tv, contract, paperless_billing,
       payment_method, monthly_charges,
       COALESCE(total_charges, 0)                       AS total_charges,
       CASE churn WHEN 'Yes' THEN 1 ELSE 0 END          AS churned
FROM (
    SELECT s.*, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY customer_id) AS rn
    FROM stg_customers s
)
WHERE rn = 1;

INSERT INTO tickets
SELECT ticket_id, customer_id, created_date, category, resolution_hours, satisfaction_score
FROM stg_support_tickets;

-- Customer-360 view: one row per customer with engineered features (used by Python, Excel and Power BI)
DROP VIEW IF EXISTS vw_customer_360;
CREATE VIEW vw_customer_360 AS
SELECT c.*,
       CASE WHEN tenure_months <= 12 THEN '0-12 months'
            WHEN tenure_months <= 24 THEN '13-24 months'
            WHEN tenure_months <= 48 THEN '25-48 months'
            ELSE '49+ months' END                                AS tenure_band,
       CASE WHEN monthly_charges < 40 THEN 'Low (<40)'
            WHEN monthly_charges < 80 THEN 'Medium (40-79)'
            ELSE 'High (80+)' END                                AS charge_band,
       COALESCE(t.ticket_count, 0)                               AS ticket_count,
       t.avg_resolution_hours,
       t.avg_satisfaction
FROM customers c
LEFT JOIN (
    SELECT customer_id, COUNT(*) AS ticket_count,
           ROUND(AVG(resolution_hours), 1) AS avg_resolution_hours,
           ROUND(AVG(satisfaction_score), 2) AS avg_satisfaction
    FROM tickets GROUP BY customer_id
) t ON t.customer_id = c.customer_id;
