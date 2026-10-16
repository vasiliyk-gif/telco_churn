# GA Execution Contract

Problem-agnostic contract between the Earth GA engine and any fitness implementation.
This contract applies to all templates and projects. It must never reference business
semantics or project-specific logic.

---

## What Earth Owns (Never Implement in Fitness Code)

Earth fully manages:

- Population generation
- Elite selection
- Mutation and crossover
- Genetic drift
- Experiment lifecycle (start, pause, abort, resume)
- Parallelization and orchestration

Python fitness code **must not**:

- Mutate chromosomes
- Track generations
- Implement GA logic
- Depend on call order between chromosomes
- Store chromosome-specific mutable state across calls

---

## Execution Lifecycle

1. Earth loads `chromosome.yaml` and parses the search space
2. Earth creates a population of individuals
3. Earth instantiates `FitnessClass(dataset_root)` **once per worker**
4. Earth calls `calculate_fitness(chromosome)` many times (once per individual per generation)
5. Earth runs selection, mutation, crossover
6. Earth optionally calls `save_model()` on the best solution

Heavy preprocessing belongs in `__init__`. `calculate_fitness` must be fast.

---

## Fitness Entry Point Contract

Every fitness implementation must expose:

```python
class FitnessClass:
    def __init__(self, dataset_root: str): ...
    def calculate_fitness(self, chromosome: Any) -> FitnessCalculationResult: ...
```

Requirements:

- Input is a decoded chromosome dictionary (never Earth GA metadata).
- Function must **always** return a valid `FitnessCalculationResult`.
- No uncaught exceptions may propagate to GA runtime.
- Fitness must be deterministic for the same chromosome + same seed.
- Avoid global mutable state.

---

## Return Type

```python
from pydantic import BaseModel
from typing import Optional, Dict, List, Union

class FitnessCalculationResult(BaseModel):
    score: float
    scalars: Optional[Dict[str, Union[float, int]]] = None
    rows: Optional[Dict[str, List[Union[str, float, int]]]] = None
```

- `score` — scalar consumed by GA for selection; must be finite and positive.
- `scalars` — flat numeric diagnostics (dashboard display, not selection).
- `rows` — optional tabular companion for post-experiment analysis.

---

## Error Handling

If fitness computation fails:

- Catch the exception inside `calculate_fitness`.
- Return a valid result with a safe fallback score (e.g., `1e-9` for max problems).
- Log the failure briefly; do not crash.

```python
try:
    ...
    return FitnessCalculationResult(score=fitness, scalars=scalars)
except Exception as exc:
    print(f"fitness error: {exc}")
    return FitnessCalculationResult(score=1e-9)
```

---

## Determinism and Resource Safety

Fitness execution must:

- Be deterministic for same chromosome and same seed.
- Avoid unbounded memory growth.
- Avoid uncontrolled parallelism.
- Avoid writing files (unless explicitly allowed by the project).
- Avoid external network calls.
- Not dynamically import external code at runtime.

---

## Optimization Direction

Default: **maximum problem** (higher score = better).

If minimizing, invert score explicitly inside fitness.

---

## Key Gotchas (Validated Against earth.evolution.inc)

1. Auth uses the ZITADEL **`access_token`** from `POST /api/auth/login`, not the `id_token`: only the access token carries `org_id` for the `x-jwt-org-id` header.
2. Start experiments with a **fully-populated `fitness_unit`** — incomplete payloads 503.
3. **Enum** chromosome genes must use `crossover: {type: error}`.
4. The `requirements` field is accepted but **not pip-installed** — only pre-baked libs or vendored pure-Python code.
5. Fitness `score` must be **strictly positive and finite** or GA selection breaks.
