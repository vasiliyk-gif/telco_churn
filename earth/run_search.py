"""Run one Earth GA search from the terminal and save it under work/runs/<name>/.

Run from repo root (requires .env with EARTH_USER / EARTH_PASS):

    python earth/run_search.py --name run1           # your chromosome + fitness under work/optimization/
    python earth/run_search.py --name run2 --fitness work/runs/run2/fitness.py
    python earth/run_search.py --name run1 --no-wait  # launch and exit
    python earth/run_search.py --name run1 --collect  # later: poll and save the champion

Steps: local pre-check of the chromosome + fitness, upload the training CSV
(default work/exploration/train.csv) plus any --assets, clone the template
project, launch, poll until Earth stops, save the champion. Refuses to upload
work/exploration/test.csv: the test set never goes to Earth.

GA settings come from the ai1 block of the chromosome YAML, except population
(--pop), time cap (--minutes), and compute (--units, --cpus), which are sized for
a class of students running at the same time.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_local import check as check_local  # noqa: E402
from earth_client import (  # noqa: E402
    BASE,
    CHURN_TEMPLATE_ID,
    auth,
    clone_template,
    launch,
    poll,
    upload_dataset,
)

DEFAULT_TRAIN = _REPO_ROOT / "work" / "exploration" / "train.csv"
TEST_CSV = _REPO_ROOT / "work" / "exploration" / "test.csv"
DEFAULT_CHROMOSOME = _REPO_ROOT / "work" / "optimization" / "chromosome.yaml"
DEFAULT_FITNESS = _REPO_ROOT / "work" / "optimization" / "fitness.py"
RUNS_DIR = _REPO_ROOT / "work" / "runs"
POLL_SECONDS = 30
FINAL_STATUSES = ("COMPLETED", "STAGNATED", "ERROR", "ABORTED")
PLACEHOLDERS = {"", "your_login_name", "your_password"}


def check_credentials() -> bool:
    """Plain-language check of .env before any Earth call."""
    env_path = _REPO_ROOT / ".env"
    if not env_path.is_file() and not os.environ.get("EARTH_USER"):
        print(
            "No .env file. Run:  cp .env.example .env  and put your Earth user "
            "and password in it.",
            flush=True,
        )
        return False
    user = (os.environ.get("EARTH_USER") or "").strip()
    password = (os.environ.get("EARTH_PASS") or "").strip()
    if user in PLACEHOLDERS or password in PLACEHOLDERS:
        print(
            "Put your Earth user and password in .env (EARTH_USER / EARTH_PASS); "
            "it still has the example values.",
            flush=True,
        )
        return False
    return True


def ga_settings(chromosome_yaml: Path, args: argparse.Namespace) -> dict:
    """launch() keyword arguments: ai1 block of the YAML + class-sized overrides."""
    doc = yaml.safe_load(chromosome_yaml.read_text(encoding="utf-8")) or {}
    ai1 = doc.get("ai1") or {}
    ga = ai1.get("ga") or {}
    flow = ai1.get("flow_control") or {}
    drifts = (ai1.get("cumulative_genetic_drift") or {}).get("chosen_drifts_names")
    yaml_pop = ga.get("population_size")
    if yaml_pop is not None and int(yaml_pop) != args.pop:
        print(
            f"Note: population_size is {args.pop} (from --pop); the YAML says {yaml_pop}.",
            flush=True,
        )
    return {
        "pop": args.pop,
        "units": args.units,
        "fitness_cpus": args.cpus,
        "concurrency": args.units,
        "minutes": args.minutes,
        "maximize": bool(ai1.get("is_maximum_problem", True)),
        "elite_pct": float(ga.get("elite_percentage", 0.05)),
        "mutation_pct": float(ga.get("mutation_percentage", 0.15)),
        "unique_mutation_pct": ga.get("unique_mutation_percentage", 0),
        "recalculate_elite": bool(ga.get("recalculate_elite_fitness", False)),
        "max_stagnation_loops": int(flow.get("max_stagnation_loops", 5)),
        "max_drifts": int(flow.get("max_drifts_with_no_change", 3)),
        "steady_threshold": float(flow.get("steady_threshold", 0.001)),
        "generation_start_steady": int(flow.get("generation_to_start_check_steady_state", 10)),
        "look_back": int(flow.get("how_many_generations_look_back", 11)),
        "generate_final_mutations": bool(ai1.get("generate_final_mutations", False)),
        "enable_genetic_drift": bool(drifts) if drifts is not None else True,
    }


def upload_extra_asset(session, headers, dataset_id: str, csv_path: Path) -> bool:
    """Add a second CSV asset to an existing dataset. Returns False on failure."""
    try:
        with open(csv_path, "rb") as f:
            resp = session.post(
                f"{BASE}/api/assets/{dataset_id}/upload",
                files={"file": (csv_path.name, f, "text/csv")},
                headers=headers,
                timeout=300,
            )
    except Exception as exc:  # noqa: BLE001 — optional asset; warn and continue
        print(f"WARNING: {csv_path.name} upload failed ({exc!r})", flush=True)
        return False
    if not resp.ok:
        print(
            f"WARNING: {csv_path.name} upload returned HTTP {resp.status_code} "
            f"body_prefix={resp.text[:200]!r}",
            flush=True,
        )
        return False
    print(f"Uploaded {csv_path.name} to dataset {dataset_id}", flush=True)
    return True


def copy_into(src: Path, run_dir: Path) -> None:
    dst = run_dir / src.name
    if dst.exists() and dst.resolve() == src.resolve():
        return
    shutil.copy(src, dst)


def wait_and_save(session, headers, exp_id: str, run_dir: Path) -> int:
    while True:
        state = poll(session, headers, exp_id)
        status = state.get("status")
        print(
            f"  [{status}] gen={state.get('generation')} score={state.get('score')}",
            flush=True,
        )
        if status in FINAL_STATUSES:
            break
        time.sleep(POLL_SECONDS)

    final = poll(session, headers, exp_id)
    champion = {
        "experiment_id": exp_id,
        "status": final.get("status"),
        "generation": final.get("generation"),
        "fitness_score": final.get("score"),
        "scalars": final.get("scalars") or {},
        "chromosome": final.get("chromosome"),
    }
    champ_path = run_dir / "champion_chromosome.json"
    champ_path.write_text(json.dumps(champion, indent=2), encoding="utf-8")
    print(f"Wrote {champ_path.relative_to(_REPO_ROOT)}", flush=True)

    if final.get("status") == "ERROR":
        print("Experiment ended in ERROR.", flush=True)
        return 1
    if final.get("chromosome") is None:
        print("No champion chromosome returned.", flush=True)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--name", default="run1", help="Run label; output goes to work/runs/<name>/")
    parser.add_argument("--chromosome", type=Path, default=DEFAULT_CHROMOSOME)
    parser.add_argument("--fitness", type=Path, default=DEFAULT_FITNESS)
    parser.add_argument("--train", type=Path, default=DEFAULT_TRAIN, help="Training CSV to upload")
    parser.add_argument("--assets", type=Path, nargs="*", default=[], help="Extra files to upload with it")
    parser.add_argument("--minutes", type=int, default=15, help="Time cap for the run")
    parser.add_argument("--pop", type=int, default=10, help="GA population size")
    parser.add_argument("--units", type=int, default=5, help="Parallel fitness workers")
    parser.add_argument("--cpus", type=int, default=1, help="CPUs per fitness worker")
    parser.add_argument("--no-wait", action="store_true", help="Launch, save ids, and exit")
    parser.add_argument("--collect", action="store_true",
                        help="Do not launch; poll the experiment in work/runs/<name>/earth_ids.json and save the champion")
    args = parser.parse_args()

    run_dir = RUNS_DIR / args.name
    ids_path = run_dir / "earth_ids.json"

    if not check_credentials():
        return 1

    if args.collect:
        if not ids_path.is_file():
            print(f"Missing {ids_path.relative_to(_REPO_ROOT)}; launch the run first.", flush=True)
            return 1
        exp_id = json.loads(ids_path.read_text(encoding="utf-8"))["experiment_id"]
        session, headers = auth(password_only=True)
        return wait_and_save(session, headers, exp_id, run_dir)

    for path in (args.train, *args.assets, args.chromosome, args.fitness):
        if not path.is_file():
            print(f"Missing {path}", flush=True)
            return 1
    for path in (args.train, *args.assets):
        if path.resolve() == TEST_CSV.resolve() or path.name == TEST_CSV.name:
            print(f"Refusing to upload {path}: the test set never goes to Earth.", flush=True)
            return 1
    if ids_path.is_file():
        print(
            f"{ids_path.relative_to(_REPO_ROOT)} already exists. Pick a new --name "
            "so this run does not overwrite an earlier one.",
            flush=True,
        )
        return 1

    if not check_local(args.chromosome, args.fitness, args.train, args.assets):
        print("Fix the chromosome / fitness above before launching on Earth.", flush=True)
        return 1

    run_dir.mkdir(parents=True, exist_ok=True)
    copy_into(args.chromosome, run_dir)
    copy_into(args.fitness, run_dir)
    settings = ga_settings(args.chromosome, args)

    print("Authenticating...", flush=True)
    try:
        session, headers = auth(password_only=True)
    except RuntimeError as exc:
        print(f"Login failed: {exc}", flush=True)
        return 1

    name = f"hw-{args.name}-{int(time.time())}"
    print(f"Uploading {args.train.name} as dataset '{name}'...", flush=True)
    dataset_id = upload_dataset(session, headers, str(args.train), name)
    assets_uploaded = {}
    for asset in args.assets:
        assets_uploaded[asset.name] = upload_extra_asset(session, headers, dataset_id, asset)
    if not all(assets_uploaded.values()):
        print("WARNING: some extra assets did not upload; the fitness will not see them.", flush=True)

    print("Creating project...", flush=True)
    project_id = clone_template(session, headers, CHURN_TEMPLATE_ID, dataset_id, name)

    print(
        f"Launching: population {settings['pop']}, {settings['units']} workers x "
        f"{settings['fitness_cpus']} CPU, time cap {settings['minutes']} min...",
        flush=True,
    )
    exp_id = launch(
        session,
        headers,
        project_id,
        dataset_id,
        chromo_path=str(args.chromosome),
        code_files=[str(args.fitness)],
        **settings,
    )

    ids = {
        "run_name": args.name,
        "earth_name": name,
        "dataset_id": dataset_id,
        "project_id": project_id,
        "experiment_id": exp_id,
        "train": args.train.name,
        "assets_uploaded": assets_uploaded,
        "chromosome": args.chromosome.name,
        "fitness": args.fitness.name,
        "settings": settings,
    }
    ids_path.write_text(json.dumps(ids, indent=2), encoding="utf-8")
    print(json.dumps(ids, indent=2), flush=True)
    print(
        f"\nWatch it in the Earth UI: {BASE} -> Experiments -> '{name}' "
        f"(experiment id {exp_id}).",
        flush=True,
    )

    if args.no_wait:
        print(
            f"Not waiting. Later run:  python earth/run_search.py --name {args.name} --collect",
            flush=True,
        )
        return 0
    return wait_and_save(session, headers, exp_id, run_dir)


if __name__ == "__main__":
    raise SystemExit(main())
