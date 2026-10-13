"""Join the five-table module and freeze train.csv / holdout.csv.

Run from repo root:
    python work/exploration/prepare_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
OUT_DIR = Path(__file__).resolve().parent

SEED = 42
HOLDOUT_SIZE = 0.2
TARGET = "Churn Value"

NUMERIC_FEATURES = [
    "Age",
    "Number of Dependents",
    "Tenure in Months",
    "Number of Referrals",
    "Avg Monthly Long Distance Charges",
    "Avg Monthly GB Download",
    "Monthly Charge",
    "Total Charges",
]

CATEGORICAL_FEATURES = [
    "Gender",
    "Married",
    "Dependents",
    "Offer",
    "Phone Service",
    "Multiple Lines",
    "Internet Service",
    "Internet Type",
    "Online Security",
    "Online Backup",
    "Device Protection Plan",
    "Premium Tech Support",
    "Streaming TV",
    "Streaming Movies",
    "Streaming Music",
    "Unlimited Data",
    "Contract",
    "Paperless Billing",
    "Payment Method",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def load_joined() -> pd.DataFrame:
    demo = pd.read_excel(DATA_DIR / "Telco_customer_churn_demographics.xlsx")
    loc = pd.read_excel(DATA_DIR / "Telco_customer_churn_location.xlsx")
    svc = pd.read_excel(DATA_DIR / "Telco_customer_churn_services.xlsx")
    status = pd.read_excel(DATA_DIR / "Telco_customer_churn_status.xlsx")

    df = (
        demo.merge(loc, on="Customer ID", how="inner", suffixes=("", "_loc"))
        .merge(svc, on="Customer ID", how="inner", suffixes=("", "_svc"))
        .merge(status, on="Customer ID", how="inner", suffixes=("", "_status"))
    )
    if len(df) != 7043:
        raise RuntimeError(f"Expected 7043 customers after join, got {len(df)}")

    for col in NUMERIC_FEATURES + [TARGET]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    keep = ["Customer ID", TARGET] + FEATURE_COLUMNS
    missing = [c for c in keep if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing columns after join: {missing}")
    return df[keep].copy()


def main() -> None:
    df = load_joined()
    y = df[TARGET].astype(int)
    train_df, holdout_df = train_test_split(
        df,
        test_size=HOLDOUT_SIZE,
        random_state=SEED,
        stratify=y,
    )

    train_path = OUT_DIR / "train.csv"
    holdout_path = OUT_DIR / "holdout.csv"
    train_df.to_csv(train_path, index=False)
    holdout_df.to_csv(holdout_path, index=False)

    meta = {
        "split_version": "split_v1",
        "seed": SEED,
        "holdout_size": HOLDOUT_SIZE,
        "method": "stratified_train_holdout",
        "target": TARGET,
        "n_total": int(len(df)),
        "n_train": int(len(train_df)),
        "n_holdout": int(len(holdout_df)),
        "train_positive_rate": float(train_df[TARGET].mean()),
        "holdout_positive_rate": float(holdout_df[TARGET].mean()),
        "feature_columns": FEATURE_COLUMNS,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "modeling_source": "five-table module (not Telco_customer_churn.xlsx)",
        "train_path": str(train_path.relative_to(REPO_ROOT)),
        "holdout_path": str(holdout_path.relative_to(REPO_ROOT)),
    }
    meta_path = OUT_DIR / "split_metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Wrote {train_path} ({len(train_df)} rows)")
    print(f"Wrote {holdout_path} ({len(holdout_df)} rows)")
    print(f"Wrote {meta_path}")
    print(
        f"train churn rate={meta['train_positive_rate']:.4f} "
        f"holdout churn rate={meta['holdout_positive_rate']:.4f}"
    )


if __name__ == "__main__":
    main()
