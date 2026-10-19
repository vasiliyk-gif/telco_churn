> **Source:** the Earth binary-classifier template. Read "template" as "your
> `fitness.py` and `chromosome.yaml`". Use it as a checklist in Step 5 (Package
> and validate), before your first Earth run.
>
> In this lab the market rule (2–20% seller flexibility, 5% costs, the $500k cap, the 0.5 risk
> weight) and the three past years are fixed in `fitness.py` on purpose: no gene may change them. Unlike
> the homework, the **pricing policy is a gene block**: what to offer is the decision Earth optimises.
> The classifier-specific parts below (probabilities, thresholds, class imbalance) do not apply to this
> regression problem; the rules about genes, determinism and the fitness contract do.

# Template Invariants – Binary Classifier

These rules must always hold true.

---

# 1. Problem Invariant

- Target must be binary.
- Labels must be convertible to {0, 1}.

---

# 2. Execution Invariant

For any valid chromosome:

- Pipeline must be constructible.
- Training must not crash.
- Fitness must return valid numeric score.

---

# 3. Separation Invariant

Template must not:

- Import from projects/
- Access business cost models
- Interpret feature names semantically

---

# 4. Determinism Invariant

Given same:

- Dataset
- Seed
- Chromosome

Pipeline must produce identical score.

---

# 5. Search Space Integrity

Chromosome length must align with:

- Number of columns
- Expected hyperparameters

Mismatches must be handled safely.
