"""Fetch every generation of an Earth run and summarise it for analysis.

Usage (from repo root, next to earth/earth_client.py):
    python earth/fetch_history.py --name run1
    python earth/fetch_history.py --experiment <experiment_id> --out work/analysis/exp

Reads the experiment id from work/runs/<name>/earth_ids.json, downloads
GET /api/experiments/{id}/{generation}/population for generation 0, 1, 2, ...
until Earth has no more, and writes into the run folder:

    history.csv   one row per candidate: generation, id, score, how it was made
                  (crossover / mutation / elite), parents, every gene, every scalar
    history.json  the raw API responses

Then prints: best and mean score per generation, how many candidates failed
(fitness error) or scored at the floor (e.g. a candidate that loses money), how the main genes were distributed in the first vs last
generations, and the top 5 distinct candidates of the whole run.
Read-only: it never changes anything on Earth.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from earth_client import BASE, auth  # noqa: E402

ERROR_SCORE_CEILING = 1e-6
MAX_GENERATIONS = 1000
PAUSE_SECONDS = 0.5


def get_population(session, headers, exp_id: str, gen: int):
    """One generation, with polite pacing and retries when Earth rate-limits (HTTP 429)."""
    for attempt in range(6):
        resp = session.get(f"{BASE}/api/experiments/{exp_id}/{gen}/population", headers=headers, timeout=60)
        if resp.status_code != 429:
            return resp
        wait = float(resp.headers.get("Retry-After") or 2 ** (attempt + 1))
        print(f"  rate-limited by Earth; waiting {wait:.0f} s...", flush=True)
        time.sleep(wait)
    return resp


def fetch(session, headers, exp_id: str) -> list[dict]:
    pages = []
    for gen in range(MAX_GENERATIONS):
        resp = get_population(session, headers, exp_id, gen)
        time.sleep(PAUSE_SECONDS)
        if resp.status_code == 404:
            break
        resp.raise_for_status()
        items = resp.json()
        if not items:
            break
        pages.extend(items)
        print(f"  generation {gen}: {len(items)} candidates", flush=True)
    return pages


def flatten(pages: list[dict]) -> pd.DataFrame:
    rows = []
    for item in pages:
        ind = item.get("individual") or {}
        row = {
            "generation": item.get("generation"),
            "id": ind.get("id"),
            "score": ind.get("fitness_score"),
            "made_by": "+".join(ind.get("dynasty_value") or []),
            "parents": " ".join(str(p) for p in ind.get("parent_ids") or []),
        }
        for gene, value in (ind.get("chromosome") or {}).items():
            if isinstance(value, list):
                row[f"gene.{gene}"] = "".join("1" if v else "0" for v in value) if all(isinstance(v, bool) for v in value) else json.dumps(value)
            elif isinstance(value, dict):
                row[f"gene.{gene}"] = json.dumps(value, sort_keys=True)
            else:
                row[f"gene.{gene}"] = value
        for key, value in ((ind.get("fitness_composition") or {}).get("scalars") or {}).items():
            if isinstance(value, dict):
                for sub, v in value.items():
                    row[f"scalar.{key}.{sub}"] = v
            else:
                row[f"scalar.{key}"] = value
        rows.append(row)
    return pd.DataFrame(rows)


def summarise(df: pd.DataFrame) -> None:
    pd.set_option("display.width", 200)
    per_gen = df.groupby("generation").score.agg(best="max", mean="mean", worst="min", n="size")
    err = df["scalar.error"].fillna(0).astype(bool) if "scalar.error" in df else pd.Series(False, index=df.index)
    floor = (df.score <= ERROR_SCORE_CEILING) & ~err
    per_gen["errors"] = err.groupby(df.generation).sum()
    per_gen["at_floor"] = floor.groupby(df.generation).sum()
    print("\n1) Score per generation")
    print(per_gen.round(4).to_string())

    genes = [c for c in df.columns if c.startswith("gene.") and df[c].nunique() <= 10]
    first = df[df.generation <= df.generation.min() + 2]
    last = df[df.generation >= df.generation.max() - 2]
    print("\n2) Gene distributions: first 3 vs last 3 generations (share of candidates)")
    for gene in genes:
        a = first[gene].value_counts(normalize=True).round(2).to_dict()
        b = last[gene].value_counts(normalize=True).round(2).to_dict()
        print(f"  {gene[5:]:<28} first {a}\n  {'':<28} last  {b}")

    gene_cols = [c for c in df.columns if c.startswith("gene.")]
    distinct = df.sort_values("score", ascending=False).drop_duplicates(subset=gene_cols)
    show = ["generation", "score", "made_by"] + [c for c in df.columns if c.startswith("scalar.") and c.endswith("_std")]
    show += [c for c in ("gene.model_family",) if c in df.columns]
    print("\n3) Top 5 distinct candidates of the whole run")
    print(distinct[show].head(5).round(4).to_string(index=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", help="Run name under work/runs/")
    parser.add_argument("--experiment", help="Experiment id (instead of --name)")
    parser.add_argument("--out", type=Path, help="Output folder (default: the run folder)")
    args = parser.parse_args()

    if args.name:
        run_dir = _REPO_ROOT / "work" / "runs" / args.name
        ids_path = run_dir / "earth_ids.json"
        if not ids_path.is_file():
            print(f"Missing {ids_path.relative_to(_REPO_ROOT)}", flush=True)
            return 1
        exp_id = json.loads(ids_path.read_text(encoding="utf-8"))["experiment_id"]
        out = args.out or run_dir
    elif args.experiment:
        exp_id = args.experiment
        out = args.out or (_REPO_ROOT / "work" / "analysis" / exp_id)
    else:
        parser.error("pass --name or --experiment")
    out.mkdir(parents=True, exist_ok=True)

    session, headers = auth(password_only=True)
    print(f"Fetching generations of experiment {exp_id}...", flush=True)
    pages = fetch(session, headers, exp_id)
    if not pages:
        print("No generations returned (wrong id, or the run has not started).", flush=True)
        return 1
    (out / "history.json").write_text(json.dumps(pages), encoding="utf-8")
    df = flatten(pages)
    df.to_csv(out / "history.csv", index=False)
    print(f"Wrote {len(df)} candidates to {out / 'history.csv'}", flush=True)
    summarise(df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
