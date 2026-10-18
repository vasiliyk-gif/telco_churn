"""Step 4: score the three baselines with the protocol in work/design.md, on train.csv only.

Run from anywhere: python work/baseline/baselines.py
Writes work/baseline/metrics.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

# ---- Fixed by work/framing.md and work/design.md ----
COST_PER_CALL = 10.0
VALUE_PER_SUBSCRIPTION = 70.0
SEED = 42
CV_FOLDS = 5
INNER_FOLDS = 3
PERFECT_PROFIT_PER_1000 = 6765.0    # calling only the subscribers: 0.11275 * 1000 * (70 - 10)

# Feature boundary (framing.md): only columns known before the campaign starts.
NUM_COLS = ["age", "previous"]
CAT_COLS = ["job", "marital", "education", "default", "housing", "loan", "contact", "poutcome"]

# ---- Data: train.csv only, never test.csv ----
train = pd.read_csv(ROOT / "work" / "exploration" / "train.csv")
y = (train["y"] == "yes").astype(int).to_numpy()
print(f"train: {train.shape}, positives: {y.sum()}, rate: {y.mean():.5f}")

folds = list(StratifiedKFold(CV_FOLDS, shuffle=True, random_state=SEED).split(train, y))


def profit_per_1000(y_true, call):
    """€70 per subscriber called, minus €10 per call, scaled to 1,000 clients."""
    profit = VALUE_PER_SUBSCRIPTION * y_true[call].sum() - COST_PER_CALL * call.sum()
    return profit * 1000 / len(y_true)


def best_call_share(probability, y_true):
    """Share of clients to call (top of the ranking) that makes the most profit; 0 if none profits."""
    order = np.argsort(-probability, kind="stable")
    profit_of_top_n = VALUE_PER_SUBSCRIPTION * np.cumsum(y_true[order]) - COST_PER_CALL * np.arange(1, len(order) + 1)
    best_n = int(np.argmax(profit_of_top_n)) + 1
    return best_n / len(order) if profit_of_top_n[best_n - 1] > 0 else 0.0


def call_top_share(probability, share):
    """Call the top `share` of clients by predicted probability."""
    call = np.zeros(len(probability), dtype=bool)
    call[np.argsort(-probability, kind="stable")[:int(round(share * len(probability)))]] = True
    return call


def make_lr():
    """Plain logistic regression on the feature boundary: no tuning."""
    prep = ColumnTransformer([
        ("num", StandardScaler(), NUM_COLS),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
    ])
    return Pipeline([("prep", prep), ("lr", LogisticRegression(max_iter=1000))])


# ---- The three references, each returns the call list for one validation fold ----
def call_everyone(train_idx, valid_idx):
    return np.ones(len(valid_idx), dtype=bool)


def call_poutcome_success(train_idx, valid_idx):
    return (train.iloc[valid_idx]["poutcome"] == "success").to_numpy()


def call_logistic_regression(train_idx, valid_idx):
    x = train[NUM_COLS + CAT_COLS]
    # 1. Out-of-fold probabilities on the training part (inner 3-fold CV).
    inner = StratifiedKFold(INNER_FOLDS, shuffle=True, random_state=SEED)
    oof = cross_val_predict(make_lr(), x.iloc[train_idx], y[train_idx], cv=inner, method="predict_proba")[:, 1]
    # 2. The share to call is picked on the training part only.
    share = best_call_share(oof, y[train_idx])
    # 3. Refit on the whole training part, call the top share of the validation fold.
    model = make_lr().fit(x.iloc[train_idx], y[train_idx])
    return call_top_share(model.predict_proba(x.iloc[valid_idx])[:, 1], share)


REFERENCES = {
    "call_everyone": call_everyone,
    "poutcome_success": call_poutcome_success,
    "logistic_regression": call_logistic_regression,
}

metrics = {}
for name, make_call in REFERENCES.items():
    profits, shares = [], []
    for train_idx, valid_idx in folds:
        call = make_call(train_idx, valid_idx)
        profits.append(profit_per_1000(y[valid_idx], call))
        shares.append(float(call.mean()))
    metrics[name] = {
        "profit_per_1000_mean": float(np.mean(profits)),
        "profit_per_1000_std": float(np.std(profits)),
        "profit_per_1000_per_fold": [round(p, 1) for p in profits],
        "share_called_mean": float(np.mean(shares)),
        "score": max(float(np.mean(profits)) / PERFECT_PROFIT_PER_1000, 1e-9),
    }

print(f"\n{'reference':22s} {'profit/1000 mean':>17s} {'std':>7s} {'share called':>13s} {'score':>7s}")
for name, m in metrics.items():
    print(f"{name:22s} {m['profit_per_1000_mean']:17.0f} {m['profit_per_1000_std']:7.0f} "
          f"{m['share_called_mean']:13.1%} {m['score']:7.3f}")

(OUT / "metrics.json").write_text(json.dumps({
    "protocol": "work/design.md: 5 stratified folds (seed 42), inner 3-fold CV picks the share to call",
    "data": "work/exploration/train.csv",
    "features": {"num": NUM_COLS, "cat": CAT_COLS},
    "references": metrics,
}, indent=2))
print(f"\nwritten: {OUT / 'metrics.json'}")
