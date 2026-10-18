# Prompts for your coding agent (homework)

Copy, paste, adapt. You make the decisions; the agent writes code and explains.
Read what it does before you accept it.

## Step 0 — Set up

> I'm in the earth_hw repo. Create a Python 3.12 virtual environment in .venv,
> install requirements.txt, and copy .env.example to .env. Don't write my
> password anywhere; I'll fill .env myself. Then run `python earth/check_connection.py`.

## Step 1 — Frame

> Read PROJECT_BRIEF.md and ask me, one at a time, the questions I need to answer
> in work/framing.md. Don't answer them for me; help me sharpen my wording.

## Step 2 — Explore and split

> Following context/methods/TABULAR_EDA_AND_SPLIT_GUIDELINES.md §3.5, write an
> EDA script for data/bank_10k.csv in work/exploration/. Show shape, target rate,
> `unknown` share per column, the `pdays == 999` share, and subscription rate by
> poutcome, contact and month.

> Plot the subscription rate and the five economic columns against contact_order
> (deciles). What changes over time, and what does that mean for a random split?

> Read the description of `duration` in data/bank-additional-names.txt and tell
> me what it says. (Then decide yourself.)

> Write work/exploration/prepare_split.py: stratified random 80/20, seed 42,
> writing train.csv, test.csv and split_metadata.json. Run it once.

## Step 3 — Design

> Here is my evaluation design: <paste>. Point out anything ambiguous, and
> anything that lets the validation fold leak into the score (for example into
> how many clients are called).

## Step 4 — Baselines

> Implement the three baselines from the README in work/baseline/, scored with
> the protocol in work/design.md, on train.csv only. The logistic regression
> must use the same call-list rule as the fitness (share picked on the
> training part of each fold). Report profit per 1,000 clients (mean and std
> over folds) and the share of clients called.

## Step 5 — Formulate

> Here is my formulation: <paste>. For each gene, tell me which code in
> fitness.py would read it, and flag any gene that would have no effect for some
> model families.

## Step 6 — Package

> Copy earth/fitness_skeleton.py to work/optimization/fitness.py and fill in the
> TODOs according to work/design.md and work/optimization/formulation.md. Write
> work/optimization/chromosome.yaml with exactly the genes the fitness reads.
> Then run `python earth/check_local.py` and fix what fails.

> Run `python earth/validate_chromosome.py work/optimization/chromosome.yaml`
> and explain the result.

## Step 7 — Run

> Run `python earth/run_search.py --name run1` and explain each stage of the
> output while it runs.

> Copy work/optimization/fitness.py to work/runs/run2/fitness.py and change only
> the score to mean F1 at threshold 0.5 over the folds, keeping the profit
> scalars. Show me the diff, run the local check, then run2, then
> `python earth/compare_runs.py run1 run2`.

## Step 8 — Analyse

> Run `python earth/fetch_history.py --name run1`, then help me answer questions
> 1–5 of EXPERIMENT_ANALYSIS_GUIDE.md one by one, with a table or plot for each,
> saved under work/analysis/.

## Step 9 — Test read

> Write work/delivery/test_read.py. For the baseline and my champion: pick the
> share to call from 3-fold out-of-fold scores on all of train.csv (same rule as
> the fitness), fit on all of train.csv, and call that share of test.csv. Then
> score all four policies once on test.csv (profit per 1,000, share called).
> Run it once.
> Then help me draft work/delivery/report.md from my notes; I'll write the verdict.
