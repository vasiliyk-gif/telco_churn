# Report — Term-deposit campaign

## Framing (short)
**Question:** which clients should the bank call in the next term-deposit campaign to make the most profit, and how much more is that than calling everyone or calling only clients whose previous campaign succeeded? **Decision:** before the campaign, each client is called or not; a model ranks clients and the call list is the top share of the ranking. **Target:** `y == "yes"` (~11.3% of contacts). **Money:** €10 per call, €70 per subscription, so a call pays off only above 10/70 = 14.3%; calling everyone loses money. **Success, on the test set, scored once:** more profit per 1,000 clients than calling everyone and than the `poutcome == "success"` rule, and at least **€300 per 1,000** more than the logistic-regression baseline (about 5 extra subscribers per 1,000; smaller gains are within the noise of ~225 test subscribers). Full text: `work/framing.md`.

## Data and split (feature boundary, split decision, what you found over time)
`data/bank_10k.csv`: 10,000 contacts, 21 columns + `y`, no missing values; `unknown` is the dataset's missing value and carries signal, so it stays a category. `pdays = 999` (96.6% of rows) is a code, not a number of days.

**Feature boundary** (only what is known before the campaign starts): in: `age`, `job`, `marital`, `education`, `default`, `housing`, `loan`, `previous`, `poutcome`, `contact` (+ a `pdays != 999` flag as a gene). Out: `duration` (target leakage: known only after the call), `campaign` (counts calls in this campaign), `month` / `day_of_week` (set during the campaign; when to call is out of scope), `pdays` as a number, the five economic columns and `contact_order` (they encode the period, not the client). With a plain LR, adding the economic columns raises 5-fold ROC-AUC from 0.713 to 0.785 and `contact_order` to 0.781: that gain comes from recognising the period, not the client.

**Over time:** strong drift. The subscription rate rises from 3% to 47% across `contact_order` deciles (2008: 68% of rows at 4.5%; 2009: 21%; 2010: 5% of rows at 53%), while euribor falls and the channel moves to cellular.

**Split:** frozen once, stratified random 80/20 on `y`, seed 42: 8,000 train (11.28%) / 2,000 test (11.25%) (`work/exploration/prepare_split.py`, `split_metadata.json`). A random split mixes periods, so all scores are likely optimistic for a future campaign; keeping time columns out limits the damage.

## Evaluation design
(`work/design.md`) 5 stratified folds of `train.csv`, seed 42, shared by all candidates and baselines. In each outer fold, an inner 3-fold CV gives out-of-fold probabilities for the training clients; the most profitable top-N on them becomes the share to call, which is then called from the top of the validation fold. The validation labels only measure profit, never decide how many to call (otherwise the cut-off is tuned on the answers, and Earth would reward the luckiest). **Metric:** mean profit per 1,000 over the 5 folds, with std and share called. **Fitness score:** normalized profit = mean profit / €6,765 (the profit of calling only the subscribers), floored at 1e-9. Before the test read, the champion and LR are re-scored on fresh fold seeds 1–5.

## Baselines (profit per 1,000 clients, share called)
Scored with the design protocol on `train.csv` (`work/baseline/`):

| Reference | Profit per 1,000 | Std | Share called | Score |
|---|---|---|---|---|
| Call everyone | −€2,108 | 21 | 100% | 0 (floor) |
| `poutcome == "success"` | €1,225 | 220 | 3.3% | 0.181 |
| Logistic regression (feature boundary, C = 1) | €1,489 | 231 | 11.8% | 0.220 |

LR beats the rule in all 5 folds but reaches only 22% of the maximum profit. **Gate 3:** an Earth search is justified; it must reach ≥ €1,790 per 1,000 (score ≥ 0.264) to be convincing.

## Formulation (genes and fixed choices)
(`work/optimization/formulation.md`) **7 genes:** `model_family` (logistic regression / XGBoost), `lr_C_exponent` (−3 to 2), `xgb_max_depth` (2–6), `xgb_n_estimators` (50–400), `xgb_learning_rate_exponent` (−2 to −0.5), `class_weight_balanced` (bool), `pdays_flag` (bool). **Fixed:** the money, the call-list rule (how many to call is never a gene), the folds and seed, the feature boundary (no gene for the economic or time columns), `unknown` as a category, the score, and `train.csv` only. One fitness call = 20 model fits; ~0.8 s for LR, ~1.7 s for XGBoost; a run takes ~2–5 minutes.

## Earth runs (ids, settings, champion of run1 and run2)
Both runs: the chromosome in `work/optimization/chromosome.yaml` (7 genes), population 10, 5 workers, 15-minute cap, seed-42 folds. Details in `work/runs/run1/`, `work/runs/run2/`, `work/run_notes.md`.

| Run | Earth experiment | Score used | Stopped | Champion | Profit per 1,000 (seed-42 folds) | Share called |
|---|---|---|---|---|---|---|
| run1 | `hw-run1-1792328099` | profit / 6,765 | gen 20, steady state | XGBoost, depth 6, 152 trees, learning rate 0.019, `pdays` flag on, no class weight | €1,698 ± 248 | 13.0% |
| run2 | `hw-run2-1792332632` | F1 at 0.5 | gen 14 | LR, C = 0.029, `pdays` flag on, no class weight | €1,544 ± 204 | 18.0% |

The profit-fitness champion makes €154 per 1,000 more than the F1 champion and wins all 5 folds. F1 at 0.5 only judges the few clients above 50% (mostly `poutcome = success`), while the money is made by ranking the top 13–18% well; F1 also ignores the costs.

## Analysis (guide questions 1–5)
All numbers on `train.csv` only (`work/analysis/analysis.py`, `work/analysis/results.json`). The local re-score reproduces Earth's champion (€1,697.5) and the Step 4 baseline (€1,488.8) exactly.

### 1. Did the search behave?
![run1 convergence](../analysis/convergence.png)

Healthy shape: the best score jumped from 0.235 to 0.248 in generation 1, made one small step to 0.251 at generation 9, then stayed flat until Earth's steady-state rule stopped the run at generation 20 (2 min 21 s, far below the 15-minute cap, so the run was not cut short). No errors and no floor scores in 210 candidates. The population mean rose from 0.211 to ~0.23–0.24 and stayed below the best, so the population kept some diversity. The best never approached the target (0.264).

### 2. Is the champion clearly best, or one of a crowd?
One of a crowd. The top 10 distinct candidates are within €33 per 1,000 of the champion, far less than the fold std (~€250): they are a tie.

| # | Score | Profit per 1,000 | Std | Share called | Family | Depth | Trees | Learning rate | Class weight | `pdays` flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.251 | 1,697.5 | 248 | 13.0% | XGBoost | 6 | 152 | 0.019 | no | yes |
| 2 | 0.250 | 1,692.5 | 225 | 13.0% | XGBoost | 6 | 152 | 0.018 | no | yes |
| 3 | 0.249 | 1,682.5 | 228 | 13.2% | XGBoost | 6 | 151 | 0.019 | no | yes |
| 4 | 0.248 | 1,680.0 | 213 | 13.0% | XGBoost | 6 | 162 | 0.014 | no | yes |
| 5 | 0.248 | 1,678.8 | 221 | 13.5% | XGBoost | 6 | 163 | 0.014 | no | yes |

Gap from the champion: #2 €5, #5 €19, #10 €33. All ten agree on XGBoost, no class weight, `pdays` flag on, depth 5–6, ~150–160 trees and a small learning rate (0.014–0.019). That agreement is what the search learned; the exact values inside it did not matter. Per fold, the champion beats LR in 4 of 5 folds (+225, −56, +244, +575, +56).

### 3. Which decisions mattered?
Gene shifts, first 3 vs last 3 generations: `model_family` XGBoost 50% → 67%; `xgb_max_depth` = 6 from 27% → 63%; `class_weight_balanced` = false from 50% → 77%; `pdays_flag` unchanged (67% on). `lr_C_exponent` only matters for LR candidates, so its values in the XGBoost winners are hitchhikers.

One-flip checks (champion, seed-42 folds, change in profit per 1,000):

| Change | Profit per 1,000 | Change |
|---|---|---|
| champion | 1,697.5 | — |
| model family → LR (C = 1) | 1,481.2 | −216 |
| class weight on | 1,558.8 | −139 |
| `pdays` flag off | 1,585.0 | −113 |
| depth 6 → 8 (outside the range) | 1,587.5 | −110 |
| depth 6 → 4 | 1,658.8 | −39 |

The genes that mattered most: **model family** (XGBoost over LR, −€216 when switched), **class weight off** (−€139 when on: upweighting subscribers spoils the ranking at the top of the list), and the **`pdays` flag** (−€113 when off, even though it mostly repeats `poutcome`). Depth matters less: 6 sits at the top of the range, but 8 is clearly worse, so the range limit did not hold the search back.

### 4. How optimistic is the search score?
Re-scored with the same fitness on fresh fold seeds 1–5 (outer and inner folds both re-drawn):

| | Search (seed 42) | Fresh seeds 1–5 (mean) | Per seed |
|---|---|---|---|
| Champion | €1,697.5 | €1,721.2 | 1,689 / 1,699 / 1,739 / 1,716 / 1,764 |
| LR baseline | €1,488.8 | €1,542.8 | 1,546 / 1,574 / 1,576 / 1,515 / 1,503 |
| Gain | €208.8 | **€178.5** | +143 / +125 / +163 / +201 / +261 |

No sign of search optimism: the champion does not drop on fresh folds (the seed-42 folds were a little harder than average for both models). The gain over LR is real (positive on every seed, spread ~€50) but smaller on fresh folds, **€179 per 1,000, below the €300 success margin**.

### 5. What is it worth, and how sure are we about the money?
Per 10,000 clients (seed-42 validation folds, scaled):

| Policy | Calls | Subscriptions | Profit |
|---|---|---|---|
| Call everyone | 10,000 | 1,128 | −€21,075 |
| LR baseline | 1,180 | 381 | €14,888 |
| Champion | 1,295 | 428 | €16,975 |

**The call list.** The champion calls 13% of clients, of whom 33% subscribe (base rate 11.3%). Compared with all clients, the list is 97% cellular (vs 63%), 26% previous-campaign success (vs 3%), over-weights students (11% vs 2%) and retired clients (18% vs 4%), and takes the young (≤30: 38% vs 18%) and the old (51+: 43% vs 18%), the U-shape in age that LR cannot model. A marketing manager would recognise this list.

**Sensitivity to the money** (same models, share re-picked on the training part):

| Cost per call, value per subscription | Champion | Baseline | Gain | Folds won | Share called |
|---|---|---|---|---|---|
| €10, €70 (base) | 1,698 | 1,489 | +209 | 4/5 | 13% |
| €8, €70 | 2,072 | 1,970 | +101 | 3/5 | 30% |
| €12, €70 | 1,419 | 1,362 | +57 | 3/5 | 11% |
| €10, €50 | 906 | 898 | +9 | 3/5 | 9% |
| €10, €90 | 2,789 | 2,654 | +135 | 2/5 | 40% |

The champion stays ahead of the baseline in every scenario, but the gain shrinks to almost nothing at €50 per subscription and is never above the base case. The share to call moves a lot with the money (9% to 40%), because the profit curve is flat around its maximum.

**The share called** per fold (picked on the training part): 15.4%, 13.0%, 9.6%, 14.8%, 12.0%; the share that would have been best in hindsight on each validation fold: 9.3%, 9.4%, 10.2%, 14.8%, 14.2%. The rule is in the right range but misses by up to 6 points on single folds, which is part of the fold-to-fold noise.

**Calibration (stretch).** Among baseline out-of-fold scores between 12% and 17% (mean predicted 14.1%), 13.0% actually subscribe: close, slightly over-confident. A fixed 14.3% cut-off would be roughly in the right place for the baseline, but picking the share on the training folds does not depend on it.

**Robustness, in one sentence:** the champion's lead over logistic regression is consistent (every fresh seed, every money scenario) but modest, €179 per 1,000 on fresh folds, below the €300 bar set in framing, and it shrinks when a subscription is worth less.

## Test read (one table: call everyone, simple rule, baseline, champion)
`test.csv` read once (`work/delivery/test_read.py`, `work/delivery/test_results.json`): 2,000 clients, 225 subscribers (11.25%). For each model, the share was picked on all of `train.csv` (3-fold out-of-fold scores), the model fitted on all of `train.csv`, and that share called from the top of `test.csv`.

| Policy | Profit per 1,000 | Share called | Calls | Subscribers called | Rate among called |
|---|---|---|---|---|---|
| Call everyone | −€2,125 | 100% | 2,000 | 225 | 11.3% |
| `poutcome == "success"` | €900 | 2.6% | 51 | 33 | 64.7% |
| **LR baseline** | **€1,760** | 8.0% | 159 | 73 | 45.9% |
| Earth champion (run1, profit fitness) | €1,725 | 20.2% | 404 | 107 | 26.5% |
| F1 champion (run2) | €1,675 | 13.0% | 260 | 85 | 32.7% |

**Three numbers for the champion vs LR:** search folds +€209, fresh folds +€179, test **−€35** per 1,000.
- *Search vs fresh:* the fresh folds showed no search optimism in the champion's own profit, but its lead shrank a little.
- *Fresh vs test:* the main difference is how many clients were called. Picked on all of `train.csv`, the champion's share came out at **20%** (vs ~13% in the folds) and LR's at **8%** (vs ~12%). The champion's extra 245 calls beyond LR's 159 found 34 subscribers, 13.9%, just under the 14.3% break-even, so they cost a little money. Step 8 had warned that the profit curve is flat near its peak, so the chosen share moves a lot between samples.
- *Noise:* with 225 subscribers, a handful more or fewer moves profit by a few hundred euros per 1,000; −€35 is a tie, not evidence that LR is better. It is clearly not the +€300 required.
- *Profit vs F1:* the profit-fitness champion made more money on test than the F1 champion (€1,725 vs €1,675), the same order as on the validation folds.

## Verdict against the success criterion
_(Draft — the verdict is the student's decision; edit before submitting.)_

| Criterion (framing) | Test result | Met? |
|---|---|---|
| More profit than calling everyone | €1,725 vs −€2,125 | ✅ |
| More profit than the `poutcome == "success"` rule | €1,725 vs €900 | ✅ |
| At least €300 per 1,000 more than the LR baseline | €1,725 vs €1,760 (−€35) | ❌ |

**Keep the logistic-regression baseline; do not adopt the Earth champion.** The champion's edge was real but modest on `train.csv` (+€179 on fresh folds, every seed positive), always below the €300 bar, and it disappeared on the test set. LR is simpler, easier to explain and calls fewer clients (8% vs 20%) for the same money. Either model is far better than the bank's current options: calling the LR list instead of using the `poutcome` rule earns about €860 more per 1,000 clients, and calling everyone loses money. Caveat for both: the random split mixes 2008–2010, so the next campaign may look different from these numbers.

## What would you let Earth evolve in your next experiment, and why?
_(Draft — edit in your own words.)_
- **Fix the weak spot that cost the champion on test: how many to call.** Keep it out of the chromosome (it must not be tuned on validation labels), but make the share more stable, for example by averaging the share over repeated inner splits, or by picking it from a smoothed profit curve. Then score candidates on profit *including* that instability.
- **Give LR what XGBoost found:** genes for binning `age` (the U-shape) and for a few interactions (`job` × `contact`, `poutcome` × `contact`). If a regularized LR with these features matches XGBoost, the bank gets the simpler model.
- **Control XGBoost overfitting with only ~900 positives:** `min_child_weight`, `subsample`, `colsample_bytree`; depth above 6 was already worse.
- **Make the search score harder to fool:** score each candidate on two fold seeds, or on mean − std, so the winner is the one that is good on many splits, not only on seed 42.
- **Not the economic or time columns:** they would raise the score on this random split by recognising the period, not the client, and would not help choose whom to call in the next campaign.
