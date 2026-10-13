# Framing (Workshop 1 solution reference)

## Goal

Build a binary classifier that flags customers at risk of churn as an input to a
later retention process. Optimize validation F1 with Earth.

## Prediction task and positive class

Binary classification. Positive class: `Churn Value == 1`.

## Workshop data assumption (restate in your own words)

The IBM file is a cross-section, not a true t → t+1 prediction snapshot. Selected
demographic and service fields are treated as prediction-time features for the
exercise; `Churn Value` is treated as the future binary outcome. Outcome and
target-adjacent fields are excluded.

## Metric contract

F1 for the positive class at threshold 0.5 (`zero_division=0`). Precision,
recall, and confusion matrix are reported beside F1. No business cost weights
are available in this exercise.

## Feature boundary (in / out)

In: Gender, Age, Married, Dependents, Number of Dependents, Tenure in Months,
Number of Referrals, Offer, Phone Service, Avg Monthly Long Distance Charges,
Multiple Lines, Internet Service, Internet Type, Avg Monthly GB Download,
Online Security, Online Backup, Device Protection Plan, Premium Tech Support,
Streaming TV / Movies / Music, Unlimited Data, Contract, Paperless Billing,
Payment Method, Monthly Charge, Total Charges.

Out: Customer ID, Count, Quarter, Country, State, City, Zip Code, Lat Long,
Latitude, Longitude, Churn Label / Value / Status, Churn Category / Reason,
Churn Score, CLTV, Satisfaction Score, Under 30, Senior Citizen, Referred a
Friend, Total Revenue and other cumulative money restatements.

Modeling source: five-table module. Not `Telco_customer_churn.xlsx`.

## Fixed protocol (seed, splits, threshold)

- Seed 42
- Stratified 80/20 → `train.csv` / `holdout.csv`
- Inner stratified 75/25 of train → `inner_train` / `validation` for baseline and Earth fitness
- Decision threshold 0.5
- Holdout read once at delivery only

## Will we optimize with Earth? Why?

Yes. Workshop 1 teaches packaging a formulated search for Earth after a fixed
baseline exists.
