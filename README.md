# Earth Lab 2 — Instant offers on Ames homes

> **Before you start:** read [PROJECT_BRIEF.md](PROJECT_BRIEF.md) (10 minutes). You run the whole
> pathway on a new problem: frame it, look at the data, score the classic approach, let Earth evolve a
> better one, analyse the run, and at the end score your offers on what the 2010 homes really sold for.
> The work is for you: nothing is handed in or graded.
>
> **Time:** 10:40 (after the demo) to 15:30; the steps below take about 3 hours of work, and you may keep going through
> the break. At 15:30 we stop for the course wrap-up. Not finished? Finish after class; the 2010
> prices stay in the repository after the reveal.

## The lab

An iBuyer makes cash offers on listed homes and resells the ones it buys. Offer too much and sellers
accept, and you lose money. Offer too little and nobody sells. The classic data-science answer is: build
the most accurate price model, then subtract one flat margin. Today you test whether Earth can do better
by evolving **the price model and the pricing policy together**, scored directly on risk-adjusted
profit.

You own the decisions. Your coding agent writes code with you; prompts are in
[AGENT_PROMPTS.md](AGENT_PROMPTS.md). Stuck? See [HINTS.md](HINTS.md).

Every step has **Read first**, **Do**, **Deliver** (what must exist under `work/`), and **Done when**.

## Repository

```text
PROJECT_BRIEF.md              The business, the market rule, the decisions you make
EXPERIMENT_ANALYSIS_GUIDE.md  Step 7: how to analyse the Earth run
HINTS.md, AGENT_PROMPTS.md    Support material and prompts for your coding agent
data/                         ames_history.csv (2006-2009, with prices), ames_2010_listings.csv (no prices)
earth/ibuyer_market.py        The market rule (fixed)
earth/classic_baseline.py     Step 3: the classic pipeline
earth/fitness_skeleton.py     Step 5: your fitness starts here
earth/make_offers.py          Step 8: champion -> offers on the 2010 listings
earth/score_2010.py           Step 8: the reveal, once the teacher releases the 2010 prices
earth/                        Earth tools: check_local, validate_chromosome, run_search, fetch_history, compare_runs
context/                      Pathway, methods, chromosome philosophy
work/                         Your work (templates to fill in)
```

## Step 0 — Set up (10 min)

Use your homework environment, on this branch:

```bash
git fetch origin && git checkout s5
source .venv/bin/activate
pip install -r requirements.txt
python earth/check_connection.py
cp data/ames_history.csv work/exploration/train.csv
```

`work/exploration/train.csv` is the file the Earth tools upload. There is no `test.csv` today: the test
is the 2010 listings, and their prices are not in this repository.

**Done when:** the connection check prints `Connection check OK.`

## Step 1 — Frame (15 min)

**Read first:** [PROJECT_BRIEF.md](PROJECT_BRIEF.md).

**Do:** write the business question, the decision, the money (when does one purchase make or lose
money?), why losses count extra, and what success means.

**Deliver:** `work/framing.md`.

**Done when:** success is written as numbers, e.g. "on the 2010 listings, at least $X more risk-adjusted
profit than the classic baseline" (you pick X and say why).

## Step 2 — Data and evaluation (20 min)

**Read first:** [data/data_dictionary.md](data/data_dictionary.md); [context/pathway.md](context/pathway.md).

**Do:**
- Quick EDA on `work/exploration/train.csv`: price by year, by `Overall Qual`, by `Year Built`, by
  neighbourhood. How many homes sell above $300k?
- **Feature boundary:** which columns would you *not* have when a home is listed? Write a reason for each.
- The fitness scores on **three past years**: fit on years before Y, offer on Y (2007, 2008, 2009).
  Write why that is closer to the real question than a random split.

**Deliver:** the feature boundary in `work/framing.md`; the evaluation in `work/design.md`.

**Done when:** someone could explain from `design.md` how a policy is scored, and what the 2010 test is.

## Step 3 — The classic baseline (15 min)

**Do:**

```bash
python earth/classic_baseline.py
```

It picks the most accurate price model (smallest RMSE) on the three past years, then the one flat margin
that makes the most risk-adjusted profit on the same years, and writes `work/baseline/`, including
offers on the 2010 listings.

**Deliver:** the baseline numbers in `work/design.md` (RMSE, best margin, risk-adjusted profit per
listing, share of listings bought), and your answer to **Gate 3**: what is left to gain, and where do
you think the classic approach loses money?

**Done when:** you can say which homes a flat margin treats badly, and why.

## Step 4 — Formulate the search (25 min)

**Read first:** [context/template/CHROMOSOME_PHILOSOPHY.md](context/template/CHROMOSOME_PHILOSOPHY.md);
[earth/context/CHROMOSOME_GUIDE.md](earth/context/CHROMOSOME_GUIDE.md) for YAML syntax.

**Do:** decide what Earth may change, in two parts:
- **Valuation** (given in the skeleton, you choose the ranges): blend weight between ridge and XGBoost,
  ridge strength, XGBoost settings, log price, dropping houses over 4,000 sq ft from training, training
  XGBoost for a lower quantile instead of the mean, feature-group switches.
- **Pricing policy** (you design it): at least a base margin. Then what a smart buyer would add: a margin
  that grows when the two models disagree, margins by quality, age or price tier, when not to offer.

Fixed: the market rule, the three past years, the feature boundary, the $500k cap.

**Deliver:** `work/optimization/formulation.md`: every gene, its range, and why.

**Done when:** for every policy gene you can say which homes it changes the offer for.

## Step 5 — Package and validate (30 min)

**Read first:** [earth/context/GA_CONTRACT.md](earth/context/GA_CONTRACT.md); [HINTS.md](HINTS.md), Step 5.

**Do:**

```bash
cp earth/fitness_skeleton.py work/optimization/fitness.py
```

Write `offer_prices()` (your policy) and the score in `work/optimization/fitness.py`, and
`work/optimization/chromosome.yaml` (the valuation block is in HINTS.md; add your `policy` block). Then:

```bash
python earth/check_local.py
python earth/validate_chromosome.py work/optimization/chromosome.yaml
```

One fitness call fits two models on three years: about 2–4 s on a laptop.

**Deliver:** `fitness.py`, `chromosome.yaml`, the run estimate in `formulation.md`.

**Done when:** both checks pass.

## Step 6 — Run the search (20 min, 15 of them waiting)

**Do:**

```bash
python earth/run_search.py --name run1
```

Defaults for today: population **30**, **15** workers × 1 CPU, 15-minute cap. Don't shrink the
population: with 10 the search stops too early on this many genes (we tested it). While it runs, write
your prediction in `work/run_notes.md`: which policy genes will matter?

If the run is still going after 25 minutes, tell the teacher (Earth's time cap is not always enforced).

**Deliver:** `work/runs/run1/`, a line in `work/run_notes.md`.

**Done when:** the champion is saved and you compared its fitness with the classic baseline's.

## Step 7 — Analyse the run (25 min)

**Read first:** [EXPERIMENT_ANALYSIS_GUIDE.md](EXPERIMENT_ANALYSIS_GUIDE.md), questions 1–4.

```bash
python earth/fetch_history.py --name run1
```

**Deliver:** the analysis sections of `work/delivery/report.md`.

**Done when:** checklist items 1–4 of the guide are ticked.

## Step 8 — Make offers, then the reveal (20 min)

**Do:**

```bash
python earth/make_offers.py --name run1
```

Write your prediction for 2010 in `work/delivery/report.md` first. When the teacher releases the 2010
prices (about 14:50):

```bash
git pull
python earth/score_2010.py
```

It scores your offers and the classic offers on the real 2010 prices with the same market rule. Run it
once: tuning on these numbers would turn the test into training data. We then compare results as a class.

**Deliver:** `work/delivery/report.md`, complete: the 2010 result table, your verdict against the
success criterion, and your answer to: *The champion's price model is about as accurate as the classic
one. Where did the money come from?*

## Troubleshooting

- `Local check FAILED`: read the line above it. Usually a gene in the YAML that the fitness does not
  read (or the reverse), or `offer_prices` still raising `NotImplementedError`.
- Bool genes take no `generation` / `mutation` / `crossover` operators; enum genes need
  `crossover: {type: error}`. The validator says which.
- Fitness score must be finite and > 0 (`max(score, 1e-9)`).
- Your score on Earth can differ from your laptop by about 1% (library versions on the workers).
- `already exists. Pick a new --name`: each run needs its own name.
