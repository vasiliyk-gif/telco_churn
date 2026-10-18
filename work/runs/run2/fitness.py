"""Fitness skeleton for the term-deposit campaign. Copy it, then fill in the TODOs.

    cp earth/fitness_skeleton.py work/optimization/fitness.py

What Earth needs from this file:
  - a class FitnessClass(dataset_root) that loads the data once in __init__;
  - calculate_fitness(chromosome) -> FitnessCalculationResult, which never raises;
  - a score that is finite and > 0, where higher is better.

Every gene in your chromosome.yaml must be read somewhere in this file, and
every gene this file reads must exist in chromosome.yaml. The money and the
calling rule (how many to call) are fixed here and are never genes.
Check it locally before Earth:  python earth/check_local.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

# ---- CONTRACT: your framing decisions, fixed for every chromosome ---------------------------
TRAIN_ASSET = "train.csv"           # the file run_search.py uploads (work/exploration/train.csv)
TARGET = "y"
POSITIVE_CLASS = "yes"
COST_PER_CALL = 10.0                # from PROJECT_BRIEF.md; never a gene
VALUE_PER_SUBSCRIPTION = 70.0       # from PROJECT_BRIEF.md; never a gene
SEED = 42
CV_FOLDS = 5
INNER_FOLDS = 3                     # inner CV on each training part, to pick the share to call
ERROR_SCORE = 1e-9                  # Earth needs a finite score > 0

# TODO (Step 5): your feature boundary. Which columns may the model use?
# Leave out anything not known before the call. Group them if you want a gene
# that switches a whole group on or off.
FEATURE_GROUPS = {
    "client": {"num": ["age"], "cat": ["job", "marital", "education", "default", "housing", "loan"]},
    "history": {"num": ["previous"], "cat": ["poutcome"]},
    "channel": {"num": [], "cat": ["contact"]},
}
# Outside the boundary (framing.md): never a model input.
EXCLUDED_COLUMNS = {"duration", "campaign", "month", "day_of_week", "pdays", "contact_order",
                    "emp.var.rate", "cons.price.idx", "cons.conf.idx", "euribor3m", "nr.employed", TARGET}
PERFECT_PROFIT_PER_1000 = 6765.0    # calling only the subscribers: 0.11275 * 1000 * (70 - 10); see design.md
# ----------------------------------------------------------------------------------------------


class FitnessCalculationResult(BaseModel):
    score: float
    scalars: dict[str, float | int | dict[str, float | int]] | None = None
    rows: dict[str, list[str | float | int]] | None = None


def campaign_profit(y_true: np.ndarray, call: np.ndarray) -> float:
    """Profit of calling the clients where call is True.

    TODO (Step 6): VALUE_PER_SUBSCRIPTION for every subscriber you call,
    minus COST_PER_CALL for every call you make.
    """
    return VALUE_PER_SUBSCRIPTION * float(y_true[call].sum()) - COST_PER_CALL * float(call.sum())


def call_top_share(probability: np.ndarray, share: float) -> np.ndarray:
    """Call the top `share` of clients by predicted probability (array of True/False)."""
    n = int(round(share * len(probability)))
    call = np.zeros(len(probability), dtype=bool)
    call[np.argsort(-probability, kind="stable")[:n]] = True
    return call


def best_call_share(probability: np.ndarray, y_true: np.ndarray) -> float:
    """The share of clients to call that makes the most profit on these clients.

    TODO (Step 6): rank the clients by probability, compute the profit of calling
    the top 1, top 2, ... clients, and return the best number as a share of
    len(probability). If no list makes a profit, return 0.0.
    """
    order = np.argsort(-probability, kind="stable")
    profit_of_top_n = VALUE_PER_SUBSCRIPTION * np.cumsum(y_true[order]) - COST_PER_CALL * np.arange(1, len(order) + 1)
    best_n = int(np.argmax(profit_of_top_n)) + 1
    return best_n / len(order) if profit_of_top_n[best_n - 1] > 0 else 0.0


def call_list(train_probability: np.ndarray, train_y: np.ndarray, valid_probability: np.ndarray) -> np.ndarray:
    """Call list for the validation fold (array of True/False).

    How many to call is learned from the training part only: the share that
    maximises profit on the training clients' out-of-fold scores. That share is
    then called from the top of the validation fold's ranking. The validation
    labels never decide how many to call.
    """
    return call_top_share(valid_probability, best_call_share(train_probability, train_y))


def build_pipeline(genes: dict, y_fit: np.ndarray):
    """Return (sklearn Pipeline, list of input columns) for one chromosome.

    TODO (Step 6): read the genes (model family, hyperparameters, feature
    groups, preprocessing choices) and build the pipeline. Use n_jobs=1 in
    every model: Earth gives each worker one CPU.
    """
    num = [c for g in FEATURE_GROUPS.values() for c in g["num"]]
    cat = [c for g in FEATURE_GROUPS.values() for c in g["cat"]]
    if genes["pdays_flag"]:
        num = num + ["contacted_before"]
    assert not EXCLUDED_COLUMNS & set(num + cat), "a column outside the feature boundary"

    prep = ColumnTransformer([
        ("num", StandardScaler(), num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
    ])
    balanced = genes["class_weight_balanced"]
    family = genes["model_family"]
    if family == "logistic_regression":
        model = LogisticRegression(C=10 ** genes["lr_C_exponent"], max_iter=1000,
                                   class_weight="balanced" if balanced else None)
    elif family == "xgboost":
        model = XGBClassifier(
            max_depth=int(genes["xgb_max_depth"]),
            n_estimators=int(genes["xgb_n_estimators"]),
            learning_rate=10 ** genes["xgb_learning_rate_exponent"],
            scale_pos_weight=(len(y_fit) - y_fit.sum()) / y_fit.sum() if balanced else 1.0,
            tree_method="hist", n_jobs=1, random_state=SEED, verbosity=0,
        )
    else:
        raise ValueError(f"unknown model_family {family!r}")
    return Pipeline([("prep", prep), ("model", model)]), num + cat


class FitnessClass:
    def __init__(self, dataset_root: str):
        path = Path(dataset_root) / TRAIN_ASSET
        if not path.is_file():
            present = sorted(p.name for p in Path(dataset_root).rglob("*") if p.is_file())
            raise FileNotFoundError(f"{TRAIN_ASSET} not in the dataset; it holds {present}")
        self.x = pd.read_csv(path)
        # pdays_flag gene: "contacted before", the only allowed form of pdays (999 = never / not recorded).
        self.x["contacted_before"] = (self.x["pdays"] != 999).astype(int)
        self.y = (self.x[TARGET] == POSITIVE_CLASS).astype(int).to_numpy()
        # Folds are fixed once: every chromosome is scored on the same splits.
        self.folds = list(StratifiedKFold(CV_FOLDS, shuffle=True, random_state=SEED).split(self.x, self.y))
        # Inner folds inside each training part, for out-of-fold scores on the training clients.
        self.inner_folds = [
            [(train_idx[a], train_idx[b]) for a, b in
             StratifiedKFold(INNER_FOLDS, shuffle=True, random_state=SEED).split(train_idx, self.y[train_idx])]
            for train_idx, _ in self.folds
        ]

    def calculate_fitness(self, chromosome: dict) -> FitnessCalculationResult:
        try:
            return self._score(chromosome.get("content", chromosome))
        except Exception as exc:  # noqa: BLE001 -- Earth contract: never raise
            print(f"fitness error: {exc!r}")
            return FitnessCalculationResult(score=ERROR_SCORE, scalars={"error": 1})

    def _score(self, genes: dict) -> FitnessCalculationResult:
        fold_profits, shares, fold_f1s = [], [], []
        for (train_idx, valid_idx), inner in zip(self.folds, self.inner_folds):
            # 1. Out-of-fold scores for the training clients (INNER_FOLDS fits on the training part).
            train_probability = np.zeros(len(self.y))
            for fit_idx, oof_idx in inner:
                pipe, cols = build_pipeline(genes, self.y[fit_idx])
                pipe.fit(self.x.iloc[fit_idx][cols], self.y[fit_idx])
                train_probability[oof_idx] = pipe.predict_proba(self.x.iloc[oof_idx][cols])[:, 1]
            # 2. Refit on the whole training part and score the validation fold.
            pipe, cols = build_pipeline(genes, self.y[train_idx])
            pipe.fit(self.x.iloc[train_idx][cols], self.y[train_idx])
            probability = pipe.predict_proba(self.x.iloc[valid_idx][cols])[:, 1]
            # 3. The share to call is picked on the training clients, then applied to the validation fold.
            call = call_list(train_probability[train_idx], self.y[train_idx], probability)
            fold_profits.append(campaign_profit(self.y[valid_idx], call) * 1000 / len(valid_idx))
            shares.append(float(call.mean()))
            # run2: F1 at threshold 0.5 on the validation fold (ignores the money and the call list).
            fold_f1s.append(f1_score(self.y[valid_idx], probability >= 0.5, zero_division=0))

        # TODO (Step 6): turn profit into a score that is > 0 and where higher is
        # better. Profit can be negative, so you need a decision here; write it in
        # work/design.md. Keep the score roughly between 0 and 1.
        # run2: the score is mean F1 at threshold 0.5 over the folds, instead of normalized profit.
        # The profit scalars below are kept, to compare the money with run1.
        score = np.mean(fold_f1s)
        return FitnessCalculationResult(
            score=max(float(score), ERROR_SCORE),
            scalars={
                "profit_per_1000_mean": float(np.mean(fold_profits)),
                "profit_per_1000_std": float(np.std(fold_profits)),
                "profit_per_1000_per_fold": {f"fold_{i}": float(p) for i, p in enumerate(fold_profits)},
                "share_called": float(np.mean(shares)),
                "f1_mean": float(np.mean(fold_f1s)),
                # TODO (stretch): precision of the call list.
            },
        )

    def save_model(self):
        return None
