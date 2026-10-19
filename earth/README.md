# Earth tools (Lab 2)

```bash
python earth/check_connection.py                     # login check, no experiment
python earth/check_local.py                          # run your fitness locally on sample chromosomes
python earth/validate_chromosome.py work/optimization/chromosome.yaml   # Earth's schema check
python earth/run_search.py --name run1               # upload, launch, poll, save to work/runs/run1/
python earth/compare_runs.py run1 run2               # champions side by side
python earth/fetch_history.py --name run1            # every generation -> work/runs/run1/history.csv
python earth/classic_baseline.py                     # Step 3: best-RMSE model + one flat margin
python earth/make_offers.py --name run1              # Step 8: champion -> offers on the 2010 listings
python earth/score_2010.py                           # Step 8: the reveal (after the teacher releases the prices)
```

Defaults: `work/exploration/train.csv`, `work/optimization/chromosome.yaml`,
`work/optimization/fitness.py`. Change them with `--train`, `--chromosome`,
`--fitness`; add extra files with `--assets`. `run_search.py` refuses to upload
`test.csv`. Run size: `--pop` (30), `--units` (15), `--cpus` (1), `--minutes`
(15); `--no-wait` and `--collect` to launch now and fetch the result later. The
other GA settings come from the YAML's `ai1` block if it has one, else defaults.

## Files

| File | Role |
|------|------|
| `fitness_skeleton.py` | Starting point for `work/optimization/fitness.py` |
| `ibuyer_market.py` | The market rule (fixed) |
| `classic_baseline.py` | The classic pipeline, scored like the fitness; writes 2010 offers |
| `make_offers.py` | Champion -> offers on the 2010 listings |
| `score_2010.py` | The reveal: scores your offers once the 2010 prices are released |
| `run_search.py` | Local check, upload, launch, poll, save one run |
| `check_local.py` | Runs the fitness locally on sample chromosomes |
| `validate_chromosome.py` | Earth's chromosome validator + a negative control |
| `compare_runs.py` | Compares saved runs and shows what changed |
| `fetch_history.py` | Downloads every generation of a run for analysis |
| `earth_client.py` | Auth, dataset upload, launch, poll, abort |
| `check_connection.py` | Login + template + running-count |
| `context/` | Earth GA contract references (see `NOTES_FOR_THIS_REPO.md`) |

## Auth

Set `EARTH_USER` / `EARTH_PASS` in `.env` (login name often without `@domain`).
Scripts log in with `POST /api/auth/login` and use the ZITADEL **access_token**
(it carries `org_id` for `x-jwt-org-id`); a bad password exits with a clear
message. Optional: set `EARTH_ORG_ID` explicitly. Tokens are cached in
`.earth_token_cache.json` (gitignored).
