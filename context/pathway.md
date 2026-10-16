# Homework pathway (minimal practices)

Map of phases and practices: [methods/PROJECT_DELIVERY_PRACTICES_ONE_PAGER.md](methods/PROJECT_DELIVERY_PRACTICES_ONE_PAGER.md).
Tabular EDA and split detail: [methods/TABULAR_EDA_AND_SPLIT_GUIDELINES.md](methods/TABULAR_EDA_AND_SPLIT_GUIDELINES.md).

Phases: **Frame → Explore → Build → Optimize → Deliver**.

## Practices in this homework

| Phase | Practice | README step | Homework definition of done |
|-------|----------|-------------|-----------------------------|
| Frame | Project Framing + Success Criteria | 1 | Business question, target, money, success as numbers in `work/framing.md` |
| Explore | Data Foundation | 2 | EDA checks done, feature boundary with reasons, `train.csv` / `test.csv` frozen once |
| Explore | Solution Design | 3 | Evaluation protocol in `work/design.md`, written before any model |
| Build | Baseline Evidence | 4 | Three references scored on the protocol; Gate 3 answered |
| Optimize | Formulation | 5 | What Earth may change and what stays fixed, with reasons |
| Optimize | Packaging + Validation | 6 | `fitness.py` + `chromosome.yaml` pass the local check and Earth's validator; run estimated |
| Optimize | Execution | 7 | Two runs saved (profit fitness, F1 fitness) |
| Optimize → Deliver | Analysis | 8 | Experiment analysis guide questions 1–5 answered |
| Deliver | Production Packaging (narrow) | 9 | One test read; verdict in `work/delivery/report.md` |

Skipped: Deployment and Monitoring; formal gates beyond Gate 3; retrospective
beyond the report's last question.

## Two non-negotiable rules

1. **Locked test set.** `test.csv` is created once in Step 2. Baselines, the
   local check, and Earth never read it, and it is never uploaded. Step 9 is the
   only time it is scored.
2. **Baseline independence.** The baselines are specified and scored in Step 4,
   before any search. A GA champion is never a baseline.

**Gate 3** in a real project asks whether the baseline leaves enough to gain to
justify spending on optimization. Answer it in writing in Step 4. You proceed
to Earth either way, because the learning goal is the pathway, but your answer
sets what a "good" Earth result means.

## Agent vs student

| Student owns | Coding agent may do |
|--------------|---------------------|
| What the decision and the business question are | Inspect files and schema |
| Which columns are known before the call | Write loaders, EDA, plots, the split script |
| The metric: campaign profit, and how probabilities become a call list | Implement baselines after the student defines them |
| What belongs in the chromosome vs stays fixed | Translate the formulation into YAML and fitness code |
| Whether the champion is really better | Run checks, Earth scripts, and the analysis |
| The verdict | Draft report sections from the artifacts |

## Split vocabulary

| Name | Role |
|------|------|
| `data/bank_10k.csv` | Source data; never edited |
| `work/exploration/train.csv` | Everything before the final read: EDA conclusions, baselines, Earth |
| Validation folds | The `CV_FOLDS` stratified folds of `train.csv` inside the fitness |
| Fresh folds | Same protocol with new seeds, to check search optimism (Step 8) |
| `work/exploration/test.csv` | Locked test set; scored once, in Step 9 |
