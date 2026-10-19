"""Earth REST client: auth, dataset upload, project clone, launch, poll, abort.

Adapted from EARTH_AGENT_GUIDE.md.
Usage: see earth/README.md; earth/run_search.py runs the full search.

Set credentials in a .env file at the repo root:
    EARTH_USER=you@evolution.inc
    EARTH_PASS=your-password
"""

from __future__ import annotations

import json
import os
import time
from copy import deepcopy
from pathlib import Path

import requests
import yaml

# ── Constants ──────────────────────────────────────────────────────────────────

BASE = "https://earth.evolution.inc"
TOKEN_CACHE_PATH = Path(__file__).resolve().parent.parent / ".earth_token_cache.json"

# Clone any existing valid project to inherit a well-formed GA configuration.
# (Earth's "Churn Prediction" template; its chromosome and fitness are replaced at launch.)
CHURN_TEMPLATE_ID = "fb775bea36244a829cd79f5d7364016b"

BASIC_COMPUTE_PROFILE = {
    "compute_profile_id":               "6052020896a64dfab30ca96f9beca711",
    "compute_profile_name":             "Basic",
    "compute_profile_launcher_cpus":    1,
    "compute_profile_launcher_memory":  "2Gi",
    "compute_profile_worker_cpus":      1,
    "compute_profile_worker_memory":    "8Gi",
    "fitness_cpu":                      2,
    "fitness_memory":                   1.0,
}

# ── Credential loading ─────────────────────────────────────────────────────────
# Credentials come from .env (gitignored) or real environment variables in CI/prod.
# Template: .env.example at repo root.
# Usage: copy .env.example to .env and set EARTH_USER + EARTH_PASS.

try:
    from dotenv import load_dotenv as _load_dotenv
    # Always load the repo-root .env, even when imported from earth/.
    _load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass  # python-dotenv optional; os.environ already set in CI/prod


# ── Auth ───────────────────────────────────────────────────────────────────────

def _org_id_from_token(token: str) -> str | None:
    """Extract Earth org id from JWT claims when present."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
        # Local import keeps the module importable without pyjwt.
        import base64
        import json

        claims = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")))
    except (ValueError, json.JSONDecodeError, UnicodeError):
        return None
    for key in ("org_id", "organization_id", "urn:zitadel:iam:org:id"):
        value = claims.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _headers_from_token(token: str) -> dict:
    """Build Earth API headers, including required org scope when available."""
    headers = {"Authorization": f"Bearer {token}"}
    org_id = (os.environ.get("EARTH_ORG_ID") or "").strip() or _org_id_from_token(token)
    if org_id:
        headers["x-jwt-org-id"] = org_id
    return headers


def _load_cached_token() -> str | None:
    if not TOKEN_CACHE_PATH.is_file():
        return None
    try:
        data = json.loads(TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    token = data.get("access_token") or data.get("id_token")
    exp = data.get("expires_at_epoch")
    if not token:
        return None
    if exp is not None and time.time() >= float(exp) - 60:
        return None
    return token


def _save_token_cache(token_data: dict) -> None:
    expires_in = token_data.get("expires_in")
    payload = {
        "access_token": token_data.get("access_token"),
        "id_token": token_data.get("id_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_at_epoch": (time.time() + float(expires_in)) if expires_in else None,
        "saved_at_epoch": time.time(),
    }
    try:
        TOKEN_CACHE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"Warning: could not write token cache: {exc}", flush=True)


def _auth_password_api(session: requests.Session) -> str | None:
    """Try the Earth /api/auth/login endpoint with EARTH_USER / EARTH_PASS."""
    username = os.environ.get("EARTH_USER")
    password = os.environ.get("EARTH_PASS")
    if not username or not password:
        return None
    # /api/auth/login expects the ZITADEL login name (often without @domain).
    login_names = [username]
    if "@" in username:
        login_names.append(username.split("@", 1)[0])
    last_status = None
    last_prefix = ""
    for login_name in login_names:
        resp = session.post(
            f"{BASE}/api/auth/login",
            json={"username": login_name, "password": password},
            timeout=60,
        )
        last_status = resp.status_code
        last_prefix = resp.text[:160]
        if resp.status_code == 401:
            continue
        if not resp.ok:
            print(
                f"Password login failed: HTTP {resp.status_code} "
                f"body_prefix={resp.text[:160]!r}",
                flush=True,
            )
            return None
        data = resp.json()
        # Prefer access_token: ZITADEL access tokens carry org_id for x-jwt-org-id.
        # id_token alone is not enough for org-scoped Earth API calls.
        token = (
            data.get("access_token")
            or (data.get("tokens") or {}).get("access_token")
            or data.get("id_token")
            or (data.get("tokens") or {}).get("id_token")
            or data.get("token")
        )
        if not token:
            print(f"Password login response missing token; keys={list(data)}", flush=True)
            return None
        _save_token_cache(
            data if ("access_token" in data or "id_token" in data) else {"access_token": token}
        )
        return token
    print(
        f"Password login rejected (invalid credentials). "
        f"last_status={last_status} body_prefix={last_prefix!r}",
        flush=True,
    )
    return None


def auth(*, password_only: bool = False) -> tuple[requests.Session, dict]:
    """Authenticate and return (session, headers).

    Order:
      1. Cached access token (``.earth_token_cache.json``)
      2. ``POST /api/auth/login`` with ``EARTH_USER`` / ``EARTH_PASS``

    Missing or rejected credentials raise ``RuntimeError``. ``password_only`` is
    kept for compatibility; password login is the only flow.
    """
    session = requests.Session()
    cached = _load_cached_token()
    if cached:
        return session, _headers_from_token(cached)

    token = _auth_password_api(session)
    if token:
        return session, _headers_from_token(token)

    raise RuntimeError(
        "Password login failed or EARTH_USER / EARTH_PASS are missing. "
        "Fix credentials in .env and retry."
    )


# ── Dataset upload ─────────────────────────────────────────────────────────────

def upload_dataset(session: requests.Session, headers: dict,
                   csv_path: str, name: str) -> str:
    """Create a dataset record and upload the CSV. Returns dataset_id."""
    resp = session.post(f"{BASE}/api/datasets",
                        json={"name": name},
                        headers=headers)
    if not resp.ok:
        raise RuntimeError(
            f"upload_dataset: POST /api/datasets returned {resp.status_code}. "
            f"Body: {resp.text!r}"
        )
    ds = resp.json()
    # API may return id under different keys depending on version
    ds_id = ds.get("id") or ds.get("_id") or ds.get("dataset_id")
    if not ds_id:
        raise RuntimeError(
            f"upload_dataset: unexpected API response for POST /api/datasets — "
            f"no 'id' field. Response keys: {list(ds.keys())!r}. Body: {ds!r}"
        )
    # Large CSVs can trigger RemoteDisconnected; retry up to 3 times.
    _max_upload_retries = 3
    for _attempt in range(1, _max_upload_retries + 1):
        try:
            with open(csv_path, "rb") as f:
                upload_resp = session.post(
                    f"{BASE}/api/assets/{ds_id}/upload",
                    files={"file": (Path(csv_path).name, f, "text/csv")},
                    headers=headers,
                    timeout=300,   # 5-min timeout for large CSV uploads
                )
            if upload_resp.ok:
                break
            raise RuntimeError(
                f"upload_dataset: asset upload returned {upload_resp.status_code}. "
                f"Body: {upload_resp.text!r}"
            )
        except Exception as _exc:
            if _attempt == _max_upload_retries:
                raise
            import time as _time
            print(
                f"upload_dataset: upload attempt {_attempt} failed ({_exc!r}); "
                f"retrying in {_attempt * 5}s...",
                flush=True,
            )
            _time.sleep(_attempt * 5)
    print(f"Uploaded dataset '{name}' → id={ds_id}")
    return ds_id


# ── Project creation ───────────────────────────────────────────────────────────

def clone_template(session: requests.Session, headers: dict,
                   template_id: str, dataset_id: str, title: str) -> str:
    """Clone a template to create a project with valid GA config. Returns project_id."""
    template = session.get(f"{BASE}/api/templates/{template_id}", headers=headers).json()
    body = {
        "title":         title,
        "shared":        False,
        "chromosome":    template.get("chromosome"),
        "fitness":       template.get("fitness"),
        "configuration": template.get("configuration"),
        "dataset_id":    dataset_id,
    }
    project_id = session.post(f"{BASE}/api/projects", json=body, headers=headers).json()["id"]
    print(f"Created project '{title}' → id={project_id}")
    return project_id


# ── GA configuration ───────────────────────────────────────────────────────────

def _ga_config(
    pop: int,
    minutes: "int | None",
    maximize: bool,
    elite_pct: float = 0.10,
    mutation_pct: float = 0.60,
    unique_mutation_pct: int = 0,
    recalculate_elite: bool = False,
    max_stagnation_loops: int = 15,
    max_drifts: int = 8,
    steady_threshold: float = 0.001,
    generation_start_steady: int = 30,
    look_back: int = 8,
    generate_final_mutations: bool = False,
    enable_genetic_drift: bool = True,
    concurrency: int = 32,
) -> dict:
    if enable_genetic_drift:
        drift_names = [
            "genesis_crossover_drift",
            "genesis_genetic_drift",
            "mutation_genetic_drift",
        ]
        genesis_drift = {"drift_fraction": 0.2}
        mutation_drift = {"drift_fraction": 0.2, "drift_factor": 2}
        crossover_drift = {"drift_fraction": 0.2}
    else:
        drift_names = []
        genesis_drift = {"drift_fraction": 0.0}
        mutation_drift = {"drift_fraction": 0.0, "drift_factor": 1}
        crossover_drift = {"drift_fraction": 0.0}
    return {
        "ai1": {
            "ga": {
                "population_size":              pop,
                "elite_percentage":             elite_pct,
                "mutation_percentage":          mutation_pct,
                "unique_mutation_percentage":   unique_mutation_pct,
                "recalculate_elite_fitness":    recalculate_elite,
                "run_on_cloud":                 True,
                "calculate_fitness_as_batch":   True,
            },
            "flow_control": {
                "minimum_problem_sufficient_fitness":               0.01,
                "max_stagnation_loops":                             max_stagnation_loops,
                "max_drifts_with_no_change":                        max_drifts,
                "steady_threshold":                                 steady_threshold,
                "generation_to_start_check_steady_state":           generation_start_steady,
                "how_many_generations_look_back":                   look_back,
                "how_many_generations_look_back_for_local_optimization": -1,
                "max_constant_loops":                               -1,
                # -1 is Earth's own sentinel for "no time cap" (matches the
                # template default). When minutes is None, stop purely on
                # max_stagnation_loops / max_drifts_with_no_change instead.
                "time_limit":                                       -1 if minutes is None else int(minutes * 60),
            },
            "cumulative_genetic_drift": {
                "chosen_drifts_names": drift_names,
            },
            "genesis_genetic_drift":    genesis_drift,
            "mutation_genetic_drift":   mutation_drift,
            "genesis_crossover_drift":  crossover_drift,
            "mutation_pool":            {"type": "DefaultMutationPoolCreator"},
            "crossover_pool":           {
                "type":              "DefaultCrossoverPoolCreator",
                "min_fitness_value": 0,
                "max_fitness_value": 1,
            },
            "is_maximum_problem":       bool(maximize),
            "generate_final_mutations": generate_final_mutations,
        },
        "ai2": {"output": {"concurrency": concurrency, "cpu_cores": 1}},
    }


# ── Launch ─────────────────────────────────────────────────────────────────────

def launch(
    session:      requests.Session,
    headers:      dict,
    project_id:   str,
    dataset_id:   str,
    chromo_path:  str   = "earth/chromosome.yaml",
    code_files:   "list[str] | None" = None,
    pop:          int   = 30,
    units:        int   = 8,
    minutes:      "int | None" = 60,
    maximize:     bool  = True,
    elite_pct:    float = 0.10,
    mutation_pct: float = 0.60,
    unique_mutation_pct: int   = 0,
    recalculate_elite:   bool  = False,
    max_stagnation_loops: int  = 15,
    max_drifts:          int   = 8,
    steady_threshold:    float = 0.001,
    generation_start_steady: int = 30,
    look_back:           int   = 8,
    generate_final_mutations: bool = False,
    enable_genetic_drift: bool = True,
    concurrency:  int   = 32,
    fitness_cpus: "int | None" = None,
) -> str:
    """PATCH project with chromosome + fitness, then POST to start experiment.

    Returns experiment_id.

    ``code_files`` (list of local paths, default ``["earth/fitness.py"]``) is the
    set of sibling Python modules to upload. Each file is uploaded under its basename
    (e.g. ``earth/fitness.py`` → ``fitness.py``). The first file whose
    basename is ``fitness.py`` (or the first file if none match) is treated as
    the fitness entry module by Earth convention; callers should include a
    ``fitness.py``.
    """
    chromo_yaml = open(chromo_path).read()

    if code_files is None:
        code_files = ["earth/fitness.py"]
    fitness_payload = []
    for path in code_files:
        p = Path(path)
        fitness_payload.append({
            "key": p.name,
            "value": p.read_text(encoding="utf-8"),
            "is_folder": False,
        })
    if not fitness_payload:
        raise ValueError("code_files must contain at least one Python module")

    intended = _ga_config(
        pop, minutes, maximize,
        elite_pct=elite_pct,
        mutation_pct=mutation_pct,
        unique_mutation_pct=unique_mutation_pct,
        recalculate_elite=recalculate_elite,
        max_stagnation_loops=max_stagnation_loops,
        max_drifts=max_drifts,
        steady_threshold=steady_threshold,
        generation_start_steady=generation_start_steady,
        look_back=look_back,
        generate_final_mutations=generate_final_mutations,
        enable_genetic_drift=enable_genetic_drift,
        concurrency=concurrency,
    )

    patch = {
        "chromosome": {"value": chromo_yaml},
        "fitness": {
            "code": fitness_payload,
            "requirements": [],
        },
        "configuration": intended,
        "dataset_id": dataset_id,
    }
    r = session.patch(
        f"{BASE}/api/projects/{project_id}",
        json=patch,
        headers=headers,
        timeout=120,
    )
    r.raise_for_status()

    # Re-GET so chromosome YAML is parsed back to dict by Earth
    proj  = session.get(
        f"{BASE}/api/projects/{project_id}", headers=headers, timeout=60
    ).json()
    chrom = yaml.safe_load(proj["chromosome"]["value"])
    chrom = chrom.get("chromosome", chrom)

    # Replace template configuration entirely. Merging ai1.ga into the clone
    # left genetic-drift operators active and did not cap live population.
    cfg = deepcopy(intended)

    code_files = [
        {"key": f["key"], "is_folder": False, "value": f["value"]}
        for f in (proj.get("fitness") or {}).get("code", [])
    ]

    fu = dict(BASIC_COMPUTE_PROFILE)
    if fitness_cpus is not None:
        fu["fitness_cpu"] = int(fitness_cpus)
    fu["fitness_units_amount"] = units
    fu["total_cpus"]           = units * fu["fitness_cpu"] + 1
    fu["total_memory"]         = f"{(units + 1) * 8 + 2}.00Gi"

    body = {
        "name":       proj.get("title", "earth-ga"),
        "project_id": project_id,
        "shared":     False,
        "configuration": {
            "chromosome":      chrom,
            "lom_configuration": cfg,
            "dataset_id":      dataset_id,
            "code_files":      code_files,
            "fitness_unit":    fu,
            "experiment_type": "REGULAR",
        },
    }
    try:
        r = session.post(
            f"{BASE}/api/experiments", json=body, headers=headers, timeout=180
        )
    except requests.exceptions.Timeout as exc:
        # Launch POST can hang while Earth still creates the experiment.
        recovered = _find_experiment_for_project(session, headers, project_id)
        if recovered:
            print(
                f"Launch POST timed out; recovered experiment id={recovered} "
                f"for project {project_id}",
                flush=True,
            )
            return recovered
        raise RuntimeError(
            f"launch POST timed out and no experiment found for project {project_id}"
        ) from exc
    if not r.ok:
        running = session.get(
            f"{BASE}/api/experiments/running-count", headers=headers, timeout=30
        ).text
        print(f"Launch failed ({r.status_code}): {r.text[:400]}")
        print(f"Running experiments count: {running}")
        # Last chance: experiment may exist despite non-OK response.
        recovered = _find_experiment_for_project(session, headers, project_id)
        if recovered:
            print(f"Recovered experiment id={recovered} after launch error", flush=True)
            return recovered
        r.raise_for_status()

    exp_id = r.json()["id"]
    print(f"Experiment started → id={exp_id}")
    return exp_id


def _find_experiment_for_project(
    session: requests.Session, headers: dict, project_id: str
) -> str | None:
    """Best-effort lookup when launch POST hangs or fails after creation."""
    try:
        resp = session.get(f"{BASE}/api/experiments", headers=headers, timeout=60)
        if not resp.ok:
            return None
        data = resp.json()
        items = data.get("items") if isinstance(data, dict) else data
        if not isinstance(items, list):
            return None
        hits = [e for e in items if str(e.get("project_id") or "") == str(project_id)]
        if not hits:
            return None
        # Prefer newest by created_at when present.
        def _key(e: dict):
            return str(e.get("created_at") or e.get("updated_at") or e.get("id") or "")

        hits.sort(key=_key, reverse=True)
        eid = hits[0].get("id")
        return str(eid) if eid else None
    except Exception:
        return None


# ── Poll / abort ───────────────────────────────────────────────────────────────

class TokenExpiredError(Exception):
    """Raised by poll() when the API returns 401 Unauthorized."""


class RateLimitError(Exception):
    """Raised by poll() when the API returns 429 Too Many Requests."""


class TransientPollError(Exception):
    """Raised by poll() for retryable HTTP failures (422, 5xx, etc.)."""


_TRANSIENT_HTTP = {408, 409, 422, 425, 500, 502, 503, 504}


def poll(session: requests.Session, headers: dict, exp_id: str) -> dict:
    """Return current experiment status + best chromosome.

    Generation source priority:
      1. best-chromosome endpoint root "generation" field  — most accurate,
         reflects the generation the best individual was found in.
      2. experiment status endpoint "generations_passed"   — fallback, often
         lags or stays 0 during deployment/early running.

    Raises
    ------
    TokenExpiredError
        When either endpoint returns HTTP 401, indicating the auth token
        has expired and the caller must re-authenticate.
    RateLimitError
        When either endpoint returns HTTP 429.
    TransientPollError
        When either endpoint returns a retryable status (422, 5xx, …).
    """
    resp = session.get(f"{BASE}/api/experiments/{exp_id}", headers=headers)
    if resp.status_code == 401:
        raise TokenExpiredError(f"poll: experiment endpoint returned 401 for exp_id={exp_id}")
    if resp.status_code == 429:
        raise RateLimitError(f"poll: experiment endpoint returned 429 for exp_id={exp_id}")
    if resp.status_code in _TRANSIENT_HTTP:
        raise TransientPollError(
            f"poll: experiment endpoint returned {resp.status_code} for exp_id={exp_id}"
        )
    resp.raise_for_status()
    exp = resp.json()

    out = {
        "status":     exp.get("status"),
        "generation": exp.get("generations_passed"),   # may be None or 0
        "generations_passed": exp.get("generations_passed"),
        "score":      None,
        "scalars":    {},
        "chromosome": None,
    }
    best_resp_obj = session.get(
        f"{BASE}/api/experiments/{exp_id}/best-chromosome", headers=headers
    )
    if best_resp_obj.status_code == 401:
        raise TokenExpiredError(
            f"poll: best-chromosome endpoint returned 401 for exp_id={exp_id}"
        )
    if best_resp_obj.status_code == 429:
        raise RateLimitError(
            f"poll: best-chromosome endpoint returned 429 for exp_id={exp_id}"
        )
    if best_resp_obj.status_code in _TRANSIENT_HTTP:
        # DEPLOYING often 500s best-chromosome while the GA is already
        # advancing. Return experiment status so observers can record gen ≤ 5.
        return out
    try:
        best_resp = best_resp_obj.json()
        ind = best_resp.get("individual") or {}
        out["score"]      = ind.get("fitness_score")
        out["scalars"]    = (ind.get("fitness_composition") or {}).get("scalars", {})
        out["chromosome"] = ind.get("chromosome")
        # "generation" in the best-chromosome response root is more reliable
        # than "generations_passed" on the experiment record.
        gen_from_best = best_resp.get("generation")
        if gen_from_best is not None:
            out["generation"] = gen_from_best
    except Exception:
        pass
    return out


def abort(session: requests.Session, headers: dict, exp_id: str) -> None:
    session.post(f"{BASE}/api/experiments/{exp_id}/abort", headers=headers)
    print(f"Aborted experiment {exp_id}")
