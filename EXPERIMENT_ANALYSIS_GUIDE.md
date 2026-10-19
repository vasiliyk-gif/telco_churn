# Experiment analysis guide (Lab 2)

You have a champion. This guide is how you decide whether to believe it, what it learned, and what it
is worth. Work through the four questions in order; each one ends with something to write in
`work/delivery/report.md`. The fifth number, the 2010 result, comes at the end of Step 8.

## Where the evidence lives

| Evidence | Where |
|----------|-------|
| Every candidate of every generation: score, how it was made, parents, genes, scalars | `python earth/fetch_history.py --name run1` → `work/runs/run1/history.csv` |
| Best and mean score per generation, gene shifts, top 5 | Printed by `fetch_history.py`; plots in the Earth UI |
| Champion, scalars, settings | `work/runs/run1/champion_chromosome.json`, `earth_ids.json` |
| The classic baseline | `work/baseline/classic_metrics.json` |

## 1. Did the search behave?

- **Shape:** a fast rise, then a plateau, is healthy. A best score that never moves means the fitness
  cannot tell candidates apart.
- **Why it stopped:** steady state (no gain over the look-back window), stagnation, or the time cap.
- **Floor scores:** candidates at 1e-9 lose so much that the score floors. A few are normal; many mean
  your policy ranges allow silly policies (margins that always lose).

*Write:* one sentence on convergence and the stop reason.

## 2. Is the champion clearly best, or one of a crowd?

- Rank the last generation. How far is the champion from numbers 2, 5 and 10?
- Do the near-ties share a policy shape (similar base margin, same segments getting extra margin)?
  What they share is what the search learned.
- Per year: does the champion beat the classic baseline in 2007, 2008 **and** 2009, or only in one?

*Write:* the top 5 (score, base margin, the segment genes, share bought) and what they agree on.

## 3. Which decisions mattered?

- Gene shifts from the first to the last generations: which policy genes moved, and which stayed spread
  out?
- **Hitchhikers:** if the blend weight `w_xgb` went to almost 0, the XGBoost hyperparameters hardly
  matter for the price itself, yet they still converge. They may still matter through the disagreement
  signal. Check before you claim it.
- **One-flip checks:** re-score the champion locally with one idea switched off (HINTS.md, Step 7):
  set `k_disagree` to 0, set the segment adjustments to 0, or set `w_xgb` to 1. How much risk-adjusted
  profit per listing does each idea earn?

*Write:* the 2–3 ideas that earned the most, with the one-flip numbers.

## 4. Where does the money come from?

- Compare the champion with the classic baseline on the three past years: profit, losses, share bought.
  Is the gain from buying more good homes, or from avoiding bad ones?
- Value accuracy: compute the champion's MAPE on the three years and the classic model's. If they are
  close, the gain is in the decisions, not in the predictions.
- Which homes does the champion treat differently from a flat margin? Describe them like a buyer would
  ("we bid lower on pre-1950 homes because...").

*Write:* a short table (classic vs champion: profit, losses, share bought, MAPE) and two sentences a
business owner would understand.

## 5. The reveal (Step 8)

`earth/score_2010.py` scores your offers and the classic offers on the real 2010 prices. Before you run it,
write your prediction. Afterwards: the past-years score, the 2010 result, and the class spread are
three different numbers. Explain them. 2010 prices fell a little compared with 2009: what does that do
to every offer policy?

## Checklist

- [ ] Convergence and stop reason
- [ ] Top 5 and what the near-ties share
- [ ] Ideas that mattered, with one-flip numbers
- [ ] Classic vs champion: where the money comes from
- [ ] Prediction written before the reveal; reveal explained
