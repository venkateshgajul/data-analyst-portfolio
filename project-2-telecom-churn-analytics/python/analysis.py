"""
Statistical testing + churn prediction model + customer risk scoring.
Run AFTER run_pipeline.py:   python python/analysis.py
Outputs: images/*.png, data/processed/{churn_scores,stat_tests,odds_ratios}.csv, model_metrics.json, insights.txt, powerbi/data/churn_scores.csv

Design choices worth explaining in an interview
  * Logistic regression is the primary model: interpretable (odds ratios) -> actionable for a retention team.
    A gradient-boosting model is trained as a benchmark to show we are not leaving accuracy on the table.
  * total_charges (= monthly x tenure, multicollinear) and post-hoc ticket satisfaction (only exists AFTER a
    bad experience / possible leakage) are excluded from the model. ticket_count is kept.
  * Threshold chosen on training-set out-of-fold predictions only; test set touched once.
  * Scores for every customer are OUT-OF-FOLD, so nobody is scored by a model that saw their own label.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
P, IMG, PBI = ROOT / "data/processed", ROOT / "images", ROOT / "powerbi/data"
IMG.mkdir(exist_ok=True); PBI.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 12, "axes.titleweight": "bold"})
BLUE, ORANGE, RED, GREY = "#1f4e79", "#e07b39", "#c0392b", "#9aa5b1"
df = pd.read_csv(P / "customer_360.csv")
notes = [f"Customers: {len(df):,} | churn rate {df.churned.mean():.1%} | monthly revenue lost to churn ${df.loc[df.churned==1,'monthly_charges'].sum():,.0f}"]

# ------------------------------------------------------------------ 1. Hypothesis tests
cat_cols = ["contract", "internet_service", "tech_support", "online_security", "payment_method",
            "paperless_billing", "senior_citizen", "partner", "dependents", "gender", "tenure_band"]
rows = []
for c in cat_cols:
    ct = pd.crosstab(df[c], df.churned)
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    v = np.sqrt(chi2 / (ct.values.sum() * (min(ct.shape) - 1)))
    rows.append((c, "chi-square", chi2, p, v))
for c in ["tenure_months", "monthly_charges", "ticket_count"]:
    a, b = df.loc[df.churned == 1, c], df.loc[df.churned == 0, c]
    u, p = stats.mannwhitneyu(a, b)
    rbc = 1 - 2 * u / (len(a) * len(b))          # rank-biserial effect size
    rows.append((c, "mann-whitney", u, p, abs(rbc)))
tests = pd.DataFrame(rows, columns=["feature", "test", "statistic", "p_value", "effect_size"]).sort_values("effect_size", ascending=False)
tests["significant_5pct"] = tests.p_value < .05
tests.round(4).to_csv(P / "stat_tests.csv", index=False)
notes.append("Strongest associations with churn (effect size): " + ", ".join(f"{r.feature} ({r.effect_size:.2f})" for r in tests.head(4).itertuples()))
notes.append("Not significant at 5%: " + (", ".join(tests.loc[~tests.significant_5pct, 'feature']) or "none"))

# ------------------------------------------------------------------ 2. Descriptive charts
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
c = df.groupby("contract").churned.mean().reindex(["Month-to-month", "One year", "Two year"]) * 100
b = ax[0].bar(c.index, c.values, color=[RED, ORANGE, BLUE])
for r, v in zip(b, c.values): ax[0].text(r.get_x() + r.get_width() / 2, v + .8, f"{v:.1f}%", ha="center", fontweight="bold")
ax[0].set_ylabel("Churn rate %"); ax[0].set_title("Contract type is the #1 driver")
t = df.groupby("tenure_months").churned.mean() * 100
ax[1].plot(t.index, t.rolling(5, center=True, min_periods=1).mean(), color=BLUE, lw=2)
ax[1].set_xlabel("Tenure (months)"); ax[1].set_ylabel("Churn rate % (5-month rolling avg)"); ax[1].set_title("Risk is highest in year 1 and decays with tenure")
fig.tight_layout(); fig.savefig(IMG / "01_contract_and_tenure.png"); plt.close()

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
g = df[df.internet_service != "No internet"].groupby(["internet_service", "tech_support"]).churned.mean().unstack() * 100
g.plot.bar(ax=ax[0], color=[GREY, BLUE], rot=0); ax[0].set_ylabel("Churn rate %"); ax[0].legend(title="Tech support", frameon=False)
ax[0].set_title("Fiber customers churn most - tech support helps"); ax[0].set_xlabel("")
pm = (df.groupby("payment_method").churned.mean() * 100).sort_values()
ax[1].barh(pm.index, pm.values, color=[RED if k == "Electronic check" else GREY for k in pm.index])
for y, v in enumerate(pm.values): ax[1].text(v + .3, y, f"{v:.1f}%", va="center")
ax[1].set_xlabel("Churn rate %"); ax[1].set_title("Electronic-check payers churn more")
fig.tight_layout(); fig.savefig(IMG / "02_service_and_payment.png"); plt.close()

# ------------------------------------------------------------------ 3. Model
num = ["tenure_months", "monthly_charges", "ticket_count"]
cat = ["contract", "internet_service", "online_security", "tech_support", "streaming_tv", "payment_method",
       "paperless_billing", "senior_citizen", "partner", "dependents"]
X, y = df[num + cat].copy(), df.churned
X["senior_citizen"] = X.senior_citizen.astype(str)
pre = ColumnTransformer([("num", StandardScaler(), num), ("cat", OneHotEncoder(drop="first"), cat)])
lr = Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=2000))])
gb = Pipeline([("pre", pre), ("clf", HistGradientBoostingClassifier(max_depth=3, learning_rate=.06, max_iter=250, random_state=1))])
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.2, stratify=y, random_state=42)
cv = StratifiedKFold(5, shuffle=True, random_state=42)

oof_tr = cross_val_predict(lr, Xtr, ytr, cv=cv, method="predict_proba")[:, 1]
cv_auc = roc_auc_score(ytr, oof_tr)
grid = np.linspace(.1, .7, 61)
thr = float(grid[np.argmax([f1_score(ytr, oof_tr >= g) for g in grid])])
lr.fit(Xtr, ytr); gb.fit(Xtr, ytr)
pl, pg = lr.predict_proba(Xte)[:, 1], gb.predict_proba(Xte)[:, 1]
met = {
    "logistic": {"test_auc": roc_auc_score(yte, pl), "cv_auc_train": cv_auc, "pr_auc": average_precision_score(yte, pl),
                 "brier": brier_score_loss(yte, pl), "threshold": thr,
                 "precision": precision_score(yte, pl >= thr), "recall": recall_score(yte, pl >= thr), "f1": f1_score(yte, pl >= thr)},
    "gradient_boosting": {"test_auc": roc_auc_score(yte, pg), "pr_auc": average_precision_score(yte, pg), "brier": brier_score_loss(yte, pg)},
    "baseline_churn_rate": float(yte.mean()),
}
met = {k: ({a: round(float(b), 4) for a, b in v.items()} if isinstance(v, dict) else round(v, 4)) for k, v in met.items()}
json.dump(met, open(P / "model_metrics.json", "w"), indent=2)
m = met["logistic"]
notes.append(f"Logistic regression: test ROC-AUC {m['test_auc']:.3f} (5-fold CV on train {m['cv_auc_train']:.3f}) vs gradient boosting {met['gradient_boosting']['test_auc']:.3f}")
notes.append(f"At threshold {m['threshold']:.2f}: precision {m['precision']:.2f}, recall {m['recall']:.2f}, F1 {m['f1']:.2f} (base churn rate {met['baseline_churn_rate']:.2f})")

# odds ratios
names = lr.named_steps["pre"].get_feature_names_out()
coef = lr.named_steps["clf"].coef_[0]
orr = pd.DataFrame({"feature": [n.split("__")[1] for n in names], "odds_ratio": np.exp(coef), "coef": coef})
orr["note"] = np.where(orr.feature.isin(num), "per +1 standard deviation", "vs reference category")
orr.sort_values("odds_ratio", ascending=False).round(3).to_csv(P / "odds_ratios.csv", index=False)
top = pd.concat([orr.nlargest(7, "coef"), orr.nsmallest(7, "coef")]).sort_values("coef")
fig, ax = plt.subplots(figsize=(8, 5.5))
ax.barh(top.feature, top.odds_ratio - 1, left=1, color=[RED if v > 1 else BLUE for v in top.odds_ratio])
ax.axvline(1, color="black", lw=.8); ax.set_xscale("log")
ax.set_xlabel("Odds ratio (log scale)  >1 raises churn risk, <1 lowers it"); ax.set_title("What drives churn? Logistic-regression odds ratios")
fig.tight_layout(); fig.savefig(IMG / "03_odds_ratios.png"); plt.close()
notes.append("Biggest risk-raisers: " + ", ".join(f"{r.feature} (OR {r.odds_ratio:.2f})" for r in orr.nlargest(3, 'coef').itertuples())
             + " | biggest protectors: " + ", ".join(f"{r.feature} (OR {r.odds_ratio:.2f})" for r in orr.nsmallest(3, 'coef').itertuples()))

# ROC + gains
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for p_, lab, col in ((pl, f"Logistic (AUC {m['test_auc']:.3f})", BLUE), (pg, f"Grad. boosting (AUC {met['gradient_boosting']['test_auc']:.3f})", ORANGE)):
    fpr, tpr, _ = roc_curve(yte, p_); ax[0].plot(fpr, tpr, label=lab, color=col, lw=2)
ax[0].plot([0, 1], [0, 1], "--", color=GREY); ax[0].set_xlabel("False positive rate"); ax[0].set_ylabel("True positive rate")
ax[0].set_title("ROC curve (hold-out test set)"); ax[0].legend(frameon=False)
order = np.argsort(-pl); gains = np.cumsum(yte.values[order]) / yte.sum(); x = np.arange(1, len(yte) + 1) / len(yte)
ax[1].plot(x * 100, gains * 100, color=BLUE, lw=2.5); ax[1].plot([0, 100], [0, 100], "--", color=GREY)
g20 = gains[int(.2 * len(yte)) - 1]
ax[1].scatter([20], [g20 * 100], color=ORANGE, zorder=3)
ax[1].annotate(f"Contact top 20% of customers\n-> reach {g20:.0%} of churners", (20, g20 * 100), (30, g20 * 100 - 25), arrowprops=dict(arrowstyle="->"))
ax[1].set_xlabel("% of customers contacted (highest risk first)"); ax[1].set_ylabel("% of churners captured"); ax[1].set_title("Cumulative gains")
fig.tight_layout(); fig.savefig(IMG / "04_roc_and_gains.png"); plt.close()
notes.append(f"Gains: contacting the top 20% riskiest customers captures {g20:.0%} of churners (random targeting would capture 20%) -> lift {g20/.2:.1f}x")

cm = confusion_matrix(yte, pl >= thr)
fig, ax = plt.subplots(figsize=(4.6, 4))
ax.imshow(cm, cmap="Blues")
for (i, j), v in np.ndenumerate(cm): ax.text(j, i, f"{v}", ha="center", va="center", fontsize=15, color="white" if v > cm.max() / 2 else "black")
ax.set_xticks([0, 1]); ax.set_xticklabels(["Stays", "Churns"]); ax.set_yticks([0, 1]); ax.set_yticklabels(["Stayed", "Churned"])
ax.set_xlabel("Predicted"); ax.set_ylabel("Actual"); ax.set_title(f"Confusion matrix @ threshold {thr:.2f}")
fig.tight_layout(); fig.savefig(IMG / "05_confusion_matrix.png"); plt.close()

# ------------------------------------------------------------------ 4. Out-of-fold scoring of ALL customers + risk tiers
oof = cross_val_predict(lr, X, y, cv=cv, method="predict_proba")[:, 1]
sc = df[["customer_id", "contract", "internet_service", "tenure_band", "tenure_months", "payment_method", "monthly_charges", "ticket_count", "churned"]].copy()
sc["churn_probability"] = oof.round(4)
q80, q50 = np.quantile(oof, .80), np.quantile(oof, .50)
sc["risk_tier"] = np.where(oof >= q80, "High", np.where(oof >= q50, "Medium", "Low"))
sc.to_csv(P / "churn_scores.csv", index=False); sc.to_csv(PBI / "churn_scores.csv", index=False)
df.to_csv(PBI / "customer_360.csv", index=False)
tier = sc.groupby("risk_tier").agg(customers=("customer_id", "count"), actual_churn_rate=("churned", "mean"), avg_prob=("churn_probability", "mean"),
                                   monthly_revenue=("monthly_charges", "sum")).reindex(["High", "Medium", "Low"])
notes.append("Risk tiers (actual churn rate): " + ", ".join(f"{k} {v:.0%}" for k, v in tier.actual_churn_rate.items()))
fig, ax = plt.subplots(figsize=(6.5, 4))
b = ax.bar(tier.index, tier.actual_churn_rate * 100, color=[RED, ORANGE, BLUE])
for r, v in zip(b, tier.actual_churn_rate * 100): ax.text(r.get_x() + r.get_width() / 2, v + 1, f"{v:.0f}%", ha="center", fontweight="bold")
ax.set_ylabel("Actual churn rate %"); ax.set_title("Model risk tiers separate churners cleanly (out-of-fold)")
fig.tight_layout(); fig.savefig(IMG / "06_risk_tiers.png"); plt.close()

active = sc[sc.churned == 0]
exp_loss = (active.churn_probability * active.monthly_charges).sum()
notes.append(f"Active customers: {len(active):,}; High-tier active customers: {(active.risk_tier=='High').sum():,} holding ${active.loc[active.risk_tier=='High','monthly_charges'].sum():,.0f}/month")
(P / "insights.txt").write_text("\n".join(notes)); print("\n".join(notes))
