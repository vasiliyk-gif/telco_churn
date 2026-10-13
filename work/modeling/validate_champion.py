"""Compare baseline vs Earth champion once on holdout.csv.

Run from repo root:
    python work/modeling/validate_champion.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from evaluate import classification_report_dict
from pipeline import (
    BASELINE_CHROMOSOME,
    FEATURE_COLUMNS,
    TARGET,
    build_pipeline,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAIN_PATH = REPO_ROOT / "work" / "exploration" / "train.csv"
HOLDOUT_PATH = REPO_ROOT / "work" / "exploration" / "holdout.csv"
CHAMPION_PATH = REPO_ROOT / "work" / "optimization" / "champion_chromosome.json"
OUT_PATH = Path(__file__).resolve().parent / "holdout_comparison.json"


def _load_champion() -> dict:
    if not CHAMPION_PATH.is_file():
        raise SystemExit(
            f"Missing {CHAMPION_PATH}. Run earth/run_search.py first."
        )
    data = json.loads(CHAMPION_PATH.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "chromosome" in data:
        return data["chromosome"]
    return data


def _score(chromosome: dict, X_train, y_train, X_hold, y_hold) -> dict:
    pipe = build_pipeline(chromosome, y_inner_train=y_train.to_numpy())
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_hold)
    return classification_report_dict(y_hold, y_pred)


def main() -> None:
    for path in (TRAIN_PATH, HOLDOUT_PATH):
        if not path.is_file():
            raise SystemExit(f"Missing {path}")

    train = pd.read_csv(TRAIN_PATH)
    holdout = pd.read_csv(HOLDOUT_PATH)
    X_train = train[FEATURE_COLUMNS]
    y_train = train[TARGET].astype(int)
    X_hold = holdout[FEATURE_COLUMNS]
    y_hold = holdout[TARGET].astype(int)

    champion = _load_champion()
    baseline_metrics = _score(
        BASELINE_CHROMOSOME, X_train, y_train, X_hold, y_hold
    )
    champion_metrics = _score(champion, X_train, y_train, X_hold, y_hold)

    payload = {
        "note": "First and only holdout metric read for Workshop 1.",
        "n_train": int(len(train)),
        "n_holdout": int(len(holdout)),
        "baseline": {
            "chromosome": BASELINE_CHROMOSOME,
            "metrics": baseline_metrics,
        },
        "champion": {
            "chromosome": champion,
            "metrics": champion_metrics,
            "source": str(CHAMPION_PATH.relative_to(REPO_ROOT)),
        },
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
