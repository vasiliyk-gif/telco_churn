# Earth DS Workshop — Churn Prediction (S4: from the Earth UI to the API)

> **Before class:** do [Step 0](#step-0--set-up) (venv, `pip install -r requirements.txt`, `.env` with your Earth login) so class starts at Step 1.

## The session

You ran a churn search in the Earth UI. Today you run the same search from your
terminal through the Earth API, read what it searched and how it scored, change
one thing, and run again.

The decision: each month the retention team calls the **400 customers most likely
to leave**. The score is **hit@400**: the share of those 400 who actually churn
(5 stratified folds, top 80 per fold, averaged). A random list scores about 0.27,
logistic regression about 0.76.

| Step | What you do | Time |
|------|-------------|------|
| 0 | Set up, put your Earth login in `.env` | 10 min |
| 1 | Run the search as is (`run1`) | 25 min |
| 2 | Read the search space and the fitness | 25 min |
| 3 | Change one thing in the chromosome, run again (`run2`) | 25 min |
| 4 | If time: change one thing in the fitness (`run3`) | — |

Each step can be done by hand in the terminal or by asking your coding agent.
Prompts for the agent: [AGENT_PROMPTS.md](AGENT_PROMPTS.md).

## Repository

```text
data/            train_clean.csv, test_ids.csv, data_dictionary.md
earth/           chromosome.yaml + fitness.py (from the UI run), run_search.py,
                 check_local.py, compare_runs.py, WALKTHROUGH.md, Earth client
work/            run_notes.md; runs/ holds one folder per run (created by run_search.py)
```

| Data file | Role |
|-----------|------|
| `data/train_clean.csv` | Uploaded to Earth; the search runs on it |
| `data/test_ids.csv` | IDs of the customers in the course's locked test set; uploaded so the fitness drops the 10 of them that also appear in train |

Column meanings: [data/data_dictionary.md](data/data_dictionary.md).

## Step 0 — Set up

You need Python 3.12 and your Earth login.

```bash
git clone --branch s4-class-v2 --single-branch https://github.com/vasiliyk-gif/telco_churn.git
cd telco_churn
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and put your Earth user and password in `EARTH_USER` / `EARTH_PASS`
(the login name is often the part before `@`). Never commit `.env`.

On Windows: `.venv\Scripts\activate` and `copy .env.example .env`.

Check the connection (no experiment is created):

```bash
python earth/check_connection.py
```

## Step 1 — Run the search as is

```bash
python earth/run_search.py --name run1
```

It checks the chromosome and fitness locally, uploads `train_clean.csv` +
`test_ids.csv`, launches on Earth, and polls until the run stops (time cap 15
minutes). It prints the experiment name; watch the generations in the Earth UI.

Results land in `work/runs/run1/` (add a line to `work/run_notes.md`):

- `earth_ids.json` — Earth ids and settings. Check `"test_ids_uploaded": true`.
- `champion_chromosome.json` — the best chromosome and its hit@400 per fold.
- `chromosome.yaml`, `fitness.py` — copies of exactly what ran.

Lost the terminal? Launch with `--no-wait`, and collect later with
`python earth/run_search.py --name run1 --collect`.

Class sizing: population 10, 5 workers × 1 CPU, 15-minute cap. Change with
`--pop`, `--units`, `--cpus`, `--minutes`. All other GA settings come from the
`ai1` block of the chromosome YAML.

## Step 2 — Read the search space and the fitness

Open [earth/chromosome.yaml](earth/chromosome.yaml) and
[earth/fitness.py](earth/fitness.py). Work through
[earth/WALKTHROUGH.md](earth/WALKTHROUGH.md): first by eye, then with your agent.
Compare what you read with your `run1` champion.

## Step 3 — Change one thing in the chromosome, run again

Edit a copy, never the original:

```bash
mkdir -p work/runs/run2
cp earth/chromosome.yaml work/runs/run2/chromosome.yaml
```

Change **one** thing in `work/runs/run2/chromosome.yaml` (ideas in the
walkthrough), write the change and your prediction in `work/run_notes.md`,
then check and run:

```bash
python earth/check_local.py --chromosome work/runs/run2/chromosome.yaml
python earth/run_search.py --name run2 --chromosome work/runs/run2/chromosome.yaml
python earth/compare_runs.py run1 run2
```

`compare_runs.py` shows both champions side by side and the lines you changed.

## Step 4 — If time: change one thing in the fitness

```bash
mkdir -p work/runs/run3
cp earth/fitness.py work/runs/run3/fitness.py
```

Change one thing in `work/runs/run3/fitness.py`, then:

```bash
python earth/check_local.py --fitness work/runs/run3/fitness.py
python earth/run_search.py --name run3 --fitness work/runs/run3/fitness.py
python earth/compare_runs.py run1 run3
```

**A changed fitness changes what the score means.** A run3 hit rate is not
comparable with run1 or run2 unless you score both champions with the same
fitness.

## Next: homework

The homework moves to a new dataset and the full cycle: framing, baseline,
search, a check on fresh folds, and one test read. Details will follow.

## Working with your coding agent

You own what the problem means, which features are allowed, the metric, what Earth
may change, and whether a champion is better. The agent may read files, explain
code, run commands, and draft edits for you to review.

## Troubleshooting

- `Put your Earth user and password in .env`: `.env` still has the example values.
- `Login failed`: check the login name (often without `@domain`) and password.
- `Local check FAILED`: read the line above it; a common cause is a `feature_mask`
  size that no longer matches the `FEATURES` list in `fitness.py`.
- `already exists. Pick a new --name`: each run needs its own name.
- Enum genes need `crossover: {type: error}`.
- Upload only `train_clean.csv` and `test_ids.csv`.
- Validate a chromosome on Earth: `python earth/validate_chromosome.py <path>`.
