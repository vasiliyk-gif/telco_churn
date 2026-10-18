"""Step 8: analyse run1 (EXPERIMENT_ANALYSIS_GUIDE.md questions 1-5), on train.csv only.

Run from the repo root after `python earth/fetch_history.py --name run1`:
    python work/analysis/analysis.py
Writes work/analysis/convergence.png and work/analysis/results.json.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "work" / "optimization"))
import fitness as F  # noqa: E402  (the same fitness Earth ran)

RUN = ROOT / "work" / "runs" / "run1"
CHAMPION = json.loads((RUN / "champion_chromosome.json").read_text())["chromosome"]
BASELINE = {**CHAMPION, "model_family": "logistic_regression", "lr_C_exponent": 0.0,
            "class_weight_balanced": False, "pdays_flag": False}       # = work/baseline LR (C = 1)
FRESH_SEEDS = [1, 2, 3, 4, 5]
results = {}

fc = F.FitnessClass(str(ROOT / "work" / "exploration"))      # loads train.csv only
y = fc.y


def make_folds(seed):
    folds = list(StratifiedKFold(F.CV_FOLDS, shuffle=True, random_state=seed).split(fc.x, y))
    inner = [[(tr[a], tr[b]) for a, b in
              StratifiedKFold(F.INNER_FOLDS, shuffle=True, random_state=seed).split(tr, y[tr])]
             for tr, _ in folds]
    return folds, inner


def fold_predictions(genes, seed=F.SEED):
    """Per outer fold: train/valid indices, out-of-fold train probabilities, validation probabilities.
    Same steps as FitnessClass._score; the money is applied afterwards, so it can be varied cheaply."""
    preds = []
    for (train_idx, valid_idx), inner in zip(*make_folds(seed)):
        train_probability = np.zeros(len(y))
        for fit_idx, oof_idx in inner:
            pipe, cols = F.build_pipeline(genes, y[fit_idx])
            pipe.fit(fc.x.iloc[fit_idx][cols], y[fit_idx])
            train_probability[oof_idx] = pipe.predict_proba(fc.x.iloc[oof_idx][cols])[:, 1]
        pipe, cols = F.build_pipeline(genes, y[train_idx])
        pipe.fit(fc.x.iloc[train_idx][cols], y[train_idx])
        preds.append((train_idx, valid_idx, train_probability[train_idx],
                      pipe.predict_proba(fc.x.iloc[valid_idx][cols])[:, 1]))
    return preds


def best_share(probability, y_true, cost, value):
    order = np.argsort(-probability, kind="stable")
    profit = value * np.cumsum(y_true[order]) - cost * np.arange(1, len(order) + 1)
    n = int(np.argmax(profit)) + 1
    return n / len(order) if profit[n - 1] > 0 else 0.0


def evaluate(preds, cost=F.COST_PER_CALL, value=F.VALUE_PER_SUBSCRIPTION):
    """Profit per 1,000 per fold with the fitness rule (share picked on the training part)."""
    rows = []
    for train_idx, valid_idx, p_train, p_valid in preds:
        share = best_share(p_train, y[train_idx], cost, value)
        call = F.call_top_share(p_valid, share)
        yv = y[valid_idx]
        rows.append({
            "profit_per_1000": (value * yv[call].sum() - cost * call.sum()) * 1000 / len(yv),
            "share": share, "calls": int(call.sum()), "subscribers": int(yv[call].sum()),
            "n": len(yv), "oracle_share": best_share(p_valid, yv, cost, value),   # best share in hindsight
        })
    return pd.DataFrame(rows)


def summary(df):
    return {"mean": float(df["profit_per_1000"].mean()), "std": float(df["profit_per_1000"].std(ddof=0)),
            "per_fold": [round(v, 1) for v in df["profit_per_1000"]], "share_mean": float(df["share"].mean())}


# ---- 1. Did the search behave? -------------------------------------------------------------
hist = pd.read_csv(RUN / "history.csv")
per_gen = hist.groupby("generation")["score"].agg(best="max", mean="mean", worst="min")
per_gen["best_so_far"] = per_gen["best"].cummax()
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.plot(per_gen.index, per_gen["best_so_far"], "o-", label="best so far")
ax.plot(per_gen.index, per_gen["mean"], "s-", label="population mean")
ax.fill_between(per_gen.index, per_gen["worst"], per_gen["best"], alpha=.15, label="worst-best range")
ax.axhline(0.220, color="k", ls=":", label="LR baseline (0.220)")
ax.axhline(0.264, color="tab:red", ls="--", label="target (0.264)")
ax.set_xlabel("generation"); ax.set_ylabel("score (profit / 6,765)"); ax.set_title("run1: convergence")
ax.legend(fontsize=7, loc="lower right"); plt.tight_layout()
fig.savefig(OUT / "convergence.png", dpi=120)
results["q1_per_generation"] = per_gen.round(4).reset_index().to_dict("records")
print("Q1 per generation:\n", per_gen.round(4).to_string())

# ---- 2. Champion vs the crowd -------------------------------------------------------------
genes = [c for c in hist.columns if c.startswith("gene.")]
distinct = hist.sort_values("score", ascending=False).drop_duplicates(subset=genes)
cols = ["generation", "score", "scalar.profit_per_1000_mean", "scalar.profit_per_1000_std",
        "scalar.share_called", "gene.model_family", "gene.xgb_max_depth", "gene.xgb_n_estimators",
        "gene.xgb_learning_rate_exponent", "gene.class_weight_balanced", "gene.pdays_flag"]
top = distinct[cols].head(10).reset_index(drop=True)
top.index += 1
champ_profit = top.loc[1, "scalar.profit_per_1000_mean"]
gaps = {f"#{k}": float(champ_profit - top.loc[k, "scalar.profit_per_1000_mean"]) for k in (2, 5, 10)}
results["q2_top10"] = top.round(4).to_dict("records")
results["q2_gap_to_champion_eur"] = gaps
print("\nQ2 top 10 distinct candidates:\n", top.round(3).to_string())
print("gap from champion (EUR per 1,000):", gaps)

# ---- 3. Which decisions mattered? one-flip checks on the champion ---------------------------
flips = {
    "champion": CHAMPION,
    "pdays_flag off": {**CHAMPION, "pdays_flag": False},
    "class weight on": {**CHAMPION, "class_weight_balanced": True},
    "depth 6 -> 4": {**CHAMPION, "xgb_max_depth": 4},
    "depth 6 -> 8 (outside the range)": {**CHAMPION, "xgb_max_depth": 8},
    "family -> LR (C = 1)": BASELINE | {"pdays_flag": CHAMPION["pdays_flag"]},
}
flip_rows = {}
for name, g in flips.items():
    s = summary(evaluate(fold_predictions(g)))
    flip_rows[name] = {"profit_per_1000_mean": round(s["mean"], 1), "change_vs_champion": None,
                       "share_called": round(s["share_mean"], 3), "per_fold": s["per_fold"]}
base = flip_rows["champion"]["profit_per_1000_mean"]
for r in flip_rows.values():
    r["change_vs_champion"] = round(r["profit_per_1000_mean"] - base, 1)
results["q3_one_flip"] = flip_rows
print("\nQ3 one-flip checks (seed 42 folds):")
for k, r in flip_rows.items():
    print(f"  {k:34s} {r['profit_per_1000_mean']:8.1f}  ({r['change_vs_champion']:+.1f})  share {r['share_called']:.3f}")

# ---- 4. Fresh folds -----------------------------------------------------------------------
fresh = {"champion": {}, "baseline": {}}
for seed in FRESH_SEEDS:
    for name, g in (("champion", CHAMPION), ("baseline", BASELINE)):
        fresh[name][seed] = summary(evaluate(fold_predictions(g, seed)))["mean"]
search = {"champion": summary(evaluate(fold_predictions(CHAMPION)))["mean"],
          "baseline": summary(evaluate(fold_predictions(BASELINE)))["mean"]}
diffs = [fresh["champion"][s] - fresh["baseline"][s] for s in FRESH_SEEDS]
q4 = {
    "search_seed42": search,
    "fresh_per_seed": fresh,
    "fresh_mean": {k: float(np.mean(list(v.values()))) for k, v in fresh.items()},
    "fresh_gain_per_seed": [round(d, 1) for d in diffs],
    "fresh_gain_mean": float(np.mean(diffs)), "fresh_gain_std": float(np.std(diffs)),
}
results["q4_fresh_folds"] = q4
print("\nQ4 search (seed 42) vs fresh seeds 1-5:")
for k in ("champion", "baseline"):
    print(f"  {k:9s} search {search[k]:7.1f}  fresh {q4['fresh_mean'][k]:7.1f}  "
          f"per seed {[round(fresh[k][s], 1) for s in FRESH_SEEDS]}")
print(f"  gain per seed {q4['fresh_gain_per_seed']}  mean {q4['fresh_gain_mean']:.1f}")

# ---- 5. Money -----------------------------------------------------------------------------
champ_preds, base_preds = fold_predictions(CHAMPION), fold_predictions(BASELINE)
champ_df, base_df = evaluate(champ_preds), evaluate(base_preds)

def per_10000(df):
    n = df["n"].sum()
    return {"calls": round(df["calls"].sum() / n * 10000), "subscriptions": round(df["subscribers"].sum() / n * 10000),
            "profit_eur": round(df["profit_per_1000"].mean() * 10)}

business = {"champion": per_10000(champ_df), "baseline": per_10000(base_df),
            "call_everyone": {"calls": 10000, "subscriptions": round(y.mean() * 10000),
                              "profit_eur": round((70 * y.mean() - 10) * 10000)}}

# Who is called (pooled over the 5 validation folds)
called = np.concatenate([valid_idx[F.call_top_share(p_valid, best_share(p_train, y[train_idx], 10, 70))]
                         for train_idx, valid_idx, p_train, p_valid in champ_preds])
x = fc.x
profile = {}
for col in ["poutcome", "contact", "job"]:
    profile[col] = pd.DataFrame({
        "share_of_called": x.iloc[called][col].value_counts(normalize=True),
        "share_of_all": x[col].value_counts(normalize=True)}).fillna(0).round(3).sort_values(
        "share_of_called", ascending=False).head(6).to_dict("index")
age = pd.cut(x["age"], [0, 30, 40, 50, 60, 120], labels=["<=30", "31-40", "41-50", "51-60", "60+"])
profile["age"] = pd.DataFrame({"share_of_called": age.iloc[called].value_counts(normalize=True),
                               "share_of_all": age.value_counts(normalize=True)}).round(3).to_dict("index")
profile["subscription_rate_of_called"] = float(y[called].mean())

# Sensitivity to the money
sens = {}
for cost, value in [(10, 70), (8, 70), (12, 70), (10, 50), (10, 90)]:
    c, b = evaluate(champ_preds, cost, value), evaluate(base_preds, cost, value)
    sens[f"cost {cost}, value {value}"] = {
        "champion": round(c["profit_per_1000"].mean(), 1), "baseline": round(b["profit_per_1000"].mean(), 1),
        "gain": round(c["profit_per_1000"].mean() - b["profit_per_1000"].mean(), 1),
        "champion_wins_folds": int((c["profit_per_1000"] > b["profit_per_1000"]).sum()),
        "champion_share": round(c["share"].mean(), 3)}

# Share called: per fold, and vs the best share in hindsight on the validation fold
share_check = champ_df[["share", "oracle_share"]].round(3).to_dict("list")

# Calibration (stretch): baseline out-of-fold probabilities near the 14.3% break-even
p_oof = np.concatenate([p for _, _, p, _ in base_preds]); y_oof = np.concatenate([y[t] for t, _, _, _ in base_preds])
band = (p_oof >= 0.12) & (p_oof < 0.17)
# each client is in 4 of the 5 training parts, so this counts client-fold pairs
calibration = {"band": "0.12-0.17", "n_client_fold_pairs": int(band.sum()), "mean_predicted": float(p_oof[band].mean()),
               "actual_rate": float(y_oof[band].mean())}

results["q5_money"] = {"per_10000_clients": business, "call_list_profile": profile,
                       "sensitivity": sens, "share_per_fold": share_check, "calibration_baseline": calibration}
print("\nQ5 per 10,000 clients:", business)
print("call list subscription rate:", round(profile["subscription_rate_of_called"], 3))
print("profile poutcome:", profile["poutcome"]); print("profile contact:", profile["contact"])
print("profile job:", profile["job"]); print("profile age:", profile["age"])
print("sensitivity:"); [print("  ", k, v) for k, v in sens.items()]
print("share per fold:", share_check)
print("calibration (baseline):", calibration)

(OUT / "results.json").write_text(json.dumps(results, indent=2, default=str))
print(f"\nwritten: {OUT / 'results.json'}, {OUT / 'convergence.png'}")
