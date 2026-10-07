-- =====================================================================
-- 01_schema.sql  |  Retail Sales Analytics
-- Staging tables (raw, untouched CSV loads) + clean star-schema tables
-- Dialect: SQLite (notes for MySQL/PostgreSQL in the project README)
-- =====================================================================

-- Staging tables are created by pandas.to_sql() in python/run_pipeline.py
-- so they mirror the raw CSVs exactly (no constraints, no cleaning).

DROP TABLE IF EXISTS dim_customer;
CREATE TABLE dim_customer (
    customer_id   TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment       TEXT NOT NULL,
    region        TEXT NOT NULL,
    city          TEXT NOT NULL,
    signup_date   DATE
);

DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product (
    product_id   TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category     TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    unit_cost    REAL NOT NULL CHECK (unit_cost >= 0),
    unit_price   REAL NOT NULL CHECK (unit_price >= 0)
);

DROP TABLE IF EXISTS fact_orders;
CREATE TABLE fact_orders (
    order_id    TEXT PRIMARY KEY,
    order_date  DATE NOT NULL,
    customer_id TEXT NOT NULL REFERENCES dim_customer(customer_id),
    ship_mode   TEXT NOT NULL
);

DROP TABLE IF EXISTS fact_sales;
CREATE TABLE fact_sales (
    order_item_id INTEGER PRIMARY KEY,
    order_id      TEXT NOT NULL REFERENCES fact_orders(order_id),
    product_id    TEXT NOT NULL REFERENCES dim_product(product_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    discount      REAL NOT NULL CHECK (discount BETWEEN 0 AND 1),
    revenue       REAL NOT NULL,   -- qty * unit_price * (1 - discount)
    cost          REAL NOT NULL,   -- qty * unit_cost
    profit        REAL NOT NULL    -- revenue - cost
);

CREATE INDEX idx_orders_date     ON fact_orders(order_date);
CREATE INDEX idx_orders_customer ON fact_orders(customer_id);
CREATE INDEX idx_sales_order     ON fact_sales(order_id);
CREATE INDEX idx_sales_product   ON fact_sales(product_id);
