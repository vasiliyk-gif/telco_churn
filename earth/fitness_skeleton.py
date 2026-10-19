"""Fitness skeleton for Lab 2: iBuyer instant offers on Ames. Copy it, then fill in the TODOs.

    cp earth/fitness_skeleton.py work/optimization/fitness.py

The company offers  predicted value x (1 - margin)  on every listed home. The fitness scores one
chromosome (valuation pipeline + pricing policy) by its expected risk-adjusted profit per listing over
three past years: train on the years before Y, make offers on year Y, for Y = 2007, 2008, 2009.

What is given: the data loading, the folds, the market rule, and the valuation part (Valuer).
What you write (TODO): the pricing policy (offer_prices) and the score.
Every gene in your chromosome.yaml must be read somewhere in this file, and every gene this file reads
must exist in chromosome.yaml. Earth contract: never raises, score finite and > 0, n_jobs=1.
Check it locally before Earth:  python earth/check_local.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

# ---- CONTRACT: fixed for every chromosome ----------------------------------------------------
TRAIN_ASSET = "train.csv"           # work/exploration/train.csv = data/ames_history.csv (2006-2009)
TARGET = "SalePrice"
VALID_YEARS = (2007, 2008, 2009)    # expanding window: train on all earlier years
ERROR_SCORE = 1e-9
NOT_FEATURES = ["Order", "PID", "ListingID", "Mo Sold", "Yr Sold", "Sale Type", "Sale Condition", TARGET]
GROUPS = {
    "quality": ["Overall Qual", "Overall Cond", "Exter Qual", "Exter Cond", "Kitchen Qual", "Heating QC", "Functional"],
    "size": ["Lot Frontage", "Lot Area", "Total Bsmt SF", "1st Flr SF", "2nd Flr SF", "Low Qual Fin SF", "Gr Liv Area",
             "TotRms AbvGrd", "Bedroom AbvGr", "Full Bath", "Half Bath", "Bsmt Full Bath", "Bsmt Half Bath", "Kitchen AbvGr"],
    "age": ["Year Built", "Year Remod/Add", "Garage Yr Blt"],
    "location": ["Neighborhood", "MS Zoning", "Condition 1", "Condition 2", "Lot Config", "Land Contour", "Land Slope",
                 "Street", "Alley", "Lot Shape"],
    "basement_garage": ["Bsmt Qual", "Bsmt Cond", "Bsmt Exposure", "BsmtFin Type 1", "BsmtFin SF 1", "BsmtFin Type 2",
                        "BsmtFin SF 2", "Bsmt Unf SF", "Garage Type", "Garage Finish", "Garage Cars", "Garage Area",
                        "Garage Qual", "Garage Cond", "Paved Drive"],
}
SWITCHABLE = ["age", "location", "basement_garage", "extras"]   # quality and size are always in
# ---- MARKET RULE: same as earth/ibuyer_market.py, do not change -----------------------------
COST = 0.05
FLEX = (0.02, 0.20)
RISK_WEIGHT = 0.5
MAX_OFFER = 500_000                 # company rule: never offer more than this on one home


def expected_outcome(offer, make, value):
    make = make & (offer <= MAX_OFFER)
    p_accept = np.clip((FLEX[1] - (1 - offer / value)) / (FLEX[1] - FLEX[0]), 0, 1) * make
    gain = value * (1 - COST) - offer
    profit = float((p_accept * gain).sum())
    losses = float((p_accept * np.minimum(gain, 0)).sum())
    return {"profit": profit, "losses": losses, "risk_adj": profit + RISK_WEIGHT * losses,
            "bought": float(p_accept.sum()), "offers_made": int(np.sum(make))}
# -----------------------------------------------------------------------------------------------


class FitnessCalculationResult(BaseModel):
    score: float
    scalars: dict[str, float | int | dict[str, float | int]] | None = None
    rows: dict[str, list[str | float | int]] | None = None


def feature_groups(columns) -> dict:
    grouped = {c for cols in GROUPS.values() for c in cols}
    return dict(GROUPS, extras=[c for c in columns if c not in grouped and c not in NOT_FEATURES])


class Valuer:
    """Two value models (ridge and XGBoost) and their blend. fit() on sales, predict() on any homes."""

    def __init__(self, genes: dict, columns):
        groups = feature_groups(columns)
        self.genes = genes
        self.cols = [c for g, cs in groups.items() if g not in SWITCHABLE or genes[f"use_{g}"] for c in cs]

    def _pre(self, x):
        num = [c for c in self.cols if pd.api.types.is_numeric_dtype(x[c])]
        cat = [c for c in self.cols if c not in num]
        return ColumnTransformer([
            ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), num),
            ("cat", Pipeline([("impute", SimpleImputer(strategy="constant", fill_value="NA")),
                              ("onehot", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=10,
                                                       sparse_output=False))]), cat)])

    def fit(self, x: pd.DataFrame, y: np.ndarray) -> "Valuer":
        g = self.genes
        if g["drop_big_houses"]:
            keep = (x["Gr Liv Area"] <= 4000).to_numpy()
            x, y = x[keep], y[keep]
        y_fit = np.log(y) if g["log_price"] else y
        quantile = {"objective": "reg:quantileerror", "quantile_alpha": float(g["quantile_alpha"])} if g["use_quantile"] else {}
        xg = g["xgb"]
        models = {"ridge": Ridge(alpha=float(g["ridge_alpha"])),
                  "xgb": XGBRegressor(n_estimators=int(xg["n_estimators"]), max_depth=int(xg["max_depth"]),
                                      learning_rate=float(xg["learning_rate"]), subsample=float(xg["subsample"]),
                                      colsample_bytree=float(xg["colsample_bytree"]), random_state=42, n_jobs=1,
                                      verbosity=0, **quantile)}
        self.models = {k: Pipeline([("pre", self._pre(x)), ("model", m)]).fit(x[self.cols], y_fit) for k, m in models.items()}
        return self

    def predict(self, x: pd.DataFrame):
        """(blend, ridge, xgb) value predictions in dollars."""
        out = {}
        for k, pipe in self.models.items():
            p = pipe.predict(x[self.cols])
            out[k] = np.clip(np.exp(np.clip(p, 0, 20)) if self.genes["log_price"] else p, 1e4, 2e6)
        w = float(self.genes["w_xgb"])
        return w * out["xgb"] + (1 - w) * out["ridge"], out["ridge"], out["xgb"]


def offer_prices(policy: dict, value, ridge, xgb, x: pd.DataFrame):
    """Pricing policy: return (offer, make) arrays, one entry per home in x.

    offer = value x (1 - margin); make = False means no offer for that home.
    `policy` is the "policy" block of your chromosome. `value` is the blended prediction; `ridge` and
    `xgb` are the two models' own predictions (their disagreement is a cheap uncertainty signal).

    TODO (Step 5): design the margin. Start with one base margin (that is the classic policy), then add
    what you think a smart buyer would do, each as a gene. Ideas:
      - a bigger margin where the two models disagree:  disagree = |xgb - ridge| / value
      - margins by segment: quality (Overall Qual), age (Year Built), price tier (value)
      - no offer when the models disagree too much, or above a maximum offer
    """
    raise NotImplementedError


class FitnessClass:
    def __init__(self, dataset_root: str):
        path = Path(dataset_root) / TRAIN_ASSET
        if not path.is_file():
            present = sorted(p.name for p in Path(dataset_root).rglob("*") if p.is_file())
            raise FileNotFoundError(f"{TRAIN_ASSET} not in the dataset; it holds {present}")
        self.data = pd.read_csv(path, keep_default_na=False, na_values=[""])
        self.y = self.data[TARGET].to_numpy(dtype=float)
        year = self.data["Yr Sold"].to_numpy()
        self.folds = [(np.where(year < v)[0], np.where(year == v)[0]) for v in VALID_YEARS]

    def calculate_fitness(self, chromosome: dict) -> FitnessCalculationResult:
        try:
            return self._score(chromosome.get("content", chromosome))
        except Exception as exc:  # noqa: BLE001 -- Earth contract: never raise
            print(f"fitness error: {exc!r}")
            return FitnessCalculationResult(score=ERROR_SCORE, scalars={"error": 1})

    def _score(self, genes: dict) -> FitnessCalculationResult:
        totals = {"profit": 0.0, "losses": 0.0, "bought": 0.0}
        per_year, n = {}, 0
        for (train_idx, valid_idx), year in zip(self.folds, VALID_YEARS):
            x_tr, x_va = self.data.iloc[train_idx], self.data.iloc[valid_idx]
            value, ridge, xgb = Valuer(genes, self.data.columns).fit(x_tr, self.y[train_idx]).predict(x_va)
            offer, make = offer_prices(genes["policy"], value, ridge, xgb, x_va)
            out = expected_outcome(offer, make, self.y[valid_idx])
            for k in totals:
                totals[k] += out[k]
            per_year[f"risk_adj_per_listing_{year}"] = out["risk_adj"] / len(valid_idx)
            n += len(valid_idx)
        risk_adj = (totals["profit"] + RISK_WEIGHT * totals["losses"]) / n
        # TODO (Step 5): turn risk_adj (dollars per listing, can be negative) into a score that is > 0
        # and where higher is better. Keep it roughly between 0 and 1, and write your choice in
        # work/design.md. (A linear map that puts break-even at 0.5 is fine.)
        score = ...
        return FitnessCalculationResult(
            score=max(score if np.isfinite(score) else 0.0, ERROR_SCORE),
            scalars={"risk_adj_per_listing": risk_adj, "profit_per_listing": totals["profit"] / n,
                     "losses_per_listing": totals["losses"] / n, "share_bought": totals["bought"] / n,
                     "per_year": per_year},
        )

    def save_model(self):
        return None
