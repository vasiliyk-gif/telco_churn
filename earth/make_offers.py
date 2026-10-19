"""Step 8: turn a champion into offers on the 2010 listings (scored in the reveal).

    python earth/make_offers.py --name run1
    python earth/make_offers.py --name run1 --fitness work/runs/run1/fitness.py

Refits the champion's value models on all of 2006-2009 (work/exploration/train.csv), predicts every
2010 listing, applies the champion's pricing policy, and writes work/delivery/offers_2010_<name>.csv
(ListingID, predicted_value, offer, make_offer). It is scored by earth/score_2010.py once the teacher releases
the 2010 sale prices at the end of the lab.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="Run folder under work/runs/")
    ap.add_argument("--fitness", type=Path, help="Fitness file (default: the copy in the run folder, else work/optimization/fitness.py)")
    args = ap.parse_args()
    run_dir = ROOT / "work" / "runs" / args.name
    fitness = args.fitness or next(p for p in [run_dir / "fitness.py", ROOT / "work" / "optimization" / "fitness.py"] if p.is_file())
    spec = importlib.util.spec_from_file_location("fitness_for_offers", fitness)
    fit = importlib.util.module_from_spec(spec); spec.loader.exec_module(fit)

    champion = json.load(open(run_dir / "champion_chromosome.json"))
    genes = champion["chromosome"]
    genes = genes.get("content", genes)
    F = fit.FitnessClass(str(ROOT / "work" / "exploration"))
    listings = pd.read_csv(ROOT / "data" / "ames_2010_listings.csv", keep_default_na=False, na_values=[""])
    value, ridge, xgb = fit.Valuer(genes, F.data.columns).fit(F.data, F.y).predict(listings)
    offer, make = fit.offer_prices(genes["policy"], value, ridge, xgb, listings)
    out = ROOT / "work" / "delivery" / f"offers_2010_{args.name}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"ListingID": listings["ListingID"], "predicted_value": value.round(0), "offer": offer.round(0),
                  "make_offer": make}).to_csv(out, index=False)
    print(f"Wrote {out.relative_to(ROOT)}: offers on {int(make.sum())} of {len(listings)} listings, "
          f"mean margin {float(((value - offer) / value)[make].mean()):.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
