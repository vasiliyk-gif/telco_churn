# Earth DS Homework — Term-deposit phone campaign

> **Before you start:** read [PROJECT_BRIEF.md](PROJECT_BRIEF.md) (10 minutes),
> then do Step 0. Budget: about 8 hours for the core track, 1–2 more for stretch
> items.

## The homework

A bank calls clients to sell term deposits. A call costs €10; a subscription
earns €70. Only about 1 call in 9 succeeds, so calling everyone loses money.
You will walk the whole pathway on this new problem: frame it, explore the
data, design the evaluation, build baselines, formulate an Earth search, run
it through the API, analyse the experiment, and read the test set once.

You own the decisions. Your coding agent writes code with you; prompts are in
[AGENT_PROMPTS.md](AGENT_PROMPTS.md). Stuck? See [HINTS.md](HINTS.md).

Every step below has:
- **Read first:** the document to read before you start the step.
- **Do:** the work.
- **Deliver:** what must exist under `work/` when you finish.
- **Done when:** the check that ends the step.
- **Stretch:** an extra for when you have time. Optional.

## Repository

```text
PROJECT_BRIEF.md              Business frame, money, the framing questions
EXPERIMENT_ANALYSIS_GUIDE.md  Step 8: how to analyse an Earth experiment
HINTS.md                      Support material if you get stuck
AGENT_PROMPTS.md              Prompts for your coding agent, per step
data/                         bank_10k.csv, data_dictionary.md, bank-additional-names.txt
context/pathway.md            Phases, practices, the two rules, split vocabulary
context/methods/              Practices one-pager, tabular EDA and split guidelines
context/template/             Chromosome philosophy, invariants, constraints, gene menu
earth/                        Earth client and tools, fitness_skeleton.py
work/                         Your work (templates to fill in)
```

## Step 0 — Set up

You need Python 3.12 and your Earth login.

```bash
git clone --branch hw-v1 --single-branch https://github.com/vasiliyk-gif/telco_churn.git earth_hw
cd earth_hw
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your Earth user and password in `.env` (`EARTH_USER` / `EARTH_PASS`). Never
commit `.env`. On Windows: `.venv\Scripts\activate` and `copy .env.example .env`.

```bash
python earth/check_connection.py
```

**Done when:** the connection check prints `Connection check OK.`

## Step 1 — Frame

**Read first:** [PROJECT_BRIEF.md](PROJECT_BRIEF.md);
[practices one-pager](context/methods/PROJECT_DELIVERY_PRACTICES_ONE_PAGER.md), Frame phase.

**Do:** in your own words, write the business question, the decision, the
target, the unit of analysis, the money, and what success means.

**Deliver:** `work/framing.md`.

**Done when:** success is written as numbers. For example: on the test set the
champion makes more profit than calling everyone and the simple rule, and at
least €X per 1,000 clients more than the logistic-regression baseline (you pick
X and say why).

## Step 2 — Explore and freeze the split

**Read first:** [TABULAR_EDA_AND_SPLIT_GUIDELINES.md](context/methods/TABULAR_EDA_AND_SPLIT_GUIDELINES.md)
§3.5–3.7 and §4.4, §4.8, and the hand-off checklist at the end;
[data/data_dictionary.md](data/data_dictionary.md).

**Do:**
- Run the standard EDA checks on `data/bank_10k.csv`: shape, target rate,
  missing and `unknown` values, types, feature–target signal.
- Decide the **feature boundary**: which columns are known before you decide to
  call? Write a reason for every column you exclude.
- Look at `pdays = 999` and the `unknown` values: what do they mean?
- Plot the subscription rate and the economic columns against `contact_order`.
  What changes over time?
- Freeze the split **once**: a stratified random 80/20 split with seed 42 into
  `work/exploration/train.csv` and `work/exploration/test.csv`, plus
  `split_metadata.json` (method, seed, sizes, positive rates).

**Deliver:** `work/exploration/` (your EDA notebook or script, the split
script, `train.csv`, `test.csv`, `split_metadata.json`) and the feature boundary
in `work/framing.md`.

**Done when:** every item of the guideline's hand-off checklist is ticked.

**Stretch:** also build a chronological split (train on earlier contacts, test
on later ones) in a separate folder, and compare the positive rates and a quick
baseline's profit on both. Report what you see; keep the random split as your
frozen split.

## Step 3 — Design the evaluation

**Read first:** [practices one-pager](context/methods/PROJECT_DELIVERY_PRACTICES_ONE_PAGER.md),
Solution Design; [context/pathway.md](context/pathway.md).

**Do:** before training any model, write how a model will be scored:
- the cross-validation scheme on `train.csv` (folds, seed);
- how predicted probabilities become a **call list**. The fitness calls the
  top share of clients, and picks that share itself on the **training** part
  of each fold: 3 inner folds give an out-of-fold score for every training
  client, and the share that makes the most profit on those scores is called
  from the top of the validation fold. Why must the validation fold never
  decide how many to call?
- how profit is computed on each fold, and how it becomes a score;
- how you will check the champion on fresh folds before the test read.

**Deliver:** `work/design.md`.

**Done when:** someone else could implement your scoring from `design.md` alone.

## Step 4 — Baselines

**Read first:** [context/pathway.md](context/pathway.md), rule 2 and Gate 3.

**Do:** score three references with your Step 3 protocol, on `train.csv` only:
1. call everyone;
2. a simple business rule: call every client whose previous campaign
   succeeded (`poutcome == "success"`);
3. logistic regression with the **same call-list rule as the fitness**: the
   share to call picked on the training part of each fold (Step 3), then called
   from the top of the validation fold. Earth's gain is then measured like for
   like.

**Deliver:** `work/baseline/` (code and metrics: profit per 1,000 clients,
share of clients called).

**Done when:** you have answered **Gate 3** in `work/design.md`: does the
baseline leave enough to gain to justify an Earth search? How much gain would
convince you?

**Stretch:** score the same logistic regression with the break-even rule
instead (call everyone whose predicted chance is above €10 / €70 ≈ 14%), and
compare its profit and share called with the fitness rule. Then check the
calibration: among clients scored near 14%, do about 14% subscribe?

## Step 5 — Formulate the search

**Read first:** [context/template/CHROMOSOME_PHILOSOPHY.md](context/template/CHROMOSOME_PHILOSOPHY.md);
[context/template/default_chromosome.yaml](context/template/default_chromosome.yaml) as a menu of gene ideas;
[earth/context/CHROMOSOME_GUIDE.md](earth/context/CHROMOSOME_GUIDE.md) for YAML syntax.

**Do:** decide what Earth may change and what stays fixed.
- Candidates for genes: model family and hyperparameters; class weight;
  feature groups (for example, a gene that switches the economic columns on or
  off); handling of `pdays = 999`.
- Fixed: the money, the folds and seed, the feature boundary from Step 2, and
  how the share to call is picked (inside the fitness, on the training folds).
  How many clients to call is not a gene.

**Deliver:** `work/optimization/formulation.md`: every gene with a reason, and
the fixed list.

**Done when:** for every gene you can say which code in `fitness.py` will read it.

**Stretch:** preprocessing genes from the menu, such as how to treat `unknown`
(keep it as a category, or impute it).

## Step 6 — Package and validate

**Read first:** [context/template/INVARIANTS.md](context/template/INVARIANTS.md),
[CONSTRAINTS.md](context/template/CONSTRAINTS.md),
[earth/context/GA_CONTRACT.md](earth/context/GA_CONTRACT.md),
[earth/context/FITNESS_DEVELOPMENT.md](earth/context/FITNESS_DEVELOPMENT.md).

**Do:**

```bash
cp earth/fitness_skeleton.py work/optimization/fitness.py
```

Fill in the TODOs in `work/optimization/fitness.py`, and write
`work/optimization/chromosome.yaml`: a `fitness_function` line and a
`chromosome` block with only your genes (format: [HINTS.md](HINTS.md), Step 5;
more gene examples in `context/template/default_chromosome.yaml`). Then:

```bash
python earth/check_local.py
python earth/validate_chromosome.py work/optimization/chromosome.yaml
```

The local check prints the time of one fitness call per model family and a
run estimate: generations × ⌈population ÷ workers⌉ × time of the slowest call.
The fitness fits each model 4 times per fold (3 inner folds to pick the share
to call, then the full training part), so a call takes 3–4 times longer than a
plain 5-fold CV: on a laptop about 1 s for logistic regression, 2–4 s for
XGBoost and 5–25 s for a random forest, depending on its size. Keep the slow
ranges (many trees, deep trees) in check, or the 15-minute cap will stop the
run after a few dozen generations.

**Deliver:** `work/optimization/fitness.py`, `work/optimization/chromosome.yaml`,
the run estimate in `work/optimization/formulation.md`.

**Done when:** both checks pass, and the run estimate fits in about 15 minutes.

## Step 7 — Run the search

**Read first:** [earth/README.md](earth/README.md) for the run options;
the "Before you press Run" slide from the Earth lab.

**Do:**

```bash
python earth/run_search.py --name run1
```

It checks your files locally, uploads `work/exploration/train.csv` (never
`test.csv`; it refuses), launches on Earth, polls until the run stops (default
cap 15 minutes; `--minutes`, `--pop`, `--units`, `--cpus` change the size), and
saves `work/runs/run1/`.

Then copy your fitness, change **only the score** to F1 at threshold 0.5, and
run the same chromosome again:

```bash
mkdir -p work/runs/run2
cp work/optimization/fitness.py work/runs/run2/fitness.py
# edit: score = F1 on each fold instead of profit; keep the profit scalars
python earth/check_local.py --fitness work/runs/run2/fitness.py
python earth/run_search.py --name run2 --fitness work/runs/run2/fitness.py
python earth/compare_runs.py run1 run2
```

**Deliver:** `work/runs/run1/`, `work/runs/run2/`, and a line per run in
`work/run_notes.md`.

**Done when:** you can say which champion makes more money on the validation
folds, and why the F1 champion differs.

**Stretch:** run3, one more change of your choice (in the chromosome or the
fitness).

## Step 8 — Analyse the experiment

**Read first:** [EXPERIMENT_ANALYSIS_GUIDE.md](EXPERIMENT_ANALYSIS_GUIDE.md),
questions 1–5.

**Do:**

```bash
python earth/fetch_history.py --name run1
```

It downloads every generation into `work/runs/run1/history.csv` and prints the
score per generation, gene shifts, and the top 5. Then work through questions
1–5 of the guide, including the re-score on fresh folds.

**Deliver:** `work/analysis/` and the analysis sections of
`work/delivery/report.md`.

**Done when:** checklist items 1–5 of the guide are ticked.

## Step 9 — Test read and report

**Read first:** [EXPERIMENT_ANALYSIS_GUIDE.md](EXPERIMENT_ANALYSIS_GUIDE.md),
question 6; [context/pathway.md](context/pathway.md), rule 1.

**Do:** for the logistic-regression baseline and your champion, pick the share
to call the same way the fitness does, now on all of `train.csv`: 3-fold
out-of-fold scores on `train.csv`, then the share that makes the most profit on
them. Fit each model on all of `train.csv` and call that share from the top of
`test.csv`. Then score all four policies (call everyone, the simple rule, the
baseline, the champion) **once** on `test.csv`: profit per 1,000 clients and
share of clients called.

**Deliver:** `work/delivery/report.md`, complete.

**Done when:** the report has the profit table on the test set, your verdict
against the success criterion from Step 1, and your answer to: *What would
you let Earth evolve in your next experiment, and why?*

## Troubleshooting

- `Put your Earth user and password in .env`: `.env` still has the example values.
- `Login failed`: check the login name (often without `@domain`) and password.
- `Local check FAILED`: read the line above it. Common causes: a gene in the YAML
  that the fitness does not read (or the reverse), an enum value the fitness does
  not handle, a column outside your feature boundary.
- `Refusing to upload ... test.csv`: the test set never goes to Earth.
- `already exists. Pick a new --name`: each run needs its own name.
- Enum genes need `crossover: {type: error}`.
- Fitness score must be finite and > 0 (`max(score, 1e-9)`).
