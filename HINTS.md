# Hints (support track)

Use these when a step is taking much longer than it should. Each hint gives a
starting point, not the whole answer: you still make the decisions.

## Step 2 — the split script

```python
# work/exploration/prepare_split.py   (run from repo root)
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
df = pd.read_csv(ROOT / "data" / "bank_10k.csv")
train, test = train_test_split(df, test_size=0.2, stratify=df["y"], random_state=42)
train.sort_values("contact_order").to_csv(OUT / "train.csv", index=False)
test.sort_values("contact_order").to_csv(OUT / "test.csv", index=False)
meta = {"method": "stratified random", "test_size": 0.2, "seed": 42,
        "n_train": len(train), "n_test": len(test),
        "train_rate": float((train["y"] == "yes").mean()), "test_rate": float((test["y"] == "yes").mean())}
(OUT / "split_metadata.json").write_text(json.dumps(meta, indent=2))
```

Run it once. Never re-run it after you have looked at results.

EDA questions to ask your agent: What share of each column is `unknown`? What
is the subscription rate for `pdays == 999` vs the rest? How do the subscription
rate and `euribor3m` change across `contact_order` (in deciles)? What is the
subscription rate by `poutcome`, `contact`, and `month`?

## Step 4 — a baseline outline

Score the references with the same folds your fitness will use (Step 3), so the
numbers compare:

```python
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_predict

y = (train["y"] == "yes").astype(int).to_numpy()
folds = list(StratifiedKFold(5, shuffle=True, random_state=42).split(train, y))

def profit_per_1000(y_true, call):
    return (70 * y_true[call].sum() - 10 * call.sum()) * 1000 / len(y_true)

def best_call_share(probability, y_true):
    order = np.argsort(-probability, kind="stable")
    profit_of_top_n = 70 * np.cumsum(y_true[order]) - 10 * np.arange(1, len(order) + 1)
    best_n = int(np.argmax(profit_of_top_n)) + 1
    return best_n / len(order) if profit_of_top_n[best_n - 1] > 0 else 0.0

def call_top_share(probability, share):
    call = np.zeros(len(probability), bool)
    call[np.argsort(-probability, kind="stable")[:int(round(share * len(probability)))]] = True
    return call

# call everyone: call = np.ones(len(valid_idx), bool)
# simple rule:   call = (train.iloc[valid_idx]["poutcome"] == "success").to_numpy()
# logistic regression, same rule as the fitness (lr = your sklearn Pipeline):
#   inner = StratifiedKFold(3, shuffle=True, random_state=42)
#   oof = cross_val_predict(lr, x.iloc[train_idx], y[train_idx], cv=inner, method="predict_proba")[:, 1]
#   share = best_call_share(oof, y[train_idx])            # picked on the training part only
#   lr.fit(x.iloc[train_idx], y[train_idx])
#   call = call_top_share(lr.predict_proba(x.iloc[valid_idx])[:, 1], share)
# stretch, break-even rule: call = lr.predict_proba(x.iloc[valid_idx])[:, 1] >= 10 / 70
```

Report the mean and standard deviation over the folds, and the share called.

## Step 5 — a minimal chromosome to start from

Start small, get it running, then add genes. Format (enum genes need
`crossover: {type: error}`):

```yaml
fitness_function:
  type: ExternalFitnessFunction
chromosome:
  type: dict
  generation: {type: per_item, non_required_probability: 0}
  mutation: {type: random, percentage_to_mutate: 0.15, max_percentage_to_mutate: 0.25,
             num_items_to_mutate: 1, max_num_items_to_mutate: 3, drift_factor: 1.1}
  crossover: {type: per_item_crossover, per_item_select_strategy: random}
  content:
    model_family:
      type: enum
      values: [logistic_regression, xgboost]
      generation: {type: uniform}
      mutation: {type: random}
      crossover: {type: error}
    lr_C_exponent:
      type: float
      min_value: -3
      max_value: 2
      generation: {type: uniform}
      mutation: {step_size: 0.2, max_step_size: 0.5, percentage_change: 0, max_magnitude: 0, drift_factor: 1.1}
      crossover: {type: range_uniform}
    xgb_max_depth:
      type: int
      min_value: 2
      max_value: 6
      generation: {type: uniform}
      mutation: {step_size: 1, max_step_size: 2, percentage_change: 0, max_magnitude: 0, drift_factor: 1.1}
      crossover: {type: range_uniform}
    use_economy: {type: bool}
```

Keep the `fitness_function` line at the top. `run_search.py` adds the GA
settings (population, stop rules) for you; you can also add an `ai1` block, as
in an Earth UI export, to set them yourself.

## Step 6 — the profit pieces of the fitness

```python
def campaign_profit(y_true, call):
    return VALUE_PER_SUBSCRIPTION * float(y_true[call].sum()) - COST_PER_CALL * float(call.sum())


def best_call_share(probability, y_true):
    order = np.argsort(-probability, kind="stable")
    profit_of_top_n = VALUE_PER_SUBSCRIPTION * np.cumsum(y_true[order]) - COST_PER_CALL * np.arange(1, len(order) + 1)
    best_n = int(np.argmax(profit_of_top_n)) + 1
    return best_n / len(order) if profit_of_top_n[best_n - 1] > 0 else 0.0
```

`call_list` in the skeleton is already written: it calls `best_call_share` on
the training clients' out-of-fold scores and applies that share to the
validation fold. It takes no genes.

A score that is > 0, roughly between 0 and 1, where higher is better: divide
each fold's profit by the profit of a perfect list on that fold (calling exactly
the subscribers), average over folds, and floor at `ERROR_SCORE`:

```python
# inside the fold loop of _score, after `call = ...`
y_valid = self.y[valid_idx]
perfect = (VALUE_PER_SUBSCRIPTION - COST_PER_CALL) * float(y_valid.sum())
ratios.append(campaign_profit(y_valid, call) / perfect)   # start with ratios = [] before the loop
...
# after the loop
score = float(np.mean(ratios))      # the return line already floors it at ERROR_SCORE
```

A candidate that loses money then scores the floor. Write in `design.md` why
that is acceptable (or not) for your search.

## Step 7 — the F1 run

In your copy `work/runs/run2/fitness.py`, keep everything and change only the
score: compute `f1_score(y_valid, (probability >= 0.5).astype(int))` per fold
and use its mean as `score`. Keep the profit scalars so `compare_runs.py` shows
how much money the F1 champion makes.

## Step 8 — fresh folds

Import your fitness and swap the folds:

```python
import sys; sys.path.insert(0, "work/optimization")
import fitness as F
from sklearn.model_selection import StratifiedKFold

fc = F.FitnessClass("work/exploration")
for seed in [1, 2, 3, 4, 5]:
    fc.folds = list(StratifiedKFold(F.CV_FOLDS, shuffle=True, random_state=seed).split(fc.x, fc.y))
    fc.inner_folds = [  # the inner folds belong to the outer folds: rebuild them too
        [(tr[a], tr[b]) for a, b in StratifiedKFold(F.INNER_FOLDS, shuffle=True, random_state=seed).split(tr, fc.y[tr])]
        for tr, _ in fc.folds
    ]
    print(seed, fc.calculate_fitness(champion_genes).scalars["profit_per_1000_mean"])
```

Do the same for the baseline genes and compare.

## Run size

With population 10 and 5 workers, a generation is 2 rounds of fitness calls,
and each round waits for its slowest call. The inner folds make each call 3–4
times slower than a plain 5-fold CV: on a laptop about 1 s for logistic
regression, 2–4 s for XGBoost and 5–25 s for a random forest. If the slowest
call in a round takes 10 seconds, a generation takes about 20 seconds, and 40
generations about 13–15 minutes, right at the class cap. `check_local.py`
prints this estimate for your own fitness.
