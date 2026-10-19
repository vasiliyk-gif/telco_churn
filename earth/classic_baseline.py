"""Step 3: the classic data-science pipeline, scored with the same folds and market rule as the fitness.

    python earth/classic_baseline.py

1. Pick the most accurate value model by RMSE (a small grid of ridge and XGBoost) on the three past
   years (train before Y, predict Y, Y = 2007, 2008, 2009).
2. Pick one flat margin (0%-30%) that maximises the risk-adjusted profit on the same three years.
3. Refit on all of 2006-2009 and write offers for the 2010 listings.
Writes work/baseline/classic_metrics.json and work/baseline/offers_2010_classic.csv. No Earth calls.
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "earth"))
import fitness_skeleton as fs  # noqa: E402  (the given parts: Valuer, folds, market rule)
from ibuyer_market import expected_outcome, RISK_WEIGHT  # noqa: E402

ALL_GROUPS = {"use_age": True, "use_location": True, "use_basement_garage": True, "use_extras": True}
BASE = ALL_GROUPS | {"drop_big_houses": True, "use_quantile": False, "quantile_alpha": 0.5, "ridge_alpha": 10.0,
                     "xgb": {"n_estimators": 300, "max_depth": 3, "learning_rate": 0.1, "subsample": 0.8,
                             "colsample_bytree": 0.8}}


def grid():
    for alpha, log in itertools.product([3.0, 10.0, 30.0], [True, False]):
        yield f"ridge alpha={alpha} log={log}", BASE | {"w_xgb": 0.0, "ridge_alpha": alpha, "log_price": log}
    for depth, n, lr in itertools.product([3, 4], [300, 700], [0.03, 0.1]):
        xg = dict(BASE["xgb"], max_depth=depth, n_estimators=n, learning_rate=lr)
        yield f"xgboost depth={depth} trees={n} lr={lr}", BASE | {"w_xgb": 1.0, "log_price": True, "xgb": xg}


def main() -> int:
    F = fs.FitnessClass(str(ROOT / "work" / "exploration"))
    data, y = F.data, F.y
    print("1. Value models by RMSE on 2007, 2008, 2009 (train on earlier years):", flush=True)
    best = None
    for name, genes in grid():
        preds = [fs.Valuer(genes, data.columns).fit(data.iloc[tr], y[tr]).predict(data.iloc[va]) for tr, va in F.folds]
        err = np.concatenate([p[0] - y[va] for p, (tr, va) in zip(preds, F.folds)])
        rmse = float(np.sqrt(np.mean(err ** 2)))
        mape = float(np.mean(np.abs(err) / np.concatenate([y[va] for _, va in F.folds])))
        print(f"   {name:34s} RMSE ${rmse:,.0f}  MAPE {mape:.3f}", flush=True)
        if best is None or rmse < best[0]:
            best = (rmse, mape, name, genes, preds)
    rmse, mape, name, genes, preds = best
    print(f"   -> most accurate: {name}", flush=True)

    def result(margin):
        outs = []
        for (value, _, _), (tr, va) in zip(preds, F.folds):
            outs.append(expected_outcome(value * (1 - margin), np.ones(len(va), bool), y[va]))
        n = sum(len(va) for _, va in F.folds)
        return {"margin": margin, "risk_adj_per_listing": sum(o["risk_adj"] for o in outs) / n,
                "profit_per_listing": sum(o["profit"] for o in outs) / n,
                "losses_per_listing": sum(o["losses"] for o in outs) / n,
                "share_bought": sum(o["bought"] for o in outs) / n,
                "per_year": {f"risk_adj_per_listing_{v}": o["risk_adj"] / len(va)
                             for o, v, (_, va) in zip(outs, fs.VALID_YEARS, F.folds)}}

    print("2. One flat margin, tuned for risk-adjusted profit on the same years:", flush=True)
    results = [result(m) for m in np.round(np.arange(0, 0.301, 0.01), 2)]
    for r in results[::5]:
        print(f"   margin {r['margin']:.2f}: ${r['risk_adj_per_listing']:>7,.0f} per listing", flush=True)
    top = max(results, key=lambda r: r["risk_adj_per_listing"])
    flat10 = next(r for r in results if r["margin"] == 0.10)
    print(f"   -> best flat margin {top['margin']:.2f}: ${top['risk_adj_per_listing']:,.0f} risk-adjusted per listing "
          f"(profit ${top['profit_per_listing']:,.0f}, losses ${top['losses_per_listing']:,.0f}, "
          f"buys {top['share_bought']:.0%} of listings); the same score as fitness = "
          f"{(top['risk_adj_per_listing'] + 3000) / 6000:.4f} on the break-even-at-0.5 scale", flush=True)

    out = ROOT / "work" / "baseline"
    out.mkdir(parents=True, exist_ok=True)
    listings = pd.read_csv(ROOT / "data" / "ames_2010_listings.csv", keep_default_na=False, na_values=[""])
    value = fs.Valuer(genes, data.columns).fit(data, y).predict(listings)[0]
    pd.DataFrame({"ListingID": listings["ListingID"], "predicted_value": value.round(0),
                  "offer": (value * (1 - top["margin"])).round(0), "make_offer": True}).to_csv(
        out / "offers_2010_classic.csv", index=False)
    json.dump({"value_model": name, "value_genes": genes, "rmse": rmse, "mape": mape, "best_flat": top,
               "flat_10pct": flat10, "risk_weight": RISK_WEIGHT}, open(out / "classic_metrics.json", "w"), indent=2)
    print(f"3. Wrote {out / 'classic_metrics.json'} and {out / 'offers_2010_classic.csv'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
