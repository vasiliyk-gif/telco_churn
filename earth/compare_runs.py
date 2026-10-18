"""Compare saved Earth runs side by side.

Usage (from repo root):
    python earth/compare_runs.py                 # every run under work/runs/
    python earth/compare_runs.py run1 run2       # just these runs

For each run: status, generations, champion score, the std and per-fold values
your fitness reported (any scalar ending in "_std", any per-fold dictionary),
the other scalars, and the champion's genes side by side. Then the lines of
chromosome.yaml / fitness.py that differ from the first run, so you can see the
one thing you changed.
No Earth calls; reads work/runs/<name>/ only.
"""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = _REPO_ROOT / "work" / "runs"


def load_run(run_dir: Path) -> dict | None:
    champ_path = run_dir / "champion_chromosome.json"
    if not champ_path.is_file():
        return None
    champion = json.loads(champ_path.read_text(encoding="utf-8"))
    genes = champion.get("chromosome") or {}
    genes = genes.get("content", genes)
    scalars = champion.get("scalars") or {}
    std = next((v for k, v in scalars.items() if k.endswith("_std") and not isinstance(v, dict)), None)
    per_fold = next((v for v in scalars.values() if isinstance(v, dict)), {})
    others = {k: v for k, v in scalars.items() if not isinstance(v, dict) and not k.endswith("_std")}
    return {
        "name": run_dir.name,
        "status": champion.get("status"),
        "generation": champion.get("generation"),
        "score": champion.get("fitness_score"),
        "std": std,
        "per_fold": [per_fold[k] for k in sorted(per_fold)],
        "scalars": others,
        "genes": genes,
    }


def fmt(value, digits: int = 4) -> str:
    if isinstance(value, bool) or value is None:
        return "-" if value is None else str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    if isinstance(value, list):
        if all(isinstance(v, bool) for v in value):
            return "".join("1" if v else "0" for v in value)
        return json.dumps(value)
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)


def file_diff(first: Path, other: Path) -> list[str]:
    if not first.is_file() or not other.is_file():
        return []
    return list(difflib.unified_diff(
        first.read_text(encoding="utf-8").splitlines(),
        other.read_text(encoding="utf-8").splitlines(),
        fromfile=str(first.relative_to(_REPO_ROOT)),
        tofile=str(other.relative_to(_REPO_ROOT)),
        n=0,
        lineterm="",
    ))


def table(header: list[str], rows: list[list[str]]) -> None:
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(header)]
    print("  ".join(h.ljust(w) for h, w in zip(header, widths)))
    for r in rows:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="*", help="Run names under work/runs/ (default: all)")
    args = parser.parse_args()

    names = args.runs or sorted(p.name for p in RUNS_DIR.glob("*") if p.is_dir())
    runs = []
    for name in names:
        run = load_run(RUNS_DIR / name)
        if run is None:
            print(f"{name}: no champion_chromosome.json yet (still running? try --collect)")
            continue
        runs.append(run)
    if not runs:
        print(f"No finished runs under {RUNS_DIR.relative_to(_REPO_ROOT)}.")
        return 1

    print()
    table(["run", "status", "gen", "score", "std", "per-fold"],
          [[r["name"], fmt(r["status"]), fmt(r["generation"]), fmt(r["score"]), fmt(r["std"], 3),
            " ".join(fmt(x, 3) for x in r["per_fold"])] for r in runs])

    keys = sorted({k for r in runs for k in r["scalars"]})
    if keys:
        print("\nOther scalars:")
        table(["scalar"] + [r["name"] for r in runs],
              [[k] + [fmt(r["scalars"].get(k), 3) for r in runs] for k in keys])

    genes = list(dict.fromkeys(g for r in runs for g in r["genes"]))
    print("\nChampion genes:")
    table(["gene"] + [r["name"] for r in runs],
          [[g] + [fmt(r["genes"].get(g), 3) for r in runs] for g in genes])

    first = RUNS_DIR / runs[0]["name"]
    for run in runs[1:]:
        other = RUNS_DIR / run["name"]
        for filename in ("chromosome.yaml", "fitness.py"):
            diff = file_diff(first / filename, other / filename)
            if diff:
                print(f"\nWhat {run['name']} changed in {filename} (vs {runs[0]['name']}):")
                print("\n".join(diff))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
