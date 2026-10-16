# GA Assumptions and Search Space Guidelines

Guardrails and design principles for implementing fitness functions and designing
chromosome search spaces in Earth GA.

---

## GA Guardrails (Do Not Violate)

### Earth-Owned — Never Implement in Python

- Population size management
- Elite selection and scoring
- Mutation and crossover operators
- Genetic drift
- Stop conditions (time, stagnation, max generations)
- Parallelism and orchestration

### Python Code Must Not

- Implement GA logic
- Track generations
- Mutate chromosomes
- Depend on call order between chromosomes
- Store chromosome-specific state between calls

---

## Optimization Direction

Default: **maximum problem** (higher score = better solution).

To minimize: invert score explicitly inside fitness — do not change Earth config.

---

## Drift Awareness

Drift increases mutation magnitude over generations. Fitness must tolerate
out-of-distribution parameter values. Validate defensively before heavy
computation.

---

## Recommended Penalty Pattern

```python
if invalid_chromosome:
    return FitnessCalculationResult(score=1e-9)
```

Use the lowest reasonable positive value, not negative or zero.

---

## Search Space Design Principles

### Good GA Parameters (optimizable)

- Learning rate, depth, regularization
- Feature selection flags / weights
- Model family choice (enum: kmeans, gmm, xgboost, etc.)
- Preprocessing toggles (PCA, normalization strategy)
- Representation family (enum)

### Bad GA Parameters (not-a-gene)

- Dataset paths
- Random seeds (seeds should be fixed in config, not searched)
- Logic flags that completely change code structure
- Fitness policy knobs (weights, penalties — belong in config)
- Environment-dependent controls

### Allowed Model Families

Tree-based: XGBoost, LightGBM, CatBoost, RandomForest, ExtraTrees, GradientBoosting

Linear/classical ML: Linear/Ridge/Lasso/ElasticNet, Logistic Regression, Linear SVM, kNN

Unsupervised/clustering: PCA, TruncatedSVD, KMeans, DBSCAN, GaussianMixture, IsolationForest

Not allowed (not available in Earth environment): PyTorch, TensorFlow, Keras,
Optuna, Hyperopt, Ray, Statsmodels, Prophet.

---

## Final Rule

If unsure whether logic belongs in Earth or Python:

> It belongs in Earth.
