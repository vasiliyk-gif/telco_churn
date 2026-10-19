# DS Project Delivery Practices (One-Pager)

> **In this homework:** use this page as the map of phases and practices. The full
> practices document and the other methodologies it names are not part of this repo;
> the one methodology you need is [TABULAR_EDA_AND_SPLIT_GUIDELINES.md](TABULAR_EDA_AND_SPLIT_GUIDELINES.md).
> The homework steps are in the [README](../../README.md); the homework pathway is
> [context/pathway.md](../pathway.md).

**Part of:** the org's DS Delivery Operating System v4.0 (Tier 2 — Practices).

## Purpose

A practical, three-tier framework — Phases, Practices, Methodologies — that turns a
business/research problem into delivered, monitored value, and plugs directly into the
org's v4.0 standard.

## The Three Tiers

| Tier | What it is | Where it lives |
|---|---|---|
| 1. Phase | 5 top-level stages of project evolution | Owned by v4.0 |
| 2. Practice | 12 recurring units of work, each with inputs/outputs/DoD | `PROJECT_DELIVERY_PRACTICES.md` (this doc's detail) |
| 3. Methodology | Modality/engine/approach-specific guidance | `Methodologies_&_Guidelines/` (not in this repo) |

## Phases → Practices

`FRAME → EXPLORE → BUILD → OPTIMIZE → DELIVER`

Not a rigid pipeline: a project may skip a non-applicable Practice, run several
concurrently, or return to an earlier one when new evidence changes understanding.

| Phase | Practices |
|---|---|
| Frame | Project Framing → Success Criteria |
| Explore | Data Foundation → Solution Design |
| Build | Baseline Evidence |
| Optimize | Optimization Formulation → Packaging → Validation → Execution |
| Deliver | Production Packaging → Deployment & Monitoring → Project Retrospective |

## Practice One-Liners

1. **Project Framing** — goal, DoD, risks, owners, timeline. *(Milestone: Problem Defined)*
2. **Success Criteria** — business KPI + ML metric + constraints, numeric thresholds. *(→ Gate 1)*
3. **Data Foundation** — data contract, EDA/profiling, immutable split. *(→ Gate 2)*
4. **Solution Design** — model family, evaluation protocol, optimize-or-not call.
5. **Baseline Evidence** — a non-searched reference point exists (simple model *or* an EDA-informed seed config). *(→ Gate 3)*
6. **Optimization Formulation** — the problem itself: variables, constraints, fitness — engine-agnostic.
7. **Optimization Packaging** — render the engine-specific package (Earth, by default).
8. **Optimization Validation** — smoke-test the package before spending real budget. *(→ Gate 4)*
9. **Optimization Execution** — run the search, track everything, select the best candidate.
10. **Production Packaging** — retrain, one final holdout read, inference package, rollout decision. *(→ Gate 5)*
11. **Deployment & Monitoring** — maintenance, monitoring, retraining triggers, rollback, governance.
12. **Project Retrospective** — extract and record what the project taught us; walks the v4.0 Knowledge Promotion questions per Practice used. No paired Gate — feeds organizational, not per-project, investment.

## Milestone ↔ Gate

Every Practice produces a Milestone (evidence) — 12 total. Only 5 are paired with a Gate
(an investment decision) — Gates are PMO capacity calls, Milestones are not:

`Gate 1 (after Success Criteria) → Gate 2 (after Data Foundation) → Gate 3 (after
Baseline Evidence) → Gate 4 (after Optimization Validation) → Gate 5 (after Production
Packaging)`

## Two Non-Negotiable Rules

- **Immutable holdout:** the test set is read once, at Production Packaging. It may only
  be revised through a versioned **Split Revision** (new understanding of the data, never
  a disappointing result) — which invalidates downstream evidence and re-triggers Gate 2.
- **Baseline independence:** whichever form Baseline Evidence takes, it must be built
  independently of the optimization search loop — a seed config that's already been
  GA-tuned isn't a baseline anymore.

## Not Every Project Is Classification

For unsupervised/no-ground-truth work (e.g. clustering), several Practices change shape —
see Clustering EDA & Methodology
*(initial framing)*: Success Criteria needs an evaluation *proxy* instead of a labeled
metric, and Data Foundation adds scale-sensitivity and routing-covariate checks.

## Methodologies & Guidelines (Tier 3)

| Methodology | Supports |
|---|---|
| [Tabular EDA & Split Guidelines](TABULAR_EDA_AND_SPLIT_GUIDELINES.md) | Data Foundation |
| Audio Data EDA & Split Guidelines | Data Foundation |
| Audio vs. Tabular EDA | Data Foundation |
| Clustering EDA & Methodology *(initial framing)* | Success Criteria, Data Foundation, Solution Design, Baseline Evidence, Optimization Formulation |
| Earth GA Optimization Methodology *(to write)* | Optimization Formulation, Packaging, Execution |
| Inference Packaging & Rollback Methodology *(to write)* | Production Packaging |
| Monitoring & Retraining Methodology *(to write)* | Deployment & Monitoring |

## Principle

Practices apply when their guidance is relevant — they guide the work, they don't define
project status. The full practices document (inputs, outputs, DoD and anti-patterns per Practice)
is an internal reference and is not needed for this homework.
