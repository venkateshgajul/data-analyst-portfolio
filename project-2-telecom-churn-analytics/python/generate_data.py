"""
Generates a reproducible SYNTHETIC telecom customer dataset (6,000 customers) + support tickets.
Churn is drawn from a hidden logistic process (contract, tenure, internet type, add-ons, payment
method, tickets) so that analysis can recover realistic, explainable drivers.
Raw data has deliberate quality issues: duplicate customer rows, blank total_charges for new customers.
Run: python python/generate_data.py
"""
from pathlib import Path
import numpy as np, pandas as pd

rng = np.random.default_rng(7)
OUT = Path(__file__).resolve().parents[1] / "data/raw"; OUT.mkdir(parents=True, exist_ok=True)
N = 6000
sig = lambda x: 1 / (1 + np.exp(-x))

contract = rng.choice(["Month-to-month", "One year", "Two year"], N, p=[.55, .21, .24])
tenure = np.where(contract == "Month-to-month", rng.gamma(1.6, 12, N),
         np.where(contract == "One year", rng.gamma(3.0, 12, N), rng.gamma(4.0, 13, N)))
tenure = np.clip(tenure.round(), 0, 72).astype(int)
internet = rng.choice(["Fiber optic", "DSL", "No internet"], N, p=[.42, .35, .23])
base = {"Fiber optic": 85, "DSL": 58, "No internet": 22}
monthly = np.array([base[i] for i in internet]) + rng.normal(0, 7, N)
phone = np.where(internet == "No internet", "Yes", rng.choice(["Yes", "No"], N, p=[.9, .1]))
def addon(p):  # only available with internet
    return np.where(internet == "No internet", "No internet service", rng.choice(["Yes", "No"], N, p=[p, 1 - p]))
security, support, streaming = addon(.30), addon(.30), addon(.45)
monthly = monthly + (security == "Yes") * 5 + (support == "Yes") * 5 + (streaming == "Yes") * 9
monthly = monthly.clip(18, 125).round(2)
payment = rng.choice(["Electronic check", "Mailed check", "Bank transfer", "Credit card"], N, p=[.34, .19, .22, .25])
paperless = rng.choice(["Yes", "No"], N, p=[.6, .4])
senior = rng.choice([0, 1], N, p=[.84, .16])
partner = rng.choice(["Yes", "No"], N, p=[.48, .52])
dependents = rng.choice(["Yes", "No"], N, p=[.30, .70])
gender = rng.choice(["Male", "Female"], N)
n_tickets = rng.poisson(np.where(internet == "Fiber optic", 1.6, 0.9) * np.where(support == "Yes", .6, 1.0) + .1)

z = (-1.75
     + np.select([contract == "Month-to-month", contract == "One year"], [1.25, -0.2], -1.4)
     - 0.035 * tenure
     + np.select([internet == "Fiber optic", internet == "DSL"], [0.65, 0.0], -0.7)
     - 0.55 * (security == "Yes") - 0.65 * (support == "Yes")
     + 0.55 * (payment == "Electronic check")
     + 0.25 * (paperless == "Yes") + 0.30 * senior
     + 0.018 * (monthly - 65)
     + 0.22 * n_tickets)
churn = rng.random(N) < sig(z)

cust = pd.DataFrame({
    "customer_id": [f"TC-{i:05d}" for i in range(1, N + 1)], "gender": gender, "senior_citizen": senior,
    "partner": partner, "dependents": dependents, "tenure_months": tenure, "phone_service": phone,
    "internet_service": internet, "online_security": security, "tech_support": support, "streaming_tv": streaming,
    "contract": contract, "paperless_billing": paperless, "payment_method": payment,
    "monthly_charges": monthly, "total_charges": (monthly * tenure * rng.uniform(.97, 1.03, N)).round(2),
    "churn": np.where(churn, "Yes", "No"),
})
# --- ticket table ---
rows, tid = [], 1
for cid, k, ch in zip(cust.customer_id, n_tickets, churn):
    for _ in range(k):
        rows.append((f"T{tid:06d}", cid, (pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(rng.integers(0, 365)))).strftime("%Y-%m-%d"),
                     rng.choice(["Billing", "Network outage", "Slow speed", "Plan change", "Device"], p=[.25, .25, .25, .15, .10]),
                     round(float(rng.gamma(2, 9)), 1), int(np.clip(round(rng.normal(2.6 if ch else 3.6, 1.1)), 1, 5))))
        tid += 1
tickets = pd.DataFrame(rows, columns=["ticket_id", "customer_id", "created_date", "category", "resolution_hours", "satisfaction_score"])
# --- dirt ---
new = cust.index[cust.tenure_months == 0]
cust.loc[new, "total_charges"] = np.nan                                  # blank total for brand-new customers
cust = pd.concat([cust, cust.sample(25, random_state=5)]).reset_index(drop=True)  # 25 duplicate rows
cust.to_csv(OUT / "customers.csv", index=False); tickets.to_csv(OUT / "support_tickets.csv", index=False)
print(len(cust), "customer rows |", len(tickets), "tickets | churn rate", round(churn.mean(), 3), "| blank totals", len(new))
