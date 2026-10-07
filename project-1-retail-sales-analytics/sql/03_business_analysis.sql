-- =====================================================================
-- 03_business_analysis.sql  |  Retail Sales Analytics
-- Each block starts with "-- name: <id>" so python/run_pipeline.py can
-- execute it and export the result to data/processed/<id>.csv
-- Concepts used: CTEs, window functions (LAG, RANK, NTILE, SUM OVER),
-- conditional aggregation, self-joins, cohort logic.
-- =====================================================================

-- name: q01_kpi_summary
SELECT ROUND(SUM(revenue), 0)                               AS total_revenue,
       ROUND(SUM(profit), 0)                                AS total_profit,
       ROUND(100.0 * SUM(profit) / SUM(revenue), 2)         AS profit_margin_pct,
       COUNT(DISTINCT order_id)                             AS total_orders,
       COUNT(DISTINCT customer_id)                          AS active_customers,
       ROUND(SUM(revenue) / COUNT(DISTINCT order_id), 0)    AS avg_order_value
FROM vw_sales_report;

-- name: q02_monthly_revenue_mom
WITH monthly AS (
    SELECT order_month, ROUND(SUM(revenue), 0) AS revenue, ROUND(SUM(profit), 0) AS profit
    FROM vw_sales_report
    GROUP BY order_month
)
SELECT order_month,
       revenue,
       profit,
       LAG(revenue) OVER (ORDER BY order_month)                                         AS prev_month_revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY order_month))
             / LAG(revenue) OVER (ORDER BY order_month), 1)                             AS mom_growth_pct,
       SUM(revenue) OVER (ORDER BY order_month)                                         AS running_total_revenue
FROM monthly
ORDER BY order_month;

-- name: q03_yoy_growth
WITH yearly AS (
    SELECT order_year, ROUND(SUM(revenue), 0) AS revenue, ROUND(SUM(profit), 0) AS profit
    FROM vw_sales_report GROUP BY order_year
)
SELECT order_year, revenue, profit,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY order_year))
             / LAG(revenue) OVER (ORDER BY order_year), 1) AS yoy_growth_pct
FROM yearly ORDER BY order_year;

-- name: q04_category_performance
SELECT category, sub_category,
       ROUND(SUM(revenue), 0)                          AS revenue,
       ROUND(SUM(profit), 0)                           AS profit,
       ROUND(100.0 * SUM(profit) / SUM(revenue), 1)    AS margin_pct,
       RANK() OVER (PARTITION BY category ORDER BY SUM(profit) DESC) AS rank_in_category
FROM vw_sales_report
GROUP BY category, sub_category
ORDER BY category, rank_in_category;

-- name: q05_top10_products_by_profit
SELECT product_name, category,
       SUM(quantity)                AS units_sold,
       ROUND(SUM(revenue), 0)       AS revenue,
       ROUND(SUM(profit), 0)        AS profit,
       ROUND(100.0 * SUM(profit) / SUM(revenue), 1) AS margin_pct
FROM vw_sales_report
GROUP BY product_id, product_name, category
ORDER BY profit DESC
LIMIT 10;

-- name: q06_discount_impact
SELECT CASE WHEN discount = 0    THEN '0%  (no discount)'
            WHEN discount <= .10 THEN '1-10%'
            WHEN discount <= .20 THEN '11-20%'
            ELSE                      '21%+' END                     AS discount_band,
       COUNT(*)                                                      AS line_items,
       ROUND(SUM(revenue), 0)                                        AS revenue,
       ROUND(SUM(profit), 0)                                         AS profit,
       ROUND(100.0 * SUM(profit) / SUM(revenue), 1)                  AS margin_pct,
       ROUND(100.0 * SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_loss_making_lines
FROM vw_sales_report
GROUP BY discount_band
ORDER BY MIN(discount);

-- name: q07_region_city_performance
SELECT region, city,
       ROUND(SUM(revenue), 0)                        AS revenue,
       ROUND(SUM(profit), 0)                         AS profit,
       ROUND(100.0 * SUM(profit) / SUM(revenue), 1)  AS margin_pct,
       COUNT(DISTINCT customer_id)                   AS customers,
       RANK() OVER (ORDER BY SUM(revenue) DESC)      AS revenue_rank
FROM vw_sales_report
GROUP BY region, city
ORDER BY revenue_rank;

-- name: q08_customer_rfm
WITH base AS (
    SELECT customer_id,
           CAST(julianday((SELECT MAX(order_date) FROM fact_orders)) - julianday(MAX(order_date)) AS INTEGER) AS recency_days,
           COUNT(DISTINCT order_id) AS frequency,
           ROUND(SUM(revenue), 0)   AS monetary
    FROM vw_sales_report
    GROUP BY customer_id
),
scored AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,   -- 5 = most recent
           NTILE(5) OVER (ORDER BY frequency)         AS f_score,
           NTILE(5) OVER (ORDER BY monetary)          AS m_score
    FROM base
)
SELECT customer_id, recency_days, frequency, monetary, r_score, f_score, m_score,
       CASE WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3                  THEN 'Loyal'
            WHEN r_score >= 4 AND f_score <= 2                  THEN 'New / Promising'
            WHEN r_score <= 2 AND f_score >= 3                  THEN 'At Risk'
            WHEN r_score <= 2 AND f_score <= 2                  THEN 'Lost / Hibernating'
            ELSE 'Needs Attention' END AS rfm_segment
FROM scored
ORDER BY monetary DESC;

-- name: q09_pareto_customers
WITH cust AS (
    SELECT customer_id, SUM(revenue) AS revenue FROM vw_sales_report GROUP BY customer_id
),
ranked AS (
    SELECT customer_id, revenue,
           ROW_NUMBER() OVER (ORDER BY revenue DESC)      AS rnk,
           COUNT(*) OVER ()                               AS n,
           SUM(revenue) OVER (ORDER BY revenue DESC)      AS cum_revenue,
           SUM(revenue) OVER ()                           AS total_revenue
    FROM cust
)
SELECT ROUND(100.0 * rnk / n, 0)                          AS customer_percentile,
       ROUND(100.0 * MAX(cum_revenue) / MAX(total_revenue), 1) AS cumulative_revenue_pct
FROM ranked
GROUP BY ROUND(100.0 * rnk / n, 0)
ORDER BY customer_percentile;

-- name: q10_cohort_retention
WITH first_order AS (
    SELECT customer_id, strftime('%Y-%m', MIN(order_date)) AS cohort_month
    FROM fact_orders GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT o.customer_id, f.cohort_month, strftime('%Y-%m', o.order_date) AS active_month
    FROM fact_orders o JOIN first_order f USING (customer_id)
),
cohort AS (
    SELECT cohort_month,
           (CAST(substr(active_month,1,4) AS INTEGER) - CAST(substr(cohort_month,1,4) AS INTEGER)) * 12
         + (CAST(substr(active_month,6,2) AS INTEGER) - CAST(substr(cohort_month,6,2) AS INTEGER)) AS month_number,
           COUNT(DISTINCT customer_id) AS active_customers
    FROM activity GROUP BY cohort_month, month_number
)
SELECT c.cohort_month, c.month_number, c.active_customers,
       s.active_customers AS cohort_size,
       ROUND(100.0 * c.active_customers / s.active_customers, 1) AS retention_pct
FROM cohort c
JOIN cohort s ON s.cohort_month = c.cohort_month AND s.month_number = 0
WHERE c.month_number BETWEEN 0 AND 12
ORDER BY c.cohort_month, c.month_number;

-- name: q11_ship_mode_analysis
SELECT ship_mode,
       COUNT(DISTINCT order_id)                          AS orders,
       ROUND(SUM(revenue) / COUNT(DISTINCT order_id), 0) AS avg_order_value,
       ROUND(100.0 * SUM(profit) / SUM(revenue), 1)      AS margin_pct
FROM vw_sales_report GROUP BY ship_mode ORDER BY orders DESC;

-- name: q12_segment_performance
SELECT segment,
       COUNT(DISTINCT customer_id)                       AS customers,
       ROUND(SUM(revenue), 0)                            AS revenue,
       ROUND(SUM(revenue) / COUNT(DISTINCT customer_id), 0) AS revenue_per_customer,
       ROUND(100.0 * SUM(profit) / SUM(revenue), 1)      AS margin_pct
FROM vw_sales_report GROUP BY segment ORDER BY revenue DESC;
