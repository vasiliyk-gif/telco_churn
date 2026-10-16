# Notes for this repository

The documents under `earth/context/` are general Earth contract references. They
predate this project; read them with these caveats.

1. **Sibling modules work.** `earth_client.launch(code_files=[...])` uploads
   several sibling `.py` files, and they import each other on the workers.

2. **Chromosome YAML.** `work/optimization/chromosome.yaml` needs the
   `chromosome` block. It may also carry the GA settings in `ai1` / `ai2` (the
   format the Earth UI exports); `run_search.py` reads `ai1` if present, except
   population, time cap and compute (`--pop`, `--minutes`, `--units`, `--cpus`).
   `validate_chromosome.py` sends only the `chromosome` block, because the
   validator fails (HTTP 500) on the extra blocks.

3. **AVAILABLE_PACKAGES.md is an undated snapshot.** Treat it as "packages known
   to be on workers when this folder was copied," not a live inventory.
   pandas, NumPy, SciPy, scikit-learn, xgboost, and pydantic are listed and used
   by the fitness skeleton; `requirements.txt` pins the same versions locally.

4. **Auth.** `earth/earth_client.py` logs in with `POST /api/auth/login`
   (`{username, password}`, login name often without `@domain`) and uses the
   returned **access_token**, which carries the `org_id` sent as `x-jwt-org-id`.
   The old Keycloak `/realms/earth/...` token endpoint no longer works.

5. **Scalars may hold one per-fold dict.** `FITNESS_DEVELOPMENT.md` says scalars
   must be flat. One level of nesting (`profit_per_1000_per_fold`, as in the
   skeleton) works on Earth, and `compare_runs.py` reads it; avoid deeper nesting.
