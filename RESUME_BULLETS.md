# Resume kit: how to present these projects

## 1. Be upfront that the data is synthetic
Write "(synthetic dataset)" or "(simulated data)" in the project line. Interviewers respect it, and it protects you when they ask how you got the data - because you can explain exactly how it was generated and why the patterns are realistic. Once you are comfortable, repeat either project on a public real dataset (Kaggle *Superstore* for Project 1, *IBM Telco Customer Churn* for Project 2) - the code, SQL and dashboards transfer directly and you can add "validated on a real public dataset".

## 2. Resume entries (copy, then trim to 3-4 bullets per project)

**Retail Sales & Profitability Analytics** | SQL, Python, Excel, Power BI | github.com/<you>/data-analyst-portfolio *(synthetic dataset)*
- Cleaned and modelled 16.7K sales line items (9K orders) in SQL - removed 40 duplicate orders, standardised 60 inconsistent region values and handled 35 NULL discounts - then built a star-schema reporting view and 12 analytical queries using CTEs and window functions (MoM growth, RFM segmentation, cohort retention).
- Discovered that discounts above 10% pushed margin to -4% and -26% (99% of loss-making lines carried a >10% discount; Spearman rho = -0.67); a Python what-if simulation showed that capping discounts at 10% could lift profit by up to 59% (Rs 24.7M to Rs 39.1M).
- Built a seasonal-trend revenue forecast validated on a 6-month hold-out (MAPE 13.5%) and a formula-driven Excel model (SUMIFS, what-if input cell, conditional formatting, charts).
- Designed a 3-page Power BI dashboard with DAX time-intelligence measures (YoY, YTD, 3-month average) and insight-led titles for executives. *(Include this bullet only after you have built the .pbix.)*

**Telecom Customer Churn Analytics & Retention ROI** | SQL, Python, Excel, Power BI | github.com/<you>/data-analyst-portfolio *(synthetic dataset)*
- Built a customer-360 view in SQL (joins, de-duplication, engineered tenure and ticket features) and segment queries showing month-to-month fiber customers in their first year churn at 70% versus a 24% overall rate.
- Tested churn drivers with chi-square and Mann-Whitney tests (effect sizes reported) and trained a logistic-regression model (ROC-AUC 0.87, 5-fold CV) benchmarked against gradient boosting; avoided leakage by excluding post-event features and scoring customers out-of-fold.
- Model targeting captures 54% of churners by contacting the top 20% of customers (2.7x lift); translated scores into an Excel ROI model with scenarios and sensitivity analysis - targeting the High-risk tier returns 189% ROI and breaks even at an 8.7% save rate.
- Created a Power BI action dashboard with a decomposition tree and What-if parameters so the retention team can adjust campaign assumptions. *(Only after you build it.)*

**Skills line:** SQL (CTEs, window functions, joins, views, data cleaning) | Python (pandas, scikit-learn, scipy, matplotlib) | Excel (SUMIFS, pivot tables, scenario analysis) | Power BI (DAX, data modelling, dashboards) | Statistics (hypothesis testing, regression, forecasting) | Git/GitHub

## 3. What makes these projects different from typical portfolio projects
| Typical project | This portfolio |
|---|---|
| Downloads a clean Kaggle CSV and plots it | Starts with **dirty data**, audits and fixes it in SQL, and documents each assumption |
| Charts with no conclusion | Every page ends in a **quantified recommendation** (Rs / $ impact, ROI, break-even) |
| Accuracy score only | Leakage checks, benchmark model, out-of-fold scoring, lift/gains, threshold choice, business ROI |
| Tools used in isolation | One **pipeline**: SQL -> Python -> Excel -> Power BI, reproducible with 3 commands |
| Titles like "Sales by region" | Insight titles: "Discounts above 10% destroy margin" |
| No limits mentioned | Explicit **limitations and next steps** (shows maturity) |

## 4. 30-second pitch
"I built two end-to-end projects. In the first I found that deep discounts were turning an 8%-margin retail business loss-making and quantified the profit from capping them. In the second I predicted telecom churn, showed that only the top fifth of customers needs contacting to catch half the churners, and modelled the campaign ROI. Both use SQL for cleaning and analysis, Python for statistics, Excel for scenario models and Power BI for the dashboard."

## 5. Interview questions to rehearse (answers are in the code and READMEs)
1. Why `ROW_NUMBER()` instead of `DISTINCT` to remove duplicates? *(keeps a deterministic row; DISTINCT fails if rows differ in any column)*
2. What is the difference between `RANK`, `DENSE_RANK` and `ROW_NUMBER`? Where did you use `NTILE`?
3. How did you handle NULL discounts and what is the risk of that assumption?
4. Why logistic regression over gradient boosting when AUC is similar? *(interpretability, odds ratios, stakeholder trust)*
5. What is data leakage and which columns did you exclude for it?
6. Why out-of-fold predictions for scoring all customers?
7. How do you pick a classification threshold? *(F1 on training folds here; in practice use campaign cost vs benefit)*
8. What does a 54% capture at 20% contacted mean? *(cumulative gains; lift 2.7x)*
9. Explain filter context vs row context in DAX; why a dedicated Date table?
10. Which of your assumptions would you test with an A/B experiment first? *(save rate and discount response)*
11. Why is the discount what-if an *upper bound*? *(assumes no volume loss / ignores price elasticity)*
12. How would you productionise the churn model? *(prediction window, monitoring, retraining, fairness checks)*
