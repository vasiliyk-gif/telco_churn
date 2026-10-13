"""Shared pipeline builder for baseline, local smoke test, and Earth workers.

Import with: from pipeline import build_pipeline
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

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
TARGET = "Churn Value"
SEED = 42
INNER_VALIDATION_SIZE = 0.25


def _unwrap_chromosome(chromosome: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(chromosome, dict):
        return {}
    if "content" in chromosome and isinstance(chromosome["content"], dict):
        return chromosome["content"]
    return chromosome


def build_pipeline(
    chromosome: dict[str, Any] | None = None,
    *,
    y_inner_train: np.ndarray | None = None,
) -> Pipeline:
    """Build a sklearn Pipeline from a decoded chromosome (or baseline defaults)."""
    node = _unwrap_chromosome(chromosome or {})

    model_name = node.get("model", "logistic_regression")
    scaling_method = node.get("scaling_method", "standard")
    imbalance_method = node.get("imbalance_method", "none")

    logreg = node.get("logistic_regression") or {}
    xgb = node.get("xgboost") or {}
    if not isinstance(logreg, dict):
        logreg = {}
    if not isinstance(xgb, dict):
        xgb = {}

    numeric_steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="median")),
    ]
    if model_name == "logistic_regression" and scaling_method == "standard":
        numeric_steps.append(("scaler", StandardScaler()))

    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline(steps=numeric_steps), NUMERIC_FEATURES),
            ("cat", categorical_pipe, CATEGORICAL_FEATURES),
        ]
    )

    if model_name == "xgboost":
        n_estimators = int(xgb.get("n_estimators", 100))
        max_depth = int(xgb.get("max_depth", 3))
        learning_rate = float(xgb.get("learning_rate", 0.1))
        scale_pos_weight = 1.0
        if imbalance_method == "class_weight_balanced":
            if y_inner_train is None:
                raise ValueError(
                    "y_inner_train is required to compute scale_pos_weight"
                )
            y = np.asarray(y_inner_train).astype(int)
            n_pos = int((y == 1).sum())
            n_neg = int((y == 0).sum())
            scale_pos_weight = float(n_neg / max(n_pos, 1))
        estimator: Any = XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=SEED,
            n_jobs=1,
            scale_pos_weight=scale_pos_weight,
        )
    else:
        C = float(logreg.get("C", 1.0))
        class_weight = (
            "balanced" if imbalance_method == "class_weight_balanced" else None
        )
        estimator = LogisticRegression(
            C=C,
            class_weight=class_weight,
            solver="lbfgs",
            max_iter=500,
            random_state=SEED,
        )

    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", estimator),
        ]
    )


BASELINE_CHROMOSOME = {
    "model": "logistic_regression",
    "scaling_method": "standard",
    "imbalance_method": "none",
    "logistic_regression": {"C": 1.0},
    "xgboost": {
        "n_estimators": 100,
        "max_depth": 3,
        "learning_rate": 0.1,
    },
}
