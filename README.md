# Earth DS Workshop — Churn Prediction

## What you will build

A binary customer churn classifier, optimized for validation F1 with Earth GA,
then scored once on an untouched holdout. The ML problem stays simple so you can
practice the full DS pathway with a coding agent.

## What you will learn

- How to partner with a coding agent on a DS project without giving up reasoning
- A lightweight DS delivery path: Frame → Explore → Baseline → Formulate → Earth → Validate → Deliver
- Earth UI and Earth API as the optimization stage

Detailed practices: [context/workshop_pathway.md](context/workshop_pathway.md) and
[context/methods/PROJECT_DELIVERY_PRACTICES_ONE_PAGER.md](context/methods/PROJECT_DELIVERY_PRACTICES_ONE_PAGER.md).

Project framing: [context/project_context.md](context/project_context.md).

Workshop tags and teacher vs student updates:
[context/WORKSHOP_STATE_MANAGEMENT.md](context/WORKSHOP_STATE_MANAGEMENT.md).

## Repository structure

```text
data/                   Excel tables + data_context.md
context/                Project context, pathway, state management, DS practices
context/template_churn/ Reference chromosome/fitness examples (not runtime)
earth/                  Earth REST client + connection check
work/                   Your work (empty at start except framing.md)
```

Start from tag `workshop-1-start-v3` (this tree). Do not check out the solution
tag during the exercise.

## Prerequisites

- Python 3.12
- An Earth account (`EARTH_USER` / `EARTH_PASS`)

## Setup

### Student checkout

```bash
git checkout workshop-1-start-v3
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set EARTH_USER / EARTH_PASS
python earth/check_connection.py
```

Use Python 3.12. `.venv/` is local and is not committed.

`python --version` should print Python 3.12.x after activate.

If `python3.12` is not on your `PATH`, create the environment with a Python 3.12
interpreter you already have. For a pyenv install of 3.12.3:

```bash
~/.pyenv/versions/3.12.3/bin/python -m venv .venv
source .venv/bin/activate
```

On Windows, activate with `.venv\Scripts\activate`.

## Verify Earth connection

```bash
python earth/check_connection.py
```

Expected: authentication succeeds, the template GET returns 200, and
`running-count` prints. No dataset or experiment is created.

## Project pathway

Work under `work/`. Ask your coding agent to implement each step after you make
the DS decisions. Read the code, run it, then continue.

### 1. Frame

Read [context/project_context.md](context/project_context.md). Fill
[work/framing.md](work/framing.md): target, metric, feature boundary, workshop
data assumption.

### 2. Explore

Build a short loader under `work/exploration/`. Join the five-table module.
Check shape, target balance, missingness, types, and exclusions. Freeze
`train.csv` and `holdout.csv`. There is another conflicting consolidated extract
(`Telco_customer_churn.xlsx`); it is deliberately not our modeling source.

### 3. Baseline

Implement a fixed sklearn logistic pipeline under `work/modeling/`. Score F1 on
`validation` cut from `train.csv`. Do not read `holdout.csv`.

### 4. Formulate

Write what Earth may change and what stays fixed. Read
[context/template_churn/](context/template_churn/) as reference, then create a
**reduced** chromosome under `work/modeling/`.

### 5. Package

Write `FitnessClass` that scores F1 on `validation` from the uploaded train CSV.
Smoke-test locally. Validate the chromosome:

```bash
python earth/validate_chromosome.py work/modeling/chromosome.yaml
```

### 6. Earth

Launch through the API (`earth/run_search.py` once you have it). Watch generations
in the Earth UI. Save the experiment id and champion chromosome.

### 7. Validate

Refit baseline and champion on all of `train.csv`. Score both once on
`holdout.csv`. Search fitness and holdout F1 are different numbers.

### 8. Deliver

Write `work/delivery/report.md` with framing, baseline, formulation, Earth ids,
champion config, holdout metrics, a conclusion, and:

> If you ran a second optimization experiment, what additional decision would you
> allow Earth to evolve?

## Working with your coding agent

You own problem meaning, feature boundaries, the metric, chromosome vs fixed
choices, and whether the champion generalized. The agent may inspect files,
implement code, run checks, and draft documentation. See
[context/workshop_pathway.md](context/workshop_pathway.md).

## Expected outputs

| After | Under `work/` |
|-------|----------------|
| Frame | Completed `framing.md` |
| Explore | `exploration/train.csv`, `exploration/holdout.csv`, split metadata |
| Baseline | Modeling scripts + validation metrics |
| Formulate / Package | `modeling/chromosome.yaml`, `modeling/fitness.py`, `modeling/pipeline.py` |
| Earth | Experiment id + champion JSON |
| Validate / Deliver | Holdout comparison + `delivery/report.md` |

## Troubleshooting

- Login name is often the part before `@` in `EARTH_USER`
- Fitness `score` must be finite and strictly positive (`max(f1, 1e-9)`)
- Enum genes need `crossover: {type: error}`
- Upload only `train.csv` to Earth — never `holdout.csv`
- Do not model from the consolidated workbook
- Do not run `python earth/earth_client.py` (legacy MOXO `__main__`)

## Workshop state management

Full rules for humans and agents (teacher mode vs student mode):
[context/WORKSHOP_STATE_MANAGEMENT.md](context/WORKSHOP_STATE_MANAGEMENT.md).

`workshop-1-start-v3` is the tree students receive. `workshop-1-solution-v3` is
the verified pathway. Leave the solution tag facilitator-only until the workshop
is over. Do not merge it into `main`.

```bash
# create the workshop starting point
git tag -a workshop-1-start-v3 -m "Earth Workshop 1 student starting state"

# continue implementing / testing the complete pathway
git switch -c facilitator/solution workshop-1-start-v3
# exploration → baseline → formulation → Earth packaging
# → Earth run → champion validation → delivery

# after successful end-to-end validation
git tag -a workshop-1-solution-v3 -m "Earth Workshop 1 verified solution"

# before class, repeat the student path from a clean tree
git worktree add ../telco_churn_student workshop-1-start-v3
```
