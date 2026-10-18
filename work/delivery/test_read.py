"""Step 9: the one test read (EXPERIMENT_ANALYSIS_GUIDE.md question 6).

    python work/delivery/test_read.py --dry-run   # rehearsal on a slice of train.csv; test.csv is not opened
    python work/delivery/test_read.py             # THE test read: run once, then never again

For the LR baseline and the Earth champions, the share to call is picked the same way the
fitness does, now on all of train.csv (3-fold out-of-fold scores, most profitable top-N share).
Each model is then fitted on all of train.csv and calls that share from the top of the test set.
All policies are scored once: profit per 1,000 clients and share called.
Writes work/delivery/test_results.json and refuses to run a second time.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "work" / "optimization"))
import fitness as F  # noqa: E402  (same money, columns and pipelines as the search)

RESULTS = OUT / "test_results.json"
CHAMPION = json.loads((ROOT / "work/runs/run1/champion_chromosome.json").read_text())["chromosome"]
F1_CHAMPION = json.loads((ROOT / "work/runs/run2/champion_chromosome.json").read_text())["chromosome"]
BASELINE = {**CHAMPION, "model_family": "logistic_regression", "lr_C_exponent": 0.0,
            "class_weight_balanced": False, "pdays_flag": False}     # = work/baseline LR (C = 1)


def load(path):
    df = pd.read_csv(path)
    df["contacted_before"] = (df["pdays"] != 999).astype(int)    # same derived column as the fitness
    return df, (df[F.TARGET] == F.POSITIVE_CLASS).astype(int).to_numpy()


def model_call_list(genes, train, y_train, test):
    """Share picked on train.csv's out-of-fold scores, then called from the top of the test set."""
    oof = np.zeros(len(y_train))
    for fit_idx, oof_idx in StratifiedKFold(F.INNER_FOLDS, shuffle=True, random_state=F.SEED).split(train, y_train):
        pipe, cols = F.build_pipeline(genes, y_train[fit_idx])
        pipe.fit(train.iloc[fit_idx][cols], y_train[fit_idx])
        oof[oof_idx] = pipe.predict_proba(train.iloc[oof_idx][cols])[:, 1]
    share = F.best_call_share(oof, y_train)
    pipe, cols = F.build_pipeline(genes, y_train)
    pipe.fit(train[cols], y_train)
    return F.call_top_share(pipe.predict_proba(test[cols])[:, 1], share), share


def score(name, call, y_test, share_picked=None):
    profit = F.campaign_profit(y_test, call) * 1000 / len(y_test)
    row = {"policy": name, "profit_per_1000": round(profit, 1), "share_called": round(float(call.mean()), 4),
           "calls": int(call.sum()), "subscribers_called": int(y_test[call].sum())}
    if share_picked is not None:
        row["share_picked_on_train"] = round(share_picked, 4)
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="rehearse on a slice of train.csv; test.csv is not opened")
    args = parser.parse_args()

    train, y_train = load(ROOT / "work/exploration/train.csv")
    if args.dry_run:
        # Stand-in for the test set: a stratified random 20% of train.csv. It only proves the code runs.
        fit_idx, stand_in_idx = next(StratifiedKFold(5, shuffle=True, random_state=0).split(train, y_train))
        test, y_test = train.iloc[stand_in_idx].reset_index(drop=True), y_train[stand_in_idx]
        train, y_train = train.iloc[fit_idx].reset_index(drop=True), y_train[fit_idx]
        print("DRY RUN: test.csv not opened; scoring a slice of train.csv")
    else:
        if RESULTS.exists():
            raise SystemExit(f"{RESULTS.name} exists: the test set has been read once already. Do not read it again.")
        test, y_test = load(ROOT / "work/exploration/test.csv")

    rows = [
        score("call everyone", np.ones(len(y_test), dtype=bool), y_test),
        score('simple rule: poutcome == "success"', (test["poutcome"] == "success").to_numpy(), y_test),
    ]
    for name, genes in (("LR baseline", BASELINE), ("Earth champion (run1, profit fitness)", CHAMPION),
                        ("F1 champion (run2)", F1_CHAMPION)):
        call, share = model_call_list(genes, train, y_train, test)
        rows.append(score(name, call, y_test, share))

    table = pd.DataFrame(rows)
    print(f"\nn = {len(y_test)} clients, {int(y_test.sum())} subscribers ({y_test.mean():.2%})")
    print(table.to_string(index=False))
    champion, baseline = rows[3]["profit_per_1000"], rows[2]["profit_per_1000"]
    print(f"\nchampion - LR baseline: {champion - baseline:+.1f} per 1,000 (success margin: +300)")

    if not args.dry_run:
        RESULTS.write_text(json.dumps({
            "data": "work/exploration/test.csv, read once",
            "n_test": len(y_test), "subscribers": int(y_test.sum()),
            "champion_genes": CHAMPION, "baseline_genes": BASELINE, "f1_champion_genes": F1_CHAMPION,
            "policies": rows, "champion_minus_baseline": round(champion - baseline, 1),
        }, indent=2))
        print(f"written: {RESULTS}")


if __name__ == "__main__":
    main()
