# Power BI build guide - Telecom Churn Dashboard (about 90 minutes)

> `.pbix` files can only be created in Power BI Desktop (free, Windows). Data, measures and theme are all here.
> Save the finished file as `Telecom_Churn_Dashboard.pbix` in this folder and add 3 screenshots to `/images`.

## 1. Load: `data/customer_360.csv`, `data/churn_scores.csv`, `data/tickets.csv`
Types: `churned` Whole number, `churn_probability` Percentage, `created_date` Date. Apply `theme.json`.

## 2. Model
`customer_360[customer_id]` 1:1 `churn_scores[customer_id]` (set cross-filter to Both) | `tickets[customer_id]` many:1 `customer_360[customer_id]`.

## 3. Measures: paste from `dax_measures.md`. Create the three What-if parameters, then add slicers for them.

## 4. Pages
**Page 1 - Churn Overview ("How big is the problem?")**
KPI cards: Churn Rate, Churned Customers, Monthly Revenue Lost, Annualised Revenue Lost.
Bars: churn rate by contract, internet_service, payment_method (same axis scale 0-50%).
Line: churn rate by tenure_months (add a trend line). Slicers: contract, internet_service, senior_citizen.

**Page 2 - Why do they leave? ("What drives churn?")**
Decomposition tree: analyse [Churn Rate] explained by contract, internet_service, tenure_band, tech_support, payment_method
(this is a natural fit for Power BI and a great demo moment). Key influencers visual on `churned` = 1.
Matrix: internet_service x tech_support with [Churn Rate] colour scale.
Ticket chart: ticket_count bucket vs churn rate; card: Avg Satisfaction (churned vs retained).

**Page 3 - Who do we call first? ("Action list")**
Cards: High-Risk Active Customers, Expected Monthly Revenue at Risk.
Table: active customers sorted by churn_probability (customer_id, contract, tenure, monthly_charges, probability with data bars)
- filter `risk_tier` = High and `churned` = 0; enable "Export data" for the retention team.
Gauge or card: Campaign Net Benefit (High tier) driven by the What-if slicers (save rate, take-up, discount).

## 5. Polish checklist
- [ ] Insight titles ("Month-to-month contracts churn 18x more than two-year contracts").
- [ ] Red only for churn / problem, blue for neutral. Same colour for the same category on every page.
- [ ] Bookmarks: "All customers" vs "High-risk only". Drill-through from a segment to the customer table.
- [ ] Phone layout, alt text, performance analyzer check.

## 6. Publish: Publish to Power BI service; use "Publish to web" only because the data is synthetic.
