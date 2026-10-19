# Prompts for your coding agent (Lab 2)

Copy, paste, adapt. You make the decisions; the agent writes code and explains. Read what it does
before you accept it.

## Step 1 — Frame

> Read PROJECT_BRIEF.md and earth/ibuyer_market.py. Ask me, one at a time, the questions I need to
> answer in work/framing.md. Don't answer them for me.

> With the market rule in earth/ibuyer_market.py: if my offer is 90% of a home's true value, what is
> the chance the seller accepts, and what do I make if they do? And at 97%?

## Step 2 — Data and evaluation

> Write a short EDA script for work/exploration/train.csv (read it with keep_default_na=False,
> na_values=[""]). Show the median SalePrice by Yr Sold, by Overall Qual and by decade of Year Built,
> with the 10th and 90th percentiles, and the count of homes above $300k.

> Which columns in data/data_dictionary.md would a buyer not know when a home is listed? List them with
> the reason; I'll decide.

## Step 3 — Baseline

> Run python earth/classic_baseline.py and explain the margin curve it prints. Then, using the same
> folds, show me where the classic model's errors are largest: by Overall Qual, by Year Built decade, by
> predicted price tier.

## Step 4 — Formulate

> Here is my pricing policy idea: <paste>. For each gene, tell me which homes it changes the offer for,
> and whether two of my genes could cancel each other out.

## Step 5 — Package

> Copy earth/fitness_skeleton.py to work/optimization/fitness.py. Implement offer_prices() from my
> formulation in work/optimization/formulation.md, and the score as (risk_adj + 3000) / 6000. Then write
> work/optimization/chromosome.yaml with the valuation block from HINTS.md and my policy block. Run
> python earth/check_local.py and python earth/validate_chromosome.py work/optimization/chromosome.yaml
> and fix what fails.

## Step 6 — Run

> Run python earth/run_search.py --name run1 and summarise the champion: fitness, risk-adjusted profit
> per listing, share bought, per-year values, and how that compares with work/baseline/classic_metrics.json.

## Step 7 — Analyse

> Run python earth/fetch_history.py --name run1, then follow EXPERIMENT_ANALYSIS_GUIDE.md questions 1–4
> with me. Show the evidence for each answer; I write the conclusions.

## Step 8 — Offers

> Run python earth/make_offers.py --name run1. Compare its offers with work/baseline/offers_2010_classic.csv:
> on which listings do the two differ most, and why (look at the champion's policy genes)?
