-- =====================================================================
-- 02_data_cleaning.sql  |  Retail Sales Analytics
-- Issues found in raw data and how they are fixed:
--   1. 40 duplicate order rows                -> ROW_NUMBER() de-duplication
--   2. Region typos: 'west', ' West '         -> TRIM + case normalisation
--   3. 35 NULL discounts in order_items       -> COALESCE to 0 (documented assumption)
-- =====================================================================

-- Data-quality audit (run BEFORE cleaning; results are logged by the pipeline)
-- name: dq_audit
SELECT 'duplicate_orders' AS issue,
       COUNT(*) - COUNT(DISTINCT order_id) AS rows_affected
FROM stg_orders
UNION ALL
SELECT 'messy_region_text',
       COUNT(*) FROM stg_customers
WHERE region <> TRIM(region) OR region <> UPPER(SUBSTR(TRIM(region),1,1)) || LOWER(SUBSTR(TRIM(region),2))
UNION ALL
SELECT 'null_discount', COUNT(*) FROM stg_order_items WHERE discount IS NULL;

-- Customers: standardise region text
INSERT INTO dim_customer
SELECT customer_id,
       customer_name,
       segment,
       UPPER(SUBSTR(TRIM(region), 1, 1)) || LOWER(SUBSTR(TRIM(region), 2)) AS region,
       TRIM(city),
       signup_date
FROM stg_customers;

INSERT INTO dim_product
SELECT product_id, product_name, category, sub_category, unit_cost, unit_price
FROM stg_products;

-- Orders: keep exactly one row per order_id
INSERT INTO fact_orders
SELECT order_id, order_date, customer_id, ship_mode
FROM (
    SELECT o.*,
           ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_date) AS rn
    FROM stg_orders o
)
WHERE rn = 1;

-- Sales lines: derive revenue / cost / profit once, here, so every report agrees
INSERT INTO fact_sales
SELECT oi.order_item_id,
       oi.order_id,
       oi.product_id,
       oi.quantity,
       COALESCE(oi.discount, 0)                                            AS discount,
       ROUND(oi.quantity * p.unit_price * (1 - COALESCE(oi.discount, 0)), 2) AS revenue,
       ROUND(oi.quantity * p.unit_cost, 2)                                 AS cost,
       ROUND(oi.quantity * p.unit_price * (1 - COALESCE(oi.discount, 0))
             - oi.quantity * p.unit_cost, 2)                               AS profit
FROM stg_order_items oi
JOIN dim_product p ON p.product_id = oi.product_id;

-- Reporting view = one wide, Power BI-friendly table
DROP VIEW IF EXISTS vw_sales_report;
CREATE VIEW vw_sales_report AS
SELECT s.order_item_id,
       s.order_id,
       o.order_date,
       CAST(strftime('%Y', o.order_date) AS INTEGER) AS order_year,
       strftime('%Y-%m', o.order_date)               AS order_month,
       o.ship_mode,
       c.customer_id, c.segment, c.region, c.city,
       p.product_id, p.product_name, p.category, p.sub_category,
       s.quantity, s.discount, s.revenue, s.cost, s.profit
FROM fact_sales s
JOIN fact_orders o   ON o.order_id    = s.order_id
JOIN dim_customer c  ON c.customer_id = o.customer_id
JOIN dim_product p   ON p.product_id  = s.product_id;
