"""
Generates a realistic, reproducible synthetic retail dataset (India, INR).
Raw files intentionally contain data-quality issues (duplicates, nulls, messy text)
so the cleaning step in SQL/Python is meaningful.
Run:  python python/generate_data.py
"""
import numpy as np, pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

# ---------- Customers ----------
cities = {
    "West": ["Mumbai", "Pune", "Nashik", "Ahmedabad"],
    "South": ["Bengaluru", "Chennai", "Hyderabad"],
    "North": ["Delhi", "Jaipur"],
    "East": ["Kolkata"],
}
city_rows = [(r, c) for r, cs in cities.items() for c in cs]
city_w = np.array([.24, .12, .08, .07, .12, .08, .08, .09, .05, .07])  # Mumbai..Kolkata (10 cities)
city_w = city_w / city_w.sum()
N_CUST = 1500
idx = rng.choice(len(city_rows), N_CUST, p=city_w)
customers = pd.DataFrame({
    "customer_id": [f"C{str(i).zfill(5)}" for i in range(1, N_CUST + 1)],
    "customer_name": [f"Customer {i}" for i in range(1, N_CUST + 1)],
    "segment": rng.choice(["Consumer", "Corporate", "Home Office"], N_CUST, p=[.52, .30, .18]),
    "region": [city_rows[i][0] for i in idx],
    "city": [city_rows[i][1] for i in idx],
    "signup_date": pd.to_datetime("2021-06-01") + pd.to_timedelta(rng.integers(0, 900, N_CUST), unit="D"),
})
customers["signup_date"] = customers["signup_date"].dt.strftime("%Y-%m-%d")

# ---------- Products ----------
catalog = {
    "Technology": {"Phones": (18000, .22), "Laptops": (55000, .14), "Accessories": (1500, .35), "Printers": (9000, .18)},
    "Furniture": {"Chairs": (6500, .20), "Tables": (12000, .16), "Bookcases": (8000, .12), "Storage": (3500, .22)},
    "Office Supplies": {"Paper": (400, .30), "Binders": (250, .38), "Art": (300, .33), "Appliances": (4500, .25)},
}
prods, pid = [], 1
for cat, subs in catalog.items():
    for sub, (base, margin) in subs.items():
        for k in range(1, 6):
            price = round(base * rng.uniform(.7, 1.4), 0)
            cost = round(price * (1 - margin * rng.uniform(.8, 1.2)), 0)
            prods.append((f"P{str(pid).zfill(4)}", f"{sub} Model {k}", cat, sub, cost, price))
            pid += 1
products = pd.DataFrame(prods, columns=["product_id", "product_name", "category", "sub_category", "unit_cost", "unit_price"])

# ---------- Orders & items (2022-2024, growth + Q4 seasonality) ----------
dates = pd.date_range("2022-01-01", "2024-12-31")
season = dates.month.map({1: .85, 2: .85, 3: .95, 4: .9, 5: .9, 6: .95, 7: .95, 8: 1, 9: 1.05, 10: 1.25, 11: 1.45, 12: 1.35}).values
growth = 1 + (dates - dates[0]).days.values / 1100 * .6
w = season * growth
w = w / w.sum()
N_ORD = 9000
order_dates = rng.choice(dates, N_ORD, p=w)
orders = pd.DataFrame({
    "order_date": pd.to_datetime(order_dates),
    "customer_id": rng.choice(customers["customer_id"], N_ORD),
    "ship_mode": rng.choice(["Standard", "Express", "Same Day"], N_ORD, p=[.62, .28, .10]),
}).sort_values("order_date").reset_index(drop=True)
orders.insert(0, "order_id", [f"O{str(i).zfill(6)}" for i in range(1, N_ORD + 1)])
orders["order_date"] = orders["order_date"].dt.strftime("%Y-%m-%d")

items, iid = [], 1
for oid in orders["order_id"]:
    for _ in range(rng.choice([1, 2, 3, 4], p=[.45, .30, .17, .08])):
        p = products.iloc[rng.integers(len(products))]
        qty = int(rng.choice([1, 2, 3, 4, 5], p=[.5, .25, .13, .08, .04]))
        disc = float(rng.choice([0, .05, .10, .20, .30, .40], p=[.45, .15, .15, .12, .08, .05]))
        items.append((iid, oid, p.product_id, qty, disc))
        iid += 1
order_items = pd.DataFrame(items, columns=["order_item_id", "order_id", "product_id", "quantity", "discount"])

# ---------- Inject realistic dirt ----------
dup = orders.sample(40, random_state=1)
orders = pd.concat([orders, dup]).reset_index(drop=True)                          # 40 duplicate orders
bad = customers.sample(60, random_state=2).index
customers.loc[bad[:30], "region"] = customers.loc[bad[:30], "region"].str.lower()  # 'west'
customers.loc[bad[30:], "region"] = " " + customers.loc[bad[30:], "region"] + " "  # ' West '
order_items.loc[order_items.sample(35, random_state=3).index, "discount"] = np.nan # null discounts

customers.to_csv(OUT / "customers.csv", index=False)
products.to_csv(OUT / "products.csv", index=False)
orders.to_csv(OUT / "orders.csv", index=False)
order_items.to_csv(OUT / "order_items.csv", index=False)
print({k: len(v) for k, v in dict(customers=customers, products=products, orders=orders, order_items=order_items).items()})
