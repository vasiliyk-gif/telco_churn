# Evaluation design (Steps 2–3)

## How a candidate is scored (years, what is fit where, what is offered on)

A candidate is a value model plus a pricing policy. It is scored on three past years, each one an
expanding window over `work/exploration/train.csv`:

| Fold | Fit the value model on | Make offers on |
|------|------------------------|----------------|
| Y = 2007 | 625 sales of 2006 | 694 sales of 2007 |
| Y = 2008 | 1,319 sales of 2006–2007 | 622 sales of 2008 |
| Y = 2009 | 1,941 sales of 2006–2008 | 648 sales of 2009 |

In each fold the model predicts the value of every home in year Y, the policy turns that into an offer
(or no offer), and the market rule (`earth/ibuyer_market.py`) gives the expected profit and losses using
the real `SalePrice` as the true value. The three folds are added up: 1,964 offers in total. Features are
the columns inside the feature boundary (`work/framing.md`); `Yr Sold` is used only to split the folds.


## Why past years and not a random split

- **It is the real question.** In early 2010 we have sales up to 2009 and must price homes we have never
  seen, later in time. Fitting on earlier years and offering on a later one is the same situation, three
  times over.
- **A random split leaks the future.** It trains on 2009 sales to price 2007 homes, so the model sees
  prices from after the offer date, including neighbours sold later and market moves we could not know.
  The error it reports would be too optimistic.
- **The housing mix changes year to year.** New homes (`Partial` sales) fell from about 90 a year in
  2006–07 to about 28 in 2008–09. A forward split tests whether the model and policy still work when the
  mix shifts, which a random split hides by mixing the years.
- **Three years, not one,** so a policy that only works in one market (for example 2007, before the
  crash) does not win. Prices were flat (medians $160–165k), so the main risk is the mix, not inflation.

Cost: the 2007 fold trains on one year only (625 sales), so it is harder than the others. That is
fine: it is the same handicap for every candidate.


## The 2010 test: what it is, who scores it

The 341 homes listed in Ames from January to July 2010 (`data/ames_2010_listings.csv`), with features
and `ListingID` but no price. The final champion and the classic baseline each make one offer (or none)
per listing, trained on all of 2006–2009. The teacher holds the 2010 sale prices and releases them at
the end of the lab; we then score both sets of offers once with `earth/score_2010.py`, under the same
market rule. Nothing is tuned on 2010: it is the only result that was never seen during the search.


## The score (Step 5): risk-adjusted dollars per listing -> fitness


## Classic baseline (Step 3): value model, RMSE, best flat margin, risk-adjusted profit per listing, share bought

`python3 earth/classic_baseline.py` → `work/baseline/classic_metrics.json`, `offers_2010_classic.csv`.

| Item | Value |
|------|-------|
| Most accurate value model | XGBoost, depth 4, 700 trees, learning rate 0.03, log price, all feature groups |
| RMSE / MAPE on 2007–2009 | **$26,954** / 8.7% (best ridge: $33,266; log-price ridge breaks down at $65,843) |
| Best flat margin | **18%** (searched 0–30% in steps of 1%) |
| Risk-adjusted profit per listing | **−$160** (profit $547, losses −$1,416) |
| Share of listings bought | 23% |
| Per year | 2007: −$593, 2008: −$25, 2009: +$173 |
| For comparison: flat 10% | −$2,782 per listing, buys 55% |
| Fitness of the baseline | 0.4733 (break-even = 0.5) |

The classic approach **loses money** on the past years, even with the margin tuned on them. No flat margin
in 0–30% is positive.


## Gate 3: what is left to gain, and where does a flat margin lose money?

Breakdown per home: `python3 work/baseline/gate3_segments.py` (writes `work/baseline/gate3_homes.csv`).

**Where it loses.** All the losses come from homes the model **overvalues by more than 10%** (286 homes:
−$1.76M). Undervalued homes cost nothing, they are just refused. A flat margin cannot tell these apart, so
the policy has to find *signals* of overvaluation:

| Segment | Homes | Risk-adj. total | Note |
|---------|-------|-----------------|------|
| `Overall Qual` = 10 | 25 | **−$1.23M** | Three huge new homes in Edwards (4,676–5,642 sq ft, partial sales) were valued at $520–550k and sold for $150–185k: **−$1.22M, i.e. −$624 per listing on their own** |
| Predicted value > $300k | 167 | −$1.47M | Few training homes, offers near the $500k cap |
| Top 20% ridge/xgb disagreement (> 8%) | 393 | −$1.73M | The other four quintiles are all positive (+$1.4M together) |
| Built before 1920 | 157 | −$0.38M | Old homes, wide spread |
| `Overall Qual` ≤ 4 | 178 | −$0.42M | Cheap homes, few sales |
| Neighbourhoods | | Edwards −$1.27M, OldTown −$0.30M, IDOTRR −$0.20M | |

**Where it earns.** Quality 5–8, built 1970–2000, predicted $100–300k, low model disagreement: these are
all positive (quality 6–7 alone: +$1.09M).

**What is left to gain.** 148 of the 1,964 past-year homes lose money in expectation; they cost $2,123 per
listing. With the same model and offers, skipping exactly those would score **+$1,963 per listing**, about
$2,100 above the baseline. A real policy cannot find all of them, but model disagreement, price tier and
quality pick out most of the losses. Gate 3: **yes, there is enough to gain to justify the search.**

**Caveat for 2010.** The 2010 listings have **no** homes over 4,000 sq ft and no quality-10 homes. On the
past years, simply not buying those three Edwards homes is worth about +$624 per listing; on 2010 it is
worth nothing. So part of any past-year gain over the baseline will not show up in 2010. Earth will
find a gene that avoids them, so I will compare the champion and the baseline on the past years with and
without those homes, and I keep the success threshold at **+$1,000 per listing on 2010** (set in Step 1,
before these numbers).

