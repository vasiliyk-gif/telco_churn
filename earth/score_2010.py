"""Step 8: the reveal. Score your offers on what the 2010 homes really sold for, once.

    git pull                      # when the teacher releases data/ames_2010_prices.csv
    python earth/score_2010.py    # scores every offers file you made

Scores work/baseline/offers_2010_classic.csv and every work/delivery/offers_2010_*.csv with the same
market rule as the fitness (earth/ibuyer_market.py): risk-adjusted profit, profit, losses, homes bought,
and the price model's error. Run it once, after your analysis. Tuning anything on these numbers turns the
test into training data.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "earth"))
from ibuyer_market import expected_outcome  # noqa: E402

PRICES = ROOT / "data" / "ames_2010_prices.csv"


def score(path: Path, prices: pd.DataFrame) -> dict:
    df = prices.merge(pd.read_csv(path), on="ListingID", how="left", validate="one_to_one")
    make = df["make_offer"].fillna(False).astype(str).str.lower().isin(["true", "1"]).to_numpy()
    offer = df["offer"].fillna(0).to_numpy(float)
    value = df["SalePrice"].to_numpy(float)
    out = expected_outcome(offer, make & (offer > 0), value)
    out["mape"] = float(np.nanmean(np.abs(df["predicted_value"].to_numpy(float) - value) / value))
    return out


def main() -> int:
    if not PRICES.is_file():
        print("The 2010 prices are not released yet. The teacher releases them at the end of the lab;\n"
              "then run  git pull  and this script again.")
        return 1
    prices = pd.read_csv(PRICES)
    files = [ROOT / "work" / "baseline" / "offers_2010_classic.csv"] + sorted((ROOT / "work" / "delivery").glob("offers_2010_*.csv"))
    files = [f for f in files if f.is_file()]
    if not files:
        print("No offers yet. Run  python earth/classic_baseline.py  and  python earth/make_offers.py --name run1  first.")
        return 1
    print(f"2010 result on {len(prices)} listings (per 100 homes in brackets):")
    for f in files:
        r = score(f, prices)
        k = 100 / len(prices)
        print(f"  {f.stem:28s} risk-adj ${r['risk_adj']:>10,.0f}  profit ${r['profit']:>10,.0f} (${r['profit'] * k:>8,.0f})  "
              f"losses ${r['losses']:>10,.0f}  bought {r['bought']:5.1f}  price error {r['mape']:.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
