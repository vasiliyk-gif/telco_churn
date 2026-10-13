# Optimization formulation (Workshop 1)

## What Earth may change

- `model`: `logistic_regression` | `xgboost` (one active model per candidate)
- `scaling_method`: `none` | `standard` (applied for logistic regression)
- `imbalance_method`: `none` | `class_weight_balanced`
- `logistic_regression.C`
- `xgboost.n_estimators`, `xgboost.max_depth`, `xgboost.learning_rate`

Inactive nested blocks remain in the genome; fitness ignores the unused family.

## What stays fixed

- Feature policy and imputation / one-hot structure
- Threshold 0.5
- Seed 42, `n_jobs=1`
- Inner validation split of `train.csv`
- F1 as the fitness score
- No ensemble weights, no cost model, no threshold search

## Candidate representation

Earth chromosome YAML: `work/modeling/chromosome.yaml`.

## Evaluation

`FitnessClass` loads the uploaded train CSV, cuts `inner_train` / `validation`,
fits the pipeline for the chromosome, and returns `score = max(F1, 1e-9)` with
scalars `f1`, `precision`, `recall`.

`holdout.csv` is never uploaded.
