# Experiment analysis guide (final stage)

You have a champion. This guide is how you decide whether to believe it, what it
learned, and what it is worth to the business. Work through the six questions in
order; each one ends with something to write in `work/delivery/report.md`.

Use the Earth UI plots, your saved runs under `work/runs/`, and local re-scoring
with your own `fitness.py`. Never use `test.csv` before question 6.

## Where the evidence lives

| Evidence | Where |
|----------|-------|
| Every candidate of every generation: score, how it was made (crossover, mutation, elite, drift), parents, genes, scalars | `python earth/fetch_history.py --name run1` → `work/runs/run1/history.csv` |
| Best and mean score per generation, error count, gene shifts, top 5 | Printed by `fetch_history.py`; plots in the Earth UI |
| Champion, scalars, settings | `work/runs/<name>/champion_chromosome.json`, `earth_ids.json` |
| Champion vs other runs | `python earth/compare_runs.py run1 run2` |

`fetch_history.py` is read-only. It calls
`GET /api/experiments/{experiment_id}/{generation}/population` for every
generation, so the whole run is in one table you can analyse with pandas or
your agent.

---

## 1. Did the search behave?

Look at best and mean fitness per generation.

- **Shape:** a fast rise in the first generations, then a plateau, is healthy.
  A best score that never moves after generation 0 means the space was too easy,
  or the fitness cannot tell candidates apart.
- **Why it stopped:** stagnation, steady state, or the time cap
  (`status`, `generation` in the champion file). A time-cap stop while the best
  was still rising means the run was cut short.
- **Gap between best and mean:** a population that is mostly far below the best
  is still exploring; a population that has collapsed onto the best has lost
  diversity (drift helps here).
- **Errors and floor scores:** `fetch_history.py` counts both. *Errors* are
  candidates your fitness could not score (a gene combination it cannot
  handle): fix them. *Floor* scores are candidates that lose money if your score
  floors losses at 1e-9: expected now and then, but if many candidates sit at
  the floor, the search space contains a lot of money-losing candidates.

*Write:* one sentence on convergence and the stop reason, with the plot.

## 2. Is the champion clearly best, or one of a crowd?

Take the final generation's population and rank it by score.

- How far is the champion from number 2, 5, and 10? If ten candidates are within
  one fold-standard-deviation of the champion, they are a tie.
- Do the near-ties share a model family, a feature group, a class weight?
  What they share is what the search actually learned; where they differ did
  not matter.
- Per-fold scores: does the champion win on every fold, or on one lucky fold?

*Write:* the top 5 as a table (score, std, family, share called, feature groups), and
which choices they agree on.

## 3. Which decisions mattered?

Use the gene distributions printed by `fetch_history.py` (first vs last
generations), or compute them from `history.csv`.

- A gene whose values concentrated (e.g. `model_family` → almost all xgboost,
  economy group → always on) may have mattered for the fitness.
- **Hitchhikers:** a gene can concentrate without mattering. If xgboost took
  over, the random-forest and logistic-regression genes are ignored by the
  fitness, yet they still converge because they ride along in the winners'
  chromosomes. Only count a gene as important if it is active for the winning
  family.
- A gene that stayed spread out did not matter, or the run was too short to
  tell.
- Check one thing by hand: re-score the champion locally with one gene flipped
  (e.g. economy off, or `pdays` handling switched). How much profit moves?

*Write:* the 2–3 genes that mattered most, with the one-flip check.

## 4. How optimistic is the search score?

Earth picked the best of hundreds of candidates on the same five folds, so its
score flatters the champion.

- Re-score the champion and the logistic-regression baseline locally on new fold
  seeds (e.g. 1, 2, 3, 4, 5): same fitness, only the seed changes.
- Report both means and the drop from the search score.
- If the champion's advantage over the baseline shrinks to less than a fold
  standard deviation, say so: the search did not find a real improvement.

*Write:* search score vs fresh-seed score for champion and baseline.

## 5. What is it worth, and how sure are we about the money?

- **Profit per campaign:** turn the per-1,000 profit into the bank's terms (e.g.
  per 10,000 clients), with the number of calls made and subscriptions won.
- **The call list:** what share of clients does the champion call? Who are they
  (previous success, cellular, month, age)? Does the list look sensible to a
  marketing manager?
- **Sensitivity:** recompute profit at €8 and €12 per call, and €50 and €90 per
  subscription. Does the champion still beat the baseline? Does the best number
  of calls move?
- **The share called:** the fitness picks it on each training fold. How much
  does it vary between folds, and how close is it to the share that would have
  been best on the validation fold?
- **Calibration (stretch):** the break-even rule calls everyone above 14%.
  Among clients the baseline scores around 14%, do about 14% subscribe? If
  not, a fixed cut-off would be in the wrong place, which is one reason the
  fitness picks a share on the training folds instead.

*Write:* a profit table and one sentence on how robust the ranking is to the
money assumptions.

## 6. One test read, then the verdict

Only now: for the baseline and the champion, pick the share to call on all of
`train.csv` (3-fold out-of-fold scores, as in the fitness), fit on all of
`train.csv`, and call that share of `test.csv`. Then score all four policies
(call everyone, the simple rule, the baseline, the champion) **once** on
`test.csv`.

- Search score, fresh-seed score, and test profit are three different numbers.
  Explain the differences.
- Compare against the success criterion from framing. Did the champion meet it?
- If you compared fitness functions (profit vs F1), which champion made more
  money on test?

*Write:* the verdict (adopt the champion, or keep the baseline) and the answer
to: *"What would you let Earth evolve in your next experiment, and why?"*

---

## Checklist

- [ ] Convergence plot and stop reason
- [ ] Top-5 table and what the near-ties share
- [ ] Genes that mattered, with a one-flip check
- [ ] Fresh-seed re-score: champion vs baseline
- [ ] Profit in business terms, call-list profile, money sensitivity
- [ ] One test read, verdict, next-experiment answer
