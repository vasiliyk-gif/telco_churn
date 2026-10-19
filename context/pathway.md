# Lab 2 pathway (minimal practices)

Map of phases and practices: [methods/PROJECT_DELIVERY_PRACTICES_ONE_PAGER.md](methods/PROJECT_DELIVERY_PRACTICES_ONE_PAGER.md).
Tabular EDA and split detail: [methods/TABULAR_EDA_AND_SPLIT_GUIDELINES.md](methods/TABULAR_EDA_AND_SPLIT_GUIDELINES.md).

Phases: **Frame → Explore → Build → Optimize → Deliver**.

## Practices in this session

| Phase | Practice | README step | Definition of done |
|-------|----------|-------------|--------------------|
| Frame | Project Framing + Success Criteria | 1 | Decision, money, success as numbers in `work/framing.md` |
| Explore | Data Foundation + Solution Design | 2 | Feature boundary with reasons; past-years evaluation in `work/design.md` |
| Build | Baseline Evidence | 3 | Classic pipeline scored on the same years; Gate 3 answered |
| Optimize | Formulation | 4 | Valuation and policy genes, fixed list, with reasons |
| Optimize | Packaging + Validation | 5 | `fitness.py` + `chromosome.yaml` pass the local check and Earth's validator |
| Optimize | Execution | 6 | One run saved |
| Optimize → Deliver | Analysis | 7 | Analysis guide questions 1–4 answered |
| Deliver | Test read | 8 | Offers made; scored once on 2010; result and verdict in the report |

## Two non-negotiable rules

1. **Locked test.** The test is the 2010 listings. Their prices are released only at the end of the lab;
   you score your offers on them once, in Step 8. Never tune anything on 2010.
2. **Baseline independence.** The classic baseline is scored in Step 3, before any search. A GA
   champion is never a baseline.

**Gate 3** asks whether the baseline leaves enough to gain to justify an optimisation. Answer it in
writing in Step 3; it sets what a "good" Earth result means.

## Agent vs student

| Student owns | Coding agent may do |
|--------------|---------------------|
| What the decision and the business question are | Inspect files and schema |
| Which columns are known when a home is listed | Write loaders, EDA, plots, the split script |
| The metric: risk-adjusted profit, and what the pricing policy may depend on | Implement baselines after the student defines them |
| What belongs in the chromosome vs stays fixed | Translate the formulation into YAML and fitness code |
| Whether the champion is really better | Run checks, Earth scripts, and the analysis |
| The verdict | Draft report sections from the artifacts |

## Split vocabulary

| Name | Role |
|------|------|
| `data/ames_history.csv` | Source sales 2006–2009; never edited |
| `work/exploration/train.csv` | Copy of the history: baselines, local checks, Earth |
| Past-year folds | Inside the fitness: fit on years before Y, offer on Y, for Y = 2007, 2008, 2009 |
| `data/ames_2010_listings.csv` | The test: 2010 homes without prices; you make offers on them |
| `data/ames_2010_prices.csv` | Released by the teacher at the end; scored once in Step 8 |
