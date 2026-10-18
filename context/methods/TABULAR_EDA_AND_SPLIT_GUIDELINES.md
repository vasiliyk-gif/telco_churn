# Tabular Data EDA and Split Guidelines

This guide expands lifecycle **Step 3 (EDA and profiling)** and **Step 4 (data split strategy)** for any supervised tabular ML project.  
It is generalized, but keeps practical lessons learned from real project execution.

> **In this homework (Bank Marketing):**
> - The course calls the final split the **test set** (`work/exploration/test.csv`); this guide says "holdout test set". Same thing: read once, at the end.
> - The metric is **campaign profit** (see `PROJECT_BRIEF.md`), not F1 or PR-AUC. Use imbalance-aware *diagnostics* in EDA, but score models in euros.
> - §4.8 applies: the rows are in date order (`contact_order`), so decide whether a random or a chronological split answers "how will this work next campaign?".

## Scope

- Problem families: binary classification, multiclass classification, and regression
- Data type: tabular datasets with mixed numeric/categorical features
- Goal: move from raw data to a trusted train/test foundation for baseline and optimization

---

## Step 3: EDA and Profiling (Detailed)

### 3.1 Goals

- Assess data quality and ML feasibility before modeling.
- Define and validate model feature policy (what is in/out and why).
- Produce both machine-readable and stakeholder-readable artifacts.

### 3.2 Inputs

- Raw dataset snapshot (versioned)
- Data contract draft (target, entity ID, non-model columns, constraints)
- Optional feature dictionary/schema file

### 3.3 Outputs (Required)

- Profiling artifact (JSON/table report) for automation and downstream config generation
- EDA notebook/report for analysts and stakeholders
- Documented pre-ML expectations and key risks

### 3.4 Execution Flow

1. **Validate schema and parseability**
   - Confirm required columns exist (target, IDs, timestamps if relevant).
   - Remove unnamed/artifact columns introduced by exports.
2. **Profile structure and quality**
   - Quantify missingness, uniqueness, constants, cardinality, and dtype mismatches.
3. **Analyze target behavior**
   - Class balance (classification) or distribution/range (regression).
4. **Analyze features**
   - Numeric distributions/percentiles/skew/outliers.
   - Categorical frequency and cardinality.
5. **Analyze relationships**
   - Feature-target signal.
   - Inter-feature correlations or redundancy risk.
6. **Set feature inclusion policy**
   - Explicitly mark excluded fields (e.g., target, IDs, descriptions, leakage columns).
7. **Write pre-ML expectation summary**
   - State expected model difficulty, risks, and recommended first metrics/models.

### 3.5 Standard Checks (Must Include)

- **Dataset shape**
  - Number of rows/columns
  - Effective candidate feature count after exclusions

- **Target diagnostics**
  - Problem type validation (binary/multiclass/regression)
  - Distribution and imbalance characteristics

- **Data quality**
  - Missingness by feature
  - Constant/near-constant features
  - All-unique features (identifier-like)
  - Parse/type anomalies

- **Feature behavior**
  - Numeric stats (mean/std/quantiles/min/max)
  - Categorical top levels + frequency shares
  - High-cardinality warnings

- **Signal diagnostics**
  - Numeric-to-target association (e.g., correlation)
  - Categorical-to-target signal (e.g., target-rate lift by level)
  - Internal correlation/redundancy checks

### 3.6 Actionable Rules (Generalized)

- Treat **feature typing** as a governed artifact (schema/dictionary), not ad-hoc notebook logic.
- Keep **identifier and human-description columns** in the data for traceability, but exclude from model features.
- Exclude columns with clear leakage risk (post-outcome signals, unavailable-at-inference fields).
- Keep exclusion reasons explicit and reproducible.
- Align profiling outputs and notebook conclusions before any split or training.

### 3.7 Definition of Done (Step 3)

Step 3 is complete only if:

- Profiling report is regenerated for the current raw-data version.
- EDA contains:
  - dataset shape
  - target distribution
  - numeric/categorical diagnostics
  - feature-target and inter-feature relationship views
  - risk + expectation summary
- Feature inclusion/exclusion policy is documented and approved.

### 3.8 Suggested Artifact Structure

- `profiling/`
  - `dataset_profile.json`
  - `eda.ipynb`
  - `eda_summary.md` (optional)

---

## Step 4: Data Preparation and Split Strategy (Detailed)

### 4.1 Goals

- Create reproducible training and evaluation datasets.
- Prevent leakage from model development into final performance estimation.
- Preserve statistically representative target behavior across splits.

### 4.2 Inputs

- Profiled and cleaned dataset snapshot
- Approved target column and feature policy
- Split strategy decision (holdout, CV, group split, time split)

### 4.3 Outputs (Required)

- `train` split artifact
- `test` split artifact (immutable holdout)
- Split metadata log (row counts, rates, seed, method)

### 4.4 Recommended Split Policy (Default for Non-Temporal Tabular Projects)

- Single immutable holdout test set (commonly 10-30%, often 20%)
- Stratified split for classification
- Fixed random seed(s) for reproducibility
- Test set never used for feature selection, hyperparameter tuning, or model search

### 4.5 Execution Flow

1. Load approved dataset snapshot.
2. Apply deterministic cleanup needed for splitting.
3. Validate target column and basic target health.
4. Create train/test split using approved method.
5. Save split artifacts with versioned naming.
6. Compare target distributions across full/train/test.
7. Freeze test split for downstream phases.

### 4.6 Validation Checks (Must Pass)

- Split row counts sum to source dataset row count.
- Target distribution shift between train and test is within agreed tolerance.
- Duplicate/near-duplicate leakage checks across splits.
- Entity leakage checks for repeated entities (group-aware split when needed).
- Split artifacts referenced consistently in training/optimization configs.

### 4.7 Definition of Done (Step 4)

Step 4 is complete only if:

- Train and test artifacts are generated and validated.
- Split metadata is logged (method, seed, date, rates, counts).
- Team agrees test set is immutable for the current data version.
- Baseline and optimization configs point to the correct split artifacts.

### 4.8 When to Use a Different Split Strategy

- **Time dependency exists:** use chronological split, not random split.
- **Multiple rows per entity:** use grouped split to avoid entity leakage.
- **Very small datasets:** consider repeated CV for robust estimation, while keeping a final holdout if feasible.
- **Severe imbalance:** stratify and monitor minority-class representation in every split.

---

## Common Pitfalls and Controls

- **Pitfall:** hidden leakage features enter training  
  **Control:** enforce availability-at-inference checks in feature policy.

- **Pitfall:** schema drift between EDA and pipeline  
  **Control:** derive both from a single schema/feature dictionary artifact.

- **Pitfall:** test set reused during tuning  
  **Control:** optimize only on train/validation workflow; reserve test for final report.

- **Pitfall:** unstable or irreproducible split  
  **Control:** fixed seeds, versioned snapshots, and split metadata logging.

- **Pitfall:** ignoring imbalance in early diagnostics  
  **Control:** include imbalance-aware metrics (e.g., F1/PR-AUC) in baseline and optimization planning.

---

## Hand-off Checklist (Before Baseline Modeling)

- [ ] Profiling artifact refreshed for current dataset version
- [ ] EDA report updated with all required diagnostics
- [ ] Target, ID, leakage, and non-model columns explicitly documented
- [ ] Train/test split generated, validated, and frozen
- [ ] Split metadata logged (counts, rates, seed, method)
- [ ] Training and optimization configs aligned to split artifacts
- [ ] Risks and pre-ML expectations documented

