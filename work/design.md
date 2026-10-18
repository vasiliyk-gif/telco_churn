# Evaluation design (Step 3)

Everything below uses `work/exploration/train.csv` only (8,000 contacts, 11.3% subscribers). `test.csv` is not read until Step 9.

## Cross-validation scheme (folds, seed)
- 5 outer folds: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` on `train.csv`, stratified on `y`. Each fold: ~6,400 training clients, ~1,600 validation clients (~180 subscribers).
- Stratified because only 11% of rows are positive: every validation fold gets about the same subscription rate.
- Inside each outer fold, the training part is split again into 3 inner folds: `StratifiedKFold(n_splits=3, shuffle=True, random_state=42)`. The validation part is never split.
- All 5 outer and 15 inner splits are created once and reused for every candidate model and for the three baselines, so all scores compare on the same rows.
- Cost: 5 × (3 inner fits + 1 refit) = 20 model fits per candidate.

## From probabilities to a call list (how the share to call is picked on the training folds)
The model gives each client a probability of subscribing. We call the clients with the highest probabilities. How many to call is decided on the training part of each outer fold only:

1. Train on 2 inner folds and predict the third, three times, so each of the ~6,400 training clients gets a probability from a model that did not see them (out-of-fold probabilities).
2. Sort the training clients by that probability, highest first (stable sort). For every N = 1, 2, …, compute the profit of calling the top N: €70 × subscribers among them − €10 × N.
3. Take the N with the highest profit and turn it into a share: share = N / number of training clients. If no N makes a profit, share = 0 (call nobody).
4. Train the model on the whole training part, predict the validation fold, and call the top round(share × fold size) clients.

The validation labels are used only to compute the fold's profit, never to choose how many to call. Each outer fold gets its own share; the mean of the 5 is reported as "share called".

## Profit per fold and the score
- Profit on a validation fold, per 1,000 clients: (70 × subscribers called − 10 × calls made) × 1000 / fold size.
- The metric is the mean of the 5 fold profits. Reported with it: the standard deviation over the folds, the 5 per-fold profits, and the mean share called.
- Fitness score (Earth needs a score > 0, higher is better, roughly 0–1):
  `score = mean profit per 1,000 / 6,765`, floored at `1e-9`.
  6,765 is the best possible profit per 1,000: calling only the subscribers, 0.11275 × 1000 × (€70 − €10). So the score is "share of the perfect campaign's profit". It is a fixed constant, so the ranking of candidates is the same as ranking by mean profit.
- A mean profit of 0 or below (no better than calling nobody) gets the floor. Earth cannot tell those candidates apart, which is fine: none of them is worth using.
- I use the mean, not mean − std: the std is reported and checked separately (Gate 3, fresh folds), and a simple score is easier to explain.

## Why the validation fold must not decide how many to call
The validation fold stands in for clients we have not called yet. In a real campaign the call list is fixed before anyone answers, so the share has to be chosen without the outcomes. If we picked N by looking at the validation labels, we would be choosing the best cut-off with the answers in hand: the profit would be too high. Earth makes this worse: it scores thousands of candidates, and it would reward the ones whose cut-off happened to fit those 1,600 labels by luck. The training part's in-sample probabilities can't be used either (a model scoring rows it learned from is overconfident), which is why the share comes from the inner 3-fold out-of-fold probabilities.

## Fresh-fold check before the test read
In Step 8, before Step 9:
- Re-score the Earth champion and the logistic-regression baseline with exactly this protocol, but with 5 new seeds (1, 2, 3, 4, 5) for both the outer and the inner folds.
- Compare, for each model: mean profit on the search folds (seed 42) vs mean profit on the fresh folds.
- The search picked the champion as the best of many on seed 42, so its seed-42 score is optimistic. If its lead over logistic regression on fresh folds falls below €300 per 1,000 (the success margin in `framing.md`), the gain is not convincing.
- Only after this check is the champion scored once on `test.csv`.

## Gate 3 (Step 4): does the baseline justify an Earth search? What gain would convince you?
Baselines scored with this protocol on `train.csv` (`work/baseline/baselines.py`, `work/baseline/metrics.json`):

| Reference | Profit per 1,000 (mean) | Std over folds | Share called | Score |
|---|---|---|---|---|
| Call everyone | −€2,108 | €21 | 100% | 0.000 (floor) |
| `poutcome == "success"` | +€1,225 | €220 | 3.3% | 0.181 |
| Logistic regression (feature boundary, no tuning) | +€1,489 | €231 | 11.8% | 0.220 |

- **LR beats both simple references.** It makes €264 per 1,000 more than the `poutcome` rule and wins in all 5 folds (per-fold gain +269, +281, +69, +338, +363).
- **Noise.** Each model's std is ~€230, but most of it is the same folds being easy or hard for every model. Paired on the same fold, LR's gain over the rule varies by only ~€100 (std). So candidates must be compared fold by fold, on the same folds, not by overlapping ± ranges.
- **Room to gain.** LR earns 22% of the perfect campaign (€1,489 of €6,765). It is linear on a small feature set, and the EDA shows signals a linear model misses (`age` is U-shaped; possible interactions such as job × contact). A more flexible model family, class weights and feature handling are what Earth can explore.
- **The margin stays at €300 per 1,000.** It is above LR's fold std (€231) and about 3× the paired fold-to-fold spread (~€100), so a gain of that size is unlikely to be luck. In score terms: the champion must reach at least €1,790 per 1,000, a score ≥ 0.264, on these folds, and keep a lead of at least €300 over LR on the fresh folds (see above).
- **Verdict: the Earth search is justified.** The baseline is clearly better than the simple rule but far from the ceiling. A champion below €1,790 per 1,000, or one whose lead disappears on fresh folds, means logistic regression stays the recommendation.
