"""Gate 3: where does the classic policy (best-RMSE model + flat 18% margin) make and lose money?

    python3 work/baseline/gate3_segments.py

Re-fits the classic value model on the same three past-year folds, applies the flat margin, and splits the
risk-adjusted result per listing by segment. Writes work/baseline/gate3_homes.csv (one row per home).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "earth"))
import fitness_skeleton as fs  # noqa: E402
from ibuyer_market import COST, FLEX, MAX_OFFER, RISK_WEIGHT  # noqa: E402

metrics = json.loads((ROOT / "work/baseline/classic_metrics.json").read_text())
genes, margin = metrics["value_genes"], metrics["best_flat"]["margin"]

F = fs.FitnessClass(str(ROOT / "work/exploration"))
rows = []
for (tr, va), year in zip(F.folds, fs.VALID_YEARS):
    value, ridge, xgb = fs.Valuer(genes, F.data.columns).fit(F.data.iloc[tr], F.y[tr]).predict(F.data.iloc[va])
    true = F.y[va]
    offer = value * (1 - margin)
    make = offer <= MAX_OFFER
    p = np.clip((FLEX[1] - (1 - offer / true)) / (FLEX[1] - FLEX[0]), 0, 1) * make
    gain = true * (1 - COST) - offer
    rows.append(pd.DataFrame({
        "year": year, "true": true, "value": value, "error": value / true - 1,
        "ridge": ridge, "xgb": xgb,
        "qual": F.data["Overall Qual"].to_numpy()[va], "built": F.data["Year Built"].to_numpy()[va],
        "area": F.data["Gr Liv Area"].to_numpy()[va], "nbhd": F.data["Neighborhood"].to_numpy()[va],
        "p_accept": p, "profit": p * gain, "loss": p * np.minimum(gain, 0)}))
d = pd.concat(rows, ignore_index=True)
d["risk_adj"] = d.profit + RISK_WEIGHT * d.loss
d["disagree"] = (d.xgb - d.ridge).abs() / d.value
d.to_csv(ROOT / "work/baseline/gate3_homes.csv", index=False)


def table(by, label):
    g = d.groupby(by, observed=True)
    t = pd.DataFrame({"homes": g.size(), "bought": g.p_accept.sum().round(0),
                      "risk_adj_per_home": g.risk_adj.mean().round(0),
                      "loss_per_home": g.loss.mean().round(0),
                      "risk_adj_total_k": (g.risk_adj.sum() / 1000).round(0),
                      "median_error": g.error.median().round(3)})
    print(f"\n== by {label}\n{t.to_string()}")


n = len(d)
print(f"classic: margin {margin:.2f}, {n} past-year listings, risk-adjusted ${d.risk_adj.sum() / n:,.0f} per listing, "
      f"profit ${d.profit.sum() / n:,.0f}, losses ${d.loss.sum() / n:,.0f}")
table(pd.cut(d.error, [-1, -0.10, -0.05, 0, 0.05, 0.10, 1]), "model error (predicted / true - 1)")
table("qual", "Overall Qual")
table(pd.cut(d.value, [0, 100e3, 150e3, 200e3, 300e3, 2e6]), "predicted value")
table(pd.cut(d.built, [1800, 1920, 1950, 1970, 1990, 2000, 2011]), "Year Built")
table(pd.qcut(d.disagree, 5), "ridge/xgb disagreement (quintiles)")
table("year", "fold year")

nb = d.groupby("nbhd").agg(homes=("risk_adj", "size"), risk_adj_total_k=("risk_adj", "sum"))
nb.risk_adj_total_k = (nb.risk_adj_total_k / 1000).round(0)
print("\n== worst 5 neighbourhoods (total)\n", nb.sort_values("risk_adj_total_k").head(5).to_string())

ideal = d.risk_adj.clip(lower=0).sum() / n
print(f"\nupper bound if we could skip every losing home (same offers): ${ideal:,.0f} per listing")
print(f"homes that lose money in expectation: {(d.risk_adj < 0).sum()} of {n}; they cost "
      f"${-d.risk_adj[d.risk_adj < 0].sum() / n:,.0f} per listing")
