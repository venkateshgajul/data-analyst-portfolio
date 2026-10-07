# Data Analyst Portfolio

Two end-to-end analytics projects that use the four core data-analyst tools together - **SQL, Python, Excel and Power BI** - and finish with quantified business recommendations, not just charts.

| # | Project | Business question | Headline result |
|---|---|---|---|
| 1 | [Retail Sales & Profitability Analytics](project-1-retail-sales-analytics) | Why is profit margin only 8% while revenue grows 15% a year? | Discounts above 10% turn sales loss-making; capping them could lift profit by up to ~59% |
| 2 | [Telecom Churn: Drivers, Prediction & Retention ROI](project-2-telecom-churn-analytics) | Who churns, why, and is a retention campaign worth it? | Month-to-month fiber customers in year 1 churn at 70%; model (AUC 0.87) finds 54% of churners in the top 20%; campaign breaks even at an 8.7% save rate |

## Skills demonstrated
| Skill | Where to look |
|---|---|
| **SQL** - schema design, de-duplication, CTEs, window functions (`LAG`, `RANK`, `NTILE`, running totals), cohort and RFM analysis, views | `*/sql/` |
| **Python** - pandas, hypothesis tests with effect sizes, logistic regression, cross-validation, forecasting with hold-out, matplotlib | `*/python/` |
| **Excel** - SUMIFS/COUNTIFS models, scenario & sensitivity analysis, conditional formatting, charts, Pivot Table guide | `*/excel/` |
| **Power BI** - star schema, DAX (time intelligence, What-if parameters), theming, storytelling dashboards | `*/powerbi/` |
| **Analyst habits** - data-quality audit, documented assumptions, reproducible pipeline, stated limitations | every README |

## Run everything
```bash
pip install -r requirements.txt
cd project-1-retail-sales-analytics && python python/run_pipeline.py && python python/analysis.py && python python/build_excel.py
cd ../project-2-telecom-churn-analytics && python python/run_pipeline.py && python python/analysis.py && python python/build_excel.py
```
All data is **synthetic and seeded**, so results are reproducible and no private data is exposed.

## Contact
**Venkatesh Gajul** - Pune - [LinkedIn](www.linkedin.com/in/venkateshgajul) - venkateshgajul783@gmail.com
