# Power BI build guide - Retail Sales Dashboard (about 90 minutes)

> A `.pbix` file is a binary produced only by Power BI Desktop (free, Windows). Everything needed to build it
> identically is in this folder: cleaned data (`data/`), measures (`dax_measures.md`) and a theme (`theme.json`).
> **When finished, save the file here as `Retail_Sales_Dashboard.pbix` and export 3 screenshots into `/images`
> - recruiters rarely open .pbix files, but they always look at screenshots in the README.**

## 1. Load data (Home > Get data > Text/CSV)
`data/fact_sales_report.csv`, `dim_customer.csv`, `dim_product.csv`, `dim_date.csv`, `customer_rfm.csv`.
In Power Query: set `order_date` and `dim_date[date]` to **Date**; revenue/profit/cost to **Fixed decimal**; discount to **Percentage**.

## 2. Model (Model view) - star schema
| From (many) | To (one) | Notes |
|---|---|---|
| fact_sales_report[order_date] | dim_date[date] | single direction; **Mark dim_date as date table** |
| fact_sales_report[customer_id] | dim_customer[customer_id] | |
| fact_sales_report[product_id] | dim_product[product_id] | |
| customer_rfm[customer_id] | dim_customer[customer_id] | |

Hide foreign keys and the raw numeric columns so report users only see measures.
Apply the theme: View > Themes > Browse for themes > `theme.json`.

## 3. Measures
Copy everything from `dax_measures.md` into a `_Measures` table.

## 4. Pages and visuals
**Page 1 - Executive Overview** (answer: "How is the business doing?")
- Row of 5 KPI cards: Total Revenue, Total Profit, Profit Margin %, Orders, Avg Order Value (add small YoY % text under revenue).
- Line chart: dim_date[year_month] x [Total Revenue] + [Revenue 3M Avg]. Add the analytics-pane forecast (3 months, seasonality 12).
- Clustered column: category x year revenue. Filled map or bar: revenue by city.
- Slicers: year (tile style), region, segment. Sync slicers across pages (View > Sync slicers).

**Page 2 - Profitability & Discounts** (answer: "Where do we lose money?")
- Column chart: `Discount Band` x [Profit Margin %] with [Margin Color] conditional formatting - the bars for 11-20% and 21%+ go red.
- Matrix: category > sub_category x [Total Revenue], [Profit Margin %] (data bars + colour scale).
- Scatter: product revenue (x) vs margin % (y), size = units, legend = category - lets you spot loss-making stars.
- Card: [% Lines at a Loss]; text box with the recommendation "cap discounts at 10%".
- Tooltip page: build a hidden page with a mini trend chart and assign it as tooltip for the scatter.

**Page 3 - Customers** (answer: "Who should we nurture or win back?")
- Donut/bar: customers per `rfm_segment`; bar of revenue per segment.
- Table: top 20 customers (customer_id, segment, region, monetary, frequency, recency_days).
- Cards: [At-Risk Customers], [At-Risk Revenue].
- Drill-through page: right-click a customer segment > drill through to a customer list.

## 5. Polish checklist (what separates a good dashboard from a great one)
- [ ] One message per page; titles state the insight, not the metric ("Discounts above 10% destroy margin").
- [ ] Consistent colours: blue = good/neutral, orange = highlight, red = problem only.
- [ ] Align and distribute visuals; 8px grid; no default titles like "Sum of revenue by city".
- [ ] Bookmarks + buttons for a "Reset filters" button; page navigator.
- [ ] Alt text on visuals; test on Phone layout (View > Phone layout).
- [ ] Performance Analyzer shows no visual > 500 ms.

## 6. Publish / share
Home > Publish to Power BI (free account) > File > Publish to web **only for non-sensitive/synthetic data** (this data is synthetic, so it is safe). Put the link at the top of the README.
