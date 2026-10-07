"""
Step 2: statistical analysis, forecasting and charts (pandas / numpy / scipy / sklearn / matplotlib).
Run AFTER run_pipeline.py:   python python/analysis.py
Outputs: images/*.png, data/processed/forecast.csv, data/processed/insights.txt
"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression

ROOT = Path(__file__).resolve().parents[1]
P, IMG = ROOT / "data/processed", ROOT / "images"
IMG.mkdir(exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 13, "axes.titleweight": "bold", "font.family": "DejaVu Sans"})
BLUE, ORANGE, RED, GREY = "#1f4e79", "#e07b39", "#c0392b", "#9aa5b1"
fact = pd.read_csv(ROOT / "powerbi/data/fact_sales_report.csv", parse_dates=["order_date"])
notes = []

# ---- 1. Monthly trend + seasonal-naive-with-trend forecast (validated on a hold-out) ----------
m = fact.groupby("order_month", as_index=False)["revenue"].sum()
m["t"] = np.arange(len(m))
m["month"] = m.order_month.str[-2:].astype(int)


def fit_forecast(train, horizon_t, horizon_month):
    lr = LinearRegression().fit(train[["t"]], train.revenue)
    detr = train.revenue / lr.predict(train[["t"]])
    seas = detr.groupby(train.month).mean()
    return lr.predict(pd.DataFrame({"t": list(horizon_t)})) * seas.reindex(horizon_month).values


train, test = m.iloc[:-6], m.iloc[-6:]
pred = fit_forecast(train, test.t, test.month)
mape = float(np.mean(np.abs(pred - test.revenue.values) / test.revenue.values) * 100)
future_t = list(range(len(m), len(m) + 3))
future_m = [1, 2, 3]
fc = fit_forecast(m, future_t, future_m)
fc_df = pd.DataFrame({"month": ["2025-01", "2025-02", "2025-03"], "forecast_revenue": fc.round(0)})
fc_df.to_csv(P / "forecast.csv", index=False)
notes.append(f"Forecast hold-out MAPE (last 6 months): {mape:.1f}%")
notes.append("Forecast Q1-2025 revenue: " + ", ".join(f"{r.month}: {r.forecast_revenue/1e6:.1f}M" for r in fc_df.itertuples()))

fig, ax = plt.subplots(figsize=(10, 4.2))
ax.plot(m.order_month, m.revenue / 1e6, color=BLUE, lw=2, label="Actual revenue")
ax.plot(m.order_month, m.revenue.rolling(3).mean() / 1e6, color=GREY, ls="--", label="3-month average")
ax.plot(["2024-12"] + list(fc_df.month), [m.revenue.iloc[-1] / 1e6] + list(fc / 1e6), color=ORANGE, marker="o", label="Forecast")
ax.set_xticks(range(0, len(m) + 3, 3)); ax.set_xticklabels(list(m.order_month[::3]) + ["2025-01"], rotation=45)
ax.set_ylabel("Revenue (₹ million)"); ax.set_title(f"Monthly revenue with Q4 seasonality & 3-month forecast (hold-out MAPE {mape:.1f}%)")
ax.legend(frameon=False); fig.tight_layout(); fig.savefig(IMG / "01_monthly_trend_forecast.png"); plt.close()

# ---- 2. Discount vs profitability (the headline insight) ---------------------------------------
fact["margin"] = fact.profit / fact.revenue
r, pval = stats.spearmanr(fact.discount, fact.margin)
notes.append(f"Spearman correlation discount vs line margin: {r:.2f} (p={pval:.2g})")
d = pd.read_csv(P / "q06_discount_impact.csv")
fig, ax = plt.subplots(figsize=(7.5, 4.2))
bars = ax.bar(d.discount_band, d.margin_pct, color=[BLUE if v > 0 else RED for v in d.margin_pct])
ax.axhline(0, color="black", lw=.8)
for b, v in zip(bars, d.margin_pct):
    ax.text(b.get_x() + b.get_width() / 2, v + (1 if v > 0 else -2.5), f"{v:.1f}%", ha="center", fontweight="bold")
ax.set_ylabel("Profit margin %"); ax.set_title("Discounts above 10% turn profitable sales into losses")
fig.tight_layout(); fig.savefig(IMG / "02_discount_vs_margin.png"); plt.close()
loss_lines = fact[fact.profit < 0]
notes.append(f"Loss-making lines: {len(loss_lines)/len(fact):.1%} of lines, total loss Rs {-loss_lines.profit.sum()/1e6:.1f}M; "
             f"{(loss_lines.discount > .10).mean():.0%} of them carry a >10% discount")
# What-if: cap discounts at 10%
capped = fact.copy()
capped["rev2"] = capped.quantity * (capped.revenue / (1 - capped.discount) / capped.quantity) * (1 - capped.discount.clip(upper=.10))
capped["profit2"] = capped.rev2 - capped.cost
notes.append(f"What-if (cap discount at 10%, same volumes): profit Rs {fact.profit.sum()/1e6:.1f}M -> {capped.profit2.sum()/1e6:.1f}M "
             f"(+{(capped.profit2.sum()/fact.profit.sum()-1)*100:.0f}%)  [assumes no volume loss - upper bound]")

# ---- 3. Category / sub-category margin ----------------------------------------------------------
c = pd.read_csv(P / "q04_category_performance.csv").sort_values("margin_pct")
fig, ax = plt.subplots(figsize=(8, 5))
cols = {"Technology": BLUE, "Furniture": ORANGE, "Office Supplies": GREY}
ax.barh(c.sub_category, c.margin_pct, color=[cols[x] for x in c.category])
for y, (v, rv) in enumerate(zip(c.margin_pct, c.revenue)):
    ax.text(v + .4, y, f"{v:.1f}%  (₹{rv/1e6:.0f}M)", va="center", fontsize=8)
ax.set_xlabel("Profit margin %"); ax.set_title("Margin by sub-category (bar label shows revenue)")
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=v) for v in cols.values()], labels=cols.keys(), frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig(IMG / "03_subcategory_margin.png"); plt.close()

# ---- 4. Regional performance --------------------------------------------------------------------
rg = pd.read_csv(P / "q07_region_city_performance.csv").sort_values("revenue")
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(rg.city, rg.revenue / 1e6, color=BLUE)
for y, v in enumerate(rg.revenue / 1e6):
    ax.text(v + .5, y, f"₹{v:.0f}M", va="center", fontsize=8)
ax.set_xlabel("Revenue (₹ million)"); ax.set_title("Revenue by city")
fig.tight_layout(); fig.savefig(IMG / "04_city_revenue.png"); plt.close()
top = rg.sort_values("revenue", ascending=False).iloc[0]
notes.append(f"Top city: {top.city} = {top.revenue/fact.revenue.sum():.0%} of revenue")

# ---- 5. RFM segments ----------------------------------------------------------------------------
rfm = pd.read_csv(P / "q08_customer_rfm.csv")
seg = rfm.groupby("rfm_segment").agg(customers=("customer_id", "count"), revenue=("monetary", "sum")).sort_values("revenue")
fig, axs = plt.subplots(1, 2, figsize=(10, 4))
axs[0].barh(seg.index, seg.customers, color=BLUE); axs[0].set_title("Customers per RFM segment")
axs[1].barh(seg.index, seg.revenue / 1e6, color=ORANGE); axs[1].set_title("Revenue (₹M) per RFM segment")
axs[1].set_yticklabels([])
fig.tight_layout(); fig.savefig(IMG / "05_rfm_segments.png"); plt.close()
ar = seg.loc["At Risk"]
notes.append(f"RFM 'At Risk' segment: {int(ar.customers)} customers holding Rs {ar.revenue/1e6:.1f}M historical revenue")

# ---- 6. Pareto curve ----------------------------------------------------------------------------
pa = pd.read_csv(P / "q09_pareto_customers.csv")
fig, ax = plt.subplots(figsize=(6.5, 4.2))
ax.plot(pa.customer_percentile, pa.cumulative_revenue_pct, color=BLUE, lw=2.5)
ax.plot([0, 100], [0, 100], color=GREY, ls="--")
v20 = float(pa.loc[pa.customer_percentile == 20, "cumulative_revenue_pct"].iloc[0])
ax.scatter([20], [v20], color=ORANGE, zorder=3); ax.annotate(f"Top 20% of customers\n= {v20:.0f}% of revenue", (20, v20), (32, v20 - 22), arrowprops=dict(arrowstyle="->"))
ax.set_xlabel("Customers ranked by revenue (percentile)"); ax.set_ylabel("Cumulative revenue %"); ax.set_title("Customer revenue concentration")
fig.tight_layout(); fig.savefig(IMG / "06_pareto.png"); plt.close()
notes.append(f"Top 20% of customers generate {v20:.0f}% of revenue (not a strict 80/20 - revenue is broad-based)")

# ---- 7. Cohort retention heat-map ---------------------------------------------------------------
co = pd.read_csv(P / "q10_cohort_retention.csv")
piv = co.pivot(index="cohort_month", columns="month_number", values="retention_pct")
piv = piv[piv.index.str[:4] == "2022"]
fig, ax = plt.subplots(figsize=(9, 4.5))
im = ax.imshow(piv.values, cmap="Blues", aspect="auto", vmin=0, vmax=40)
ax.set_xticks(range(piv.shape[1])); ax.set_xticklabels(piv.columns); ax.set_yticks(range(len(piv))); ax.set_yticklabels(piv.index)
ax.set_xlabel("Months since first order"); ax.set_title("2022 cohorts: % of customers who ordered again (month 0 = 100%)")
fig.colorbar(im, ax=ax, label="Retention %"); fig.tight_layout(); fig.savefig(IMG / "07_cohort_retention.png"); plt.close()

# ---- 8. Seasonality statement -------------------------------------------------------------------
q = fact.assign(q=fact.order_date.dt.quarter).groupby("q").revenue.sum()
notes.append(f"Q4 share of annual revenue: {q.loc[4]/q.sum():.0%}")

(P / "insights.txt").write_text("\n".join(notes))
print("\n".join(notes))
