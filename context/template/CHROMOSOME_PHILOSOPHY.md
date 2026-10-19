> **Source:** the Earth binary-classifier template. Read "template" as "your
> `fitness.py`". It is a checklist for Step 4 (Formulate).
>
> In this lab the market rule (2–20% seller flexibility, 5% costs, the $500k cap, the 0.5 risk
> weight) and the three past years are fixed in `fitness.py` on purpose: no gene may change them. Unlike
> the homework, the **pricing policy is a gene block**: what to offer is the decision Earth optimises.
> The classifier-specific parts below (probabilities, thresholds, class imbalance) do not apply to this
> regression problem; the rules about genes, determinism and the fitness contract do.

# Chromosome Philosophy – Binary Classifier Template

The chromosome represents a configuration of:

- Feature preprocessing
- Feature selection
- Model selection
- Model hyperparameters
- Optional feature engineering

It encodes HOW to solve the problem,
not WHY the problem exists.

---

# Structural Principles

1. Deterministic Interpretation
   - Each chromosome key has fixed meaning.
   - Decoding must not depend on external state.

2. Full Executability
   - Any valid chromosome must produce a runnable pipeline.

3. Defensive Decoding
   - Invalid or extreme values must be handled safely.
   - Chromosome must never cause uncaught exceptions.

---

# Typical Dimensions

Examples (problem-agnostic):

- Encoding method per column
- Imputation strategy per column
- Scaling choice per column
- Feature selection mask
- Model selection flags
- Model hyperparameters
- Ensemble weights

# Hybrid search spaces

Some problems combine a **global** feature-selection method (e.g. mutual information with a
continuous threshold on numeric columns) with **per-column** preprocess arrays (encoding,
imputation, scaling) in a fixed column order. That keeps selection semantics simple while
still letting a GA explore column-wise treatment.

---

# What Chromosome Must NOT Contain

- Business thresholds
- Cost multipliers
- Dataset-specific feature meaning
- Runtime configuration (e.g. file paths)

Chromosome represents search space only.
