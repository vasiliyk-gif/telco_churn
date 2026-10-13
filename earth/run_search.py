"""Upload train.csv, launch a short Earth GA run, save the champion.

Run from repo root (requires .env):
    python earth/run_search.py

Abort after generation >= 5 (teaching budget). time_limit=15 minutes is a safety cap.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from earth_client import (  # noqa: E402
    CHURN_TEMPLATE_ID,
    abort,
    auth,
    clone_template,
    launch,
    poll,
    upload_dataset,
)

TRAIN_CSV = _REPO_ROOT / "work" / "exploration" / "train.csv"
CHROMOSOME = _REPO_ROOT / "work" / "modeling" / "chromosome.yaml"
FITNESS_PY = _REPO_ROOT / "work" / "modeling" / "fitness.py"
PIPELINE_PY = _REPO_ROOT / "work" / "modeling" / "pipeline.py"
OUT_DIR = _REPO_ROOT / "work" / "optimization"
TARGET_GENERATION = 5
POLL_SECONDS = 30


def main() -> int:
    if not TRAIN_CSV.is_file():
        print(f"Missing {TRAIN_CSV}. Run prepare_data.py first.", flush=True)
        return 1
    for path in (CHROMOSOME, FITNESS_PY, PIPELINE_PY):
        if not path.is_file():
            print(f"Missing {path}", flush=True)
            return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Authenticating (password_only=True)...", flush=True)
    session, headers = auth(password_only=True)

    name = f"workshop1-churn-{int(time.time())}"
    print(f"Uploading {TRAIN_CSV} as dataset '{name}'...", flush=True)
    dataset_id = upload_dataset(session, headers, str(TRAIN_CSV), name)

    print("Cloning template / creating project...", flush=True)
    project_id = clone_template(
        session, headers, CHURN_TEMPLATE_ID, dataset_id, name
    )

    print("Launching experiment...", flush=True)
    exp_id = launch(
        session,
        headers,
        project_id,
        dataset_id,
        chromo_path=str(CHROMOSOME),
        code_files=[str(FITNESS_PY), str(PIPELINE_PY)],
        pop=12,
        units=4,
        minutes=15,
        maximize=True,
        enable_genetic_drift=False,
        generation_start_steady=1000,
        max_stagnation_loops=100,
        max_drifts=100,
    )

    ids = {
        "dataset_id": dataset_id,
        "project_id": project_id,
        "experiment_id": exp_id,
        "train_csv": str(TRAIN_CSV.relative_to(_REPO_ROOT)),
        "chromosome": str(CHROMOSOME.relative_to(_REPO_ROOT)),
    }
    (OUT_DIR / "earth_ids.json").write_text(
        json.dumps(ids, indent=2), encoding="utf-8"
    )
    print(json.dumps(ids, indent=2), flush=True)

    aborted_for_budget = False
    while True:
        time.sleep(POLL_SECONDS)
        state = poll(session, headers, exp_id)
        status = state.get("status")
        gen = state.get("generation")
        score = state.get("score")
        print(
            f"  [{status}] gen={gen} score={score}",
            flush=True,
        )
        if status in ("COMPLETED", "STAGNATED", "ERROR", "ABORTED"):
            break
        try:
            gen_i = int(gen) if gen is not None else -1
        except (TypeError, ValueError):
            gen_i = -1
        if gen_i >= TARGET_GENERATION and not aborted_for_budget:
            print(
                f"Teaching budget reached (generation {gen_i}). Aborting...",
                flush=True,
            )
            abort(session, headers, exp_id)
            aborted_for_budget = True

    final = poll(session, headers, exp_id)
    champion = {
        "experiment_id": exp_id,
        "status": final.get("status"),
        "generation": final.get("generation"),
        "fitness_score": final.get("score"),
        "scalars": final.get("scalars") or {},
        "chromosome": final.get("chromosome"),
        "aborted_for_teaching_budget": aborted_for_budget,
    }
    champ_path = OUT_DIR / "champion_chromosome.json"
    champ_path.write_text(json.dumps(champion, indent=2), encoding="utf-8")
    print(f"Wrote {champ_path}", flush=True)

    if final.get("status") == "ERROR":
        print("Experiment ended in ERROR.", flush=True)
        return 1
    if final.get("chromosome") is None:
        print("No champion chromosome returned.", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
