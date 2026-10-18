> **Source:** the Earth binary-classifier template. Read "template" as "your
> `fitness.py` and `chromosome.yaml`". Use it as a checklist in Step 6 (Package
> and validate), before your first Earth run.
>
> In this homework the money (€10 per call, €70 per subscription) and the calling
> rule are fixed in `fitness.py` on purpose. The rules below about business cost
> models and business assumptions apply to the chromosome: no gene may change them.

# Known Constraints – Binary Classifier Template

These are structural constraints discovered during development.

---

# 1. Memory Constraints

- Large ensembles increase memory usage.
- Feature engineering can significantly expand feature space.
- High-cardinality categorical encoding can cause blow-up.

Template must guard against:
- Excessive feature expansion
- Unbounded model growth

---

# 2. Runtime Constraints

- Complex models (e.g. deep trees) increase training time.
- Large CV folds multiply runtime.

Template must:
- Respect n_splits parameter
- Avoid uncontrolled parallelism

---

# 3. Metric Constraints

- Some metrics require probability outputs.
- Not all models support predict_proba.
- Template must handle fallback logic.

---

# 4. Defensive Handling

Template must handle:

- Class imbalance
- Degenerate folds
- Numerical instability
- Empty feature sets

Failures must degrade gracefully.

---

# 5. Template Stability Rule

If a change introduces:

- Business assumptions
- Dataset-specific hacks
- Project constants

It violates template constraints
and must be reverted to project layer.
