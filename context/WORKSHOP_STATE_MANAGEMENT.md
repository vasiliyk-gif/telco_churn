# Workshop state management

Humans and coding agents use this file to decide **where a change belongs**.
Wrong placement either spoils the exercise (students see the solution) or
leaves the starter broken.

## Two states

| State | Git object | What it is |
|-------|------------|------------|
| Starting state | `workshop-1-start-vN` (current: `workshop-1-start-v3`), branch `main` | What students clone and check out |
| Solution | `workshop-1-solution-vN` (current: `workshop-1-solution-v3`), branch `facilitator/solution` | Verified pathway after Earth + holdout |

`main` stays on the start tag. The solution is **not** merged into `main`.
Keep the solution tag facilitator-only until the workshop is over.

```bash
# starting point (students)
git checkout workshop-1-start-v3

# facilitator pathway
git switch facilitator/solution
```

## Ask first: which mode?

Before editing, the agent must identify the mode. If the user did not say,
ask once:

1. **Teacher mode** — change the starting state (what every student receives).
2. **Student mode** — continue or revise the completed pathway (solution).

Do not mix the two in one commit.

## Teacher mode — merge into the starting state

Use when the change must exist **before** a student begins Frame / Explore /
Baseline / Earth.

Typical teacher-mode work:

- README, setup, prerequisites, checkout commands
- `requirements.txt`, `.env.example`, `.gitignore`
- `context/` (project context, pathway, this file, template reference)
- `data/` and `data/data_context.md`
- Earth **client** and readiness tools: `earth/earth_client.py`,
  `earth/check_connection.py`, `earth/validate_chromosome.py`, `earth/README.md`
- Empty `work/` layout and the unfilled `work/framing.md` template
- Auth / connection fixes that would otherwise block Step 0

How to apply:

1. Branch or check out from the current start tag (`workshop-1-start-vN` / `main`).
2. Make only starter-safe changes. Do **not** add `work/modeling/`,
   `work/exploration/prepare_data.py`, `earth/run_search.py`, filled reports,
   train/holdout CSVs, or champion JSON.
3. Commit on `main`.
4. Create the **next** annotated start tag (`workshop-1-start-vN+1`). Do not
   move a published start tag.
5. Rebase or merge that start commit onto `facilitator/solution` so the
   solution stays based on the new starter.
6. If the solution still validates, retag `workshop-1-solution-vN+1`.
7. Push `main`, `facilitator/solution`, and the new tags.

Never copy solution files into `main` to “keep them in sync.”

## Student mode — tag as solution

Use when the change is part of **doing the workshop**: implementing the
pathway, or fixing something that only exists after students start coding.

Typical student-mode work:

- Filled `work/framing.md` decisions
- `work/exploration/prepare_data.py`, `train.csv`, `holdout.csv`
- `work/modeling/` (pipeline, baseline, fitness, chromosome, smoke test,
  champion validation)
- `earth/run_search.py` and Earth run artifacts
- `work/optimization/`, `work/delivery/report.md`

How to apply:

1. Work on `facilitator/solution`, branched from the current start tag.
2. Keep the student README prompts. Do not rewrite the starter into a finished
   project on `main`.
3. After Earth run + holdout validation succeed, create or move the **next**
   annotated solution tag (`workshop-1-solution-vN+1`).
4. Do **not** merge into `main`. Do not push the solution to the student remote
   until the workshop is finished, if that would leak the reference.

## Decision rule

| Question | Teacher (start) | Student (solution) |
|----------|-----------------|--------------------|
| Would a student need this on day one, before framing? | Yes | No |
| Does it implement explore / baseline / Earth / delivery? | No | Yes |
| Would seeing it skip a pathway decision? | Must not be in start | Belongs in solution |

If both: split the change. Starter-safe docs/client go to `main` first; pathway
code stays on `facilitator/solution`.

## Agent checklist

- [ ] Mode is explicit (teacher or student).
- [ ] Start tree still has empty `work/exploration`, `work/baseline`,
      `work/optimization`, `work/delivery` (plus unfilled `framing.md` only).
- [ ] Start tree has no `earth/run_search.py` and no `work/modeling/`.
- [ ] New start tag is a new version (`vN+1`), not a moved published tag.
- [ ] Solution remains based on the current start tag.
- [ ] `.env` and `.earth_token_cache.json` are never committed.
