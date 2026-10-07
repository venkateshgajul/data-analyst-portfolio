"""
Step 1 of the pipeline: raw CSV -> SQLite staging -> clean tables -> analysis query results.
Run:  python python/run_pipeline.py
Outputs: data/retail.db, data/processed/*.csv, powerbi/data/*.csv
"""
import sqlite3, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, PROC, SQLDIR, PBI = ROOT / "data/raw", ROOT / "data/processed", ROOT / "sql", ROOT / "powerbi/data"
for d in (PROC, PBI):
    d.mkdir(parents=True, exist_ok=True)
DB = ROOT / "data/retail.db"


def run_sql_file(con, path, export=True):
    """Execute a .sql file statement by statement. A '-- name: x' comment before a
    SELECT/WITH statement exports its result to data/processed/x.csv"""
    name, buf = None, []
    for line in path.read_text().splitlines():
        if line.strip().lower().startswith("-- name:"):
            name = line.split(":", 1)[1].strip()
            continue
        buf.append(line)
        stmt = "\n".join(buf)
        if sqlite3.complete_statement(stmt) and stmt.strip():
            body = "\n".join(l for l in buf if not l.strip().startswith("--")).strip()
            if body and name and body.split()[0].upper() in ("SELECT", "WITH"):
                df = pd.read_sql_query(body, con)
                if export:
                    df.to_csv(PROC / f"{name}.csv", index=False)
                print(f"  [{path.name}] {name:34s} -> {len(df):>5} rows")
                if name == "dq_audit":
                    print(df.to_string(index=False))
            elif body:
                con.execute(body)
            buf, name = [], None
    con.commit()


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    print("1) Loading raw CSVs into staging tables")
    for t in ("customers", "products", "orders", "order_items"):
        pd.read_csv(RAW / f"{t}.csv").to_sql(f"stg_{t}", con, index=False)
    print("2) Creating schema");            run_sql_file(con, SQLDIR / "01_schema.sql")
    print("3) Cleaning + building tables"); run_sql_file(con, SQLDIR / "02_data_cleaning.sql")
    print("4) Running business analysis");  run_sql_file(con, SQLDIR / "03_business_analysis.sql")

    print("5) Exporting star schema for Power BI")
    pd.read_sql_query("SELECT * FROM dim_customer", con).to_csv(PBI / "dim_customer.csv", index=False)
    pd.read_sql_query("SELECT * FROM dim_product", con).to_csv(PBI / "dim_product.csv", index=False)
    fact = pd.read_sql_query("SELECT * FROM vw_sales_report", con)
    fact.to_csv(PBI / "fact_sales_report.csv", index=False)
    dates = pd.DataFrame({"date": pd.date_range(fact.order_date.min(), fact.order_date.max())})
    dates["year"], dates["quarter"] = dates.date.dt.year, "Q" + dates.date.dt.quarter.astype(str)
    dates["month_num"], dates["month_name"] = dates.date.dt.month, dates.date.dt.strftime("%b")
    dates["year_month"], dates["weekday"] = dates.date.dt.strftime("%Y-%m"), dates.date.dt.day_name()
    dates["date"] = dates.date.dt.strftime("%Y-%m-%d")
    dates.to_csv(PBI / "dim_date.csv", index=False)
    pd.read_csv(PROC / "q08_customer_rfm.csv").to_csv(PBI / "customer_rfm.csv", index=False)
    con.close()
    print("Done.")


if __name__ == "__main__":
    sys.exit(main())
