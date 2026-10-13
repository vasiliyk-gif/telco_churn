# Workshop 1 delivery report

## Framing

Binary churn classifier on the IBM five-table telco module under the workshop
data assumption (cross-section treated as prediction-time features → future
`Churn Value`). Metric contract: F1 at threshold 0.5.

See `work/framing.md` and `context/project_context.md`.

## Baseline

Fixed logistic regression (`C=1.0`, standard scaling, no class weight) scored on
`validation` cut from `train.csv`.

| Metric | Value |
|--------|-------|
| F1 | 0.6914 |
| Precision | 0.6850 |
| Recall | 0.6979 |

Source: `work/modeling/baseline_metrics.json`.

## Optimization formulation

Earth may change model (`logistic_regression` | `xgboost`), `scaling_method`,
`imbalance_method`, `logistic_regression.C`, and a small XGBoost hyperparameter
block. Fixed: features, splits, seed, threshold 0.5, F1 fitness.

See `work/optimization/formulation.md` and `work/modeling/chromosome.yaml`.

## Earth experiment

| Field | Value |
|-------|-------|
| Dataset id | `d6050858-a5a2-49ee-b26a-087c61b9a37d` |
| Project id | `d4514877159443cba319d7b519a647e8` |
| Experiment id | `4cf6cc09830d483490d5f87145d8f0fd` |
| Stop | Abort at generation 5 (teaching budget) |
| Fitness score at stop | 0.7108 |

Ids: `work/optimization/earth_ids.json`. Champion:
`work/optimization/champion_chromosome.json`.

## Champion configuration

- `model`: xgboost
- `scaling_method`: standard
- `imbalance_method`: none
- `xgboost.n_estimators`: 115
- `xgboost.max_depth`: 5
- `xgboost.learning_rate`: ≈ 0.0466

## Holdout evaluation (one read)

Both models refit on all of `train.csv`, scored once on `holdout.csv`.

| Model | F1 | Precision | Recall |
|-------|----|-----------|--------|
| Baseline | 0.7031 | 0.7382 | 0.6711 |
| Earth champion | 0.7079 | 0.7664 | 0.6578 |

Confusion matrices and full payload: `work/modeling/holdout_comparison.json`.

Search fitness (0.7108 on validation) and holdout F1 are different numbers.

## Conclusion

The Earth champion slightly improves holdout F1 versus the fixed baseline on this
split. The gain is small; the pathway (frame → baseline → formulate → Earth →
independent holdout) is the primary result of Workshop 1.

## If you ran a second optimization experiment, what additional decision would you allow Earth to evolve?

_(Left blank for class discussion. Candidates: decision threshold, feature
subsets, richer preprocessing, validation strategy.)_
