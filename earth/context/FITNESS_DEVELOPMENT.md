# Fitness Development Guide

Complete reference for implementing `FitnessClass` and understanding the output
schema and error model. Problem-agnostic — applies to all Earth templates.

---

## FitnessClass Contract

Earth instantiates `FitnessClass` once per worker and calls `calculate_fitness`
many times (once per chromosome per generation).

```python
class FitnessClass:
    def __init__(self, dataset_root: str):
        # Load data, build models, do heavy preprocessing here.
        # Called once per worker.
        ...

    def calculate_fitness(self, chromosome: Any) -> FitnessCalculationResult:
        # Score a single chromosome. Must be fast.
        # Must always return a valid result — never raise.
        ...
```

---

## Result Schema

```python
from pydantic import BaseModel
from typing import Optional, Dict, List, Union

class FitnessCalculationResult(BaseModel):
    score: float
    scalars: Optional[Dict[str, Union[float, int]]] = None
    rows: Optional[Dict[str, List[Union[str, float, int]]]] = None
```

### `score` (required)

- Must be numeric, finite, and strictly positive (for maximum problems).
- Single selection signal — GA uses only this value for selection.
- `NaN` or `inf` will break GA selection.

### `scalars` (optional)

- Flat numeric diagnostics — displayed on Earth dashboard.
- Values: `float`, `int`, or `bool` (coerced to float).
- Must not contain `None`, strings, lists, or deeply nested dicts.
- Penalty breakdowns belong here as top-level keys.
- Must **not** influence `score` directly (diagnostics only).

### `rows` (optional)

- Optional per-experiment tabular companion.
- Column → list of values (str, float, int).
- Not consumed by GA selection; for post-experiment analysis.

---

## Lifecycle

1. `__init__` called once per worker — load data, split, validate columns.
2. `calculate_fitness` called per chromosome — score only, no side effects.
3. `save_model` (optional) called on best solution at experiment end.

---

## Configuration Pattern

Keep the plan in one `CONTRACT` block of module-level constants at the top of
`fitness.py` (asset names, target, ordered feature list, seed, folds, capacity).
Every chromosome is decoded against those constants, so the fitness file and the
chromosome YAML must change together. Sibling modules are allowed: everything in
`launch(code_files=[...])` is uploaded next to `fitness.py`.

---

## Error Handling

All errors must be caught inside `calculate_fitness`:

```python
def calculate_fitness(self, chromosome):
    try:
        # ... computation ...
        return FitnessCalculationResult(score=fitness, scalars=scalars)
    except Exception as exc:
        print(f"fitness error: {exc}")
        return FitnessCalculationResult(score=1e-9)
```

Error categories:
- Invalid chromosome values → defensive validation, return penalty score.
- Model training failure → catch, log, return fallback.
- Numerical instability → check for `NaN`/`inf`, return fallback.

**Never** let exceptions propagate to the GA runtime.

---

## Performance Rules

- Heavy preprocessing belongs in `__init__` (data loading, train/val split, validation).
- `calculate_fitness` must be fast — it is called many times per generation.
- Avoid global mutable state.
- Avoid uncontrolled parallelism inside fitness.
- Avoid external network calls or file writes.

---

## Optional `save_model`

```python
def save_model(self):
    return "sklearn", self.model, self.input_features
```

Used only if a serializable model artifact exists. Called on best solution after
experiment completes.

---

## Available Packages (Earth Worker Environment)

Only packages pre-installed on Earth workers may be used in fitness code.

Key available packages: `numpy`, `pandas`, `scikit-learn`, `pydantic`,
`xgboost-cpu`, `lightgbm`, `catboost`, `matplotlib`, `plotly`, `joblib`, `scipy`.

**Not available**: `pyarrow` (use `fastparquet` instead), `dask`, PyTorch,
TensorFlow, or any package outside the pre-installed list.

See `AVAILABLE_PACKAGES.md` for the complete version-pinned list.
