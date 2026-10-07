# DAX measures - Telecom Churn dashboard

Create an empty `_Measures` table and add these. Model: `customer_360[customer_id]` 1-to-1 `churn_scores[customer_id]`;
`tickets[customer_id]` many-to-1 `customer_360[customer_id]`.

```dax
-- ===== Core =====
Customers         = COUNTROWS ( customer_360 )
Churned Customers = SUM ( customer_360[churned] )
Churn Rate        = DIVIDE ( [Churned Customers], [Customers] )
Avg Tenure (months) = AVERAGE ( customer_360[tenure_months] )
Avg Monthly Charge  = AVERAGE ( customer_360[monthly_charges] )
Monthly Revenue Lost = CALCULATE ( SUM ( customer_360[monthly_charges] ), customer_360[churned] = 1 )
Annualised Revenue Lost = [Monthly Revenue Lost] * 12

-- ===== Comparison to the average (use in matrix / bar visuals) =====
Churn Index vs Avg = DIVIDE ( [Churn Rate], CALCULATE ( [Churn Rate], ALL ( customer_360 ) ) )

-- ===== Model-driven =====
Active Customers = CALCULATE ( [Customers], customer_360[churned] = 0 )
High-Risk Active Customers =
    CALCULATE ( COUNTROWS ( churn_scores ), churn_scores[risk_tier] = "High", churn_scores[churned] = 0 )
Expected Monthly Revenue at Risk =
    SUMX ( FILTER ( churn_scores, churn_scores[churned] = 0 ),
           churn_scores[churn_probability] * churn_scores[monthly_charges] )
Avg Churn Probability = AVERAGE ( churn_scores[churn_probability] )

-- ===== What-if parameters (Modeling > New parameter > Numeric range) =====
-- Save Rate: 0.05 to 0.50 step 0.05, default 0.25  -> creates [Save Rate Value]
-- Offer Take-up: 0.10 to 0.60 step 0.05, default 0.30 -> creates [Offer Take-up Value]
-- Discount: 0.05 to 0.30 step 0.05, default 0.15 -> creates [Discount Value]
Campaign Net Benefit (High tier) =
VAR _targets  = CALCULATETABLE ( churn_scores, churn_scores[risk_tier] = "High", churn_scores[churned] = 0 )
VAR _n        = COUNTROWS ( _targets )
VAR _churners = SUMX ( _targets, churn_scores[churn_probability] )
VAR _avgbill  = AVERAGEX ( _targets, churn_scores[monthly_charges] )
VAR _profit   = _churners * [Save Rate Value] * _avgbill * 12 * 0.5          -- 12 months kept, 50% margin
VAR _cost     = _n * 5 + _n * [Offer Take-up Value] * _avgbill * [Discount Value] * 6
RETURN _profit - _cost

-- ===== Tickets =====
Tickets = COUNTROWS ( tickets )
Avg Satisfaction = AVERAGE ( tickets[satisfaction_score] )
```
Calculated columns on `customer_360` are not needed - `tenure_band`, `charge_band`, `ticket_count` already come from SQL.
