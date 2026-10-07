"""
Step 1 of the pipeline: raw CSV -> SQLite staging -> clean tables -> analysis query results.
Run:  python python/run_pipeline.py
Outputs: data/telecom.db, data/processed/*.csv, powerbi/data/*.csv
"""
import sqlite3, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, PROC, SQLDIR, PBI = ROOT / "data/raw", ROOT / "data/processed", ROOT / "sql", ROOT / "powerbi/data"
for d in (PROC, PBI):
    d.mkdir(parents=True, exist_ok=True)
DB = ROOT / "data/telecom.db"


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
    for t in ("customers", "support_tickets"):
        pd.read_csv(RAW / f"{t}.csv").to_sql(f"stg_{t}", con, index=False)
    print("2) Creating schema");            run_sql_file(con, SQLDIR / "01_schema.sql")
    print("3) Cleaning + building tables"); run_sql_file(con, SQLDIR / "02_data_cleaning.sql")
    print("4) Running churn analysis");     run_sql_file(con, SQLDIR / "03_churn_analysis.sql")
    print("5) Exporting modelling / Power BI tables")
    pd.read_sql_query("SELECT * FROM vw_customer_360", con).to_csv(PROC / "customer_360.csv", index=False)
    pd.read_sql_query("SELECT * FROM tickets", con).to_csv(PBI / "tickets.csv", index=False)
    con.close()
    print("Done.")


if __name__ == "__main__":
    sys.exit(main())
