"""Fixed logistic baseline scored on validation cut from train.csv.

Run from repo root:
    python work/modeling/baseline.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from evaluate import classification_report_dict
from pipeline import (
    BASELINE_CHROMOSOME,
    FEATURE_COLUMNS,
    INNER_VALIDATION_SIZE,
    SEED,
    TARGET,
    build_pipeline,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAIN_PATH = REPO_ROOT / "work" / "exploration" / "train.csv"
OUT_PATH = Path(__file__).resolve().parent / "baseline_metrics.json"


def main() -> None:
    if not TRAIN_PATH.is_file():
        raise SystemExit(
            f"Missing {TRAIN_PATH}. Run: python work/exploration/prepare_data.py"
        )
    df = pd.read_csv(TRAIN_PATH)
    X = df[FEATURE_COLUMNS]
    y = df[TARGET].astype(int)

    X_inner, X_val, y_inner, y_val = train_test_split(
        X,
        y,
        test_size=INNER_VALIDATION_SIZE,
        random_state=SEED,
        stratify=y,
    )

    pipe = build_pipeline(BASELINE_CHROMOSOME, y_inner_train=y_inner.to_numpy())
    pipe.fit(X_inner, y_inner)
    y_pred = pipe.predict(X_val)
    metrics = classification_report_dict(y_val, y_pred)
    payload = {
        "split": "validation_from_train",
        "chromosome": BASELINE_CHROMOSOME,
        "n_inner_train": int(len(X_inner)),
        "n_validation": int(len(X_val)),
        "metrics": metrics,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
