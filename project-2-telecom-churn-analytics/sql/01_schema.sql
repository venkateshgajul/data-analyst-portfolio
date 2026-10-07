-- =====================================================================
-- 01_schema.sql  |  Telecom Churn Analytics   (dialect: SQLite)
-- stg_* tables are loaded 1:1 from the raw CSVs by python/run_pipeline.py
-- =====================================================================
DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    customer_id       TEXT PRIMARY KEY,
    gender            TEXT,
    senior_citizen    INTEGER CHECK (senior_citizen IN (0,1)),
    partner           TEXT,
    dependents        TEXT,
    tenure_months     INTEGER NOT NULL CHECK (tenure_months >= 0),
    phone_service     TEXT,
    internet_service  TEXT,
    online_security   TEXT,
    tech_support      TEXT,
    streaming_tv      TEXT,
    contract          TEXT NOT NULL,
    paperless_billing TEXT,
    payment_method    TEXT,
    monthly_charges   REAL NOT NULL,
    total_charges     REAL NOT NULL,
    churned           INTEGER NOT NULL CHECK (churned IN (0,1))   -- 1 = left the company
);

DROP TABLE IF EXISTS tickets;
CREATE TABLE tickets (
    ticket_id          TEXT PRIMARY KEY,
    customer_id        TEXT NOT NULL REFERENCES customers(customer_id),
    created_date       DATE,
    category           TEXT,
    resolution_hours   REAL,
    satisfaction_score INTEGER CHECK (satisfaction_score BETWEEN 1 AND 5)
);
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_cust_contract    ON customers(contract);
