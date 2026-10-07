# DAX measures - Retail Sales dashboard

Create a table called `_Measures` (Home > Enter Data, leave empty) and add each measure below to it.
Model first: see `DASHBOARD_BUILD_GUIDE.md` (star schema + a marked Date table).

```dax
-- ===== Core KPIs =====
Total Revenue   = SUM ( fact_sales_report[revenue] )
Total Profit    = SUM ( fact_sales_report[profit] )
Profit Margin % = DIVIDE ( [Total Profit], [Total Revenue] )
Orders          = DISTINCTCOUNT ( fact_sales_report[order_id] )
Customers       = DISTINCTCOUNT ( fact_sales_report[customer_id] )
Avg Order Value = DIVIDE ( [Total Revenue], [Orders] )
Avg Discount %  = AVERAGE ( fact_sales_report[discount] )

-- ===== Time intelligence (needs dim_date[date] marked as Date table) =====
Revenue LY   = CALCULATE ( [Total Revenue], SAMEPERIODLASTYEAR ( dim_date[date] ) )
Revenue YoY % = DIVIDE ( [Total Revenue] - [Revenue LY], [Revenue LY] )
Revenue YTD  = TOTALYTD ( [Total Revenue], dim_date[date] )
Revenue PM   = CALCULATE ( [Total Revenue], DATEADD ( dim_date[date], -1, MONTH ) )
Revenue MoM % = DIVIDE ( [Total Revenue] - [Revenue PM], [Revenue PM] )
Revenue 3M Avg =                                   -- average MONTHLY revenue over the trailing 3 months
    DIVIDE ( CALCULATE ( [Total Revenue], DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -3, MONTH ) ), 3 )

-- ===== The headline insight: discounts destroy margin =====
Loss-Making Lines   = CALCULATE ( COUNTROWS ( fact_sales_report ), fact_sales_report[profit] < 0 )
% Lines at a Loss   = DIVIDE ( [Loss-Making Lines], COUNTROWS ( fact_sales_report ) )
Profit Lost to Loss Lines = - CALCULATE ( [Total Profit], fact_sales_report[profit] < 0 )

-- Calculated column on fact_sales_report (Modeling > New column)
Discount Band =
SWITCH ( TRUE (),
    fact_sales_report[discount] = 0,    "0% (none)",
    fact_sales_report[discount] <= 0.10, "1-10%",
    fact_sales_report[discount] <= 0.20, "11-20%",
    "21%+" )

-- ===== Ranking & contribution =====
Revenue Share % = DIVIDE ( [Total Revenue], CALCULATE ( [Total Revenue], ALL ( fact_sales_report ) ) )
City Rank       = RANKX ( ALL ( fact_sales_report[city] ), [Total Revenue], , DESC )

-- ===== Customer segments (from customer_rfm table) =====
At-Risk Customers = CALCULATE ( DISTINCTCOUNT ( customer_rfm[customer_id] ), customer_rfm[rfm_segment] = "At Risk" )
At-Risk Revenue   = CALCULATE ( SUM ( customer_rfm[monetary] ), customer_rfm[rfm_segment] = "At Risk" )

-- ===== Storytelling helpers =====
Margin Color =                                     -- Conditional formatting > Format by > Field value
    IF ( [Profit Margin %] < 0, "#C0392B", IF ( [Profit Margin %] < 0.08, "#F2C14E", "#3A9D6E" ) )

Dynamic Title =
    "Revenue " & FORMAT ( [Total Revenue] / 1000000, "#,0.0" ) & "M | margin "
    & FORMAT ( [Profit Margin %], "0.0%" ) & IF ( ISFILTERED ( dim_date[year] ), " | " & SELECTEDVALUE ( dim_date[year] ), " | 2022-24" )
```

**Why these matter in an interview:** `CALCULATE` + filter context, time intelligence on a proper date table,
`DIVIDE` for safe division, `ALL` for percent-of-total, and `RANKX`. Be ready to explain *filter context vs row context*.
