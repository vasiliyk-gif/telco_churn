"""Local pre-flight check: does this chromosome + fitness pair run on your laptop?

Usage (from repo root):
    python earth/check_local.py
    python earth/check_local.py --chromosome work/runs/run2/chromosome.yaml
    python earth/check_local.py --fitness work/runs/run3/fitness.py --train work/exploration/train.csv

Builds one sample chromosome per model family from the YAML (first enum value,
middle of every range, bools and bool arrays on), copies the training CSV (and any --assets)
into a temporary folder the way Earth does, runs FitnessClass on it, and checks
every score is finite and positive. Catches wrong array sizes, enum values the
fitness does not know, and broken fitness code before you spend an Earth run.
Then prints a rough run estimate from the slowest call. The fitness fits each
model 4 times per fold (3 inner folds to pick the share to call, then the full
training part), so one call takes 3-4 times longer than a single 5-fold CV.
No Earth calls.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import shutil
import sys
import tempfile
import time
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRAIN = _REPO_ROOT / "work" / "exploration" / "train.csv"
DEFAULT_CHROMOSOME = _REPO_ROOT / "work" / "optimization" / "chromosome.yaml"
DEFAULT_FITNESS = _REPO_ROOT / "work" / "optimization" / "fitness.py"
# Scores at or below this are at the error/loss floor (fitness floors scores at 1e-9).
ERROR_SCORE_CEILING = 1e-6
# Class run settings (run_search.py defaults) and a typical length, for the run estimate.
CLASS_POP, CLASS_UNITS, CLASS_MINUTES, TYPICAL_GENERATIONS = 10, 5, 15, 40


def load_fitness_module(path: Path):
    spec = importlib.util.spec_from_file_location("fitness_under_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_gene(spec: dict):
    """A deterministic value for one gene definition."""
    kind = spec.get("type")
    if kind == "enum":
        return spec["values"][0]
    if kind == "int":
        return int(round((spec["min_value"] + spec["max_value"]) / 2))
    if kind == "float":
        return (spec["min_value"] + spec["max_value"]) / 2
    if kind == "bool":
        return True
    if kind == "array":
        if (spec.get("item_definition") or {}).get("type") != "bool":
            raise ValueError("only bool arrays are supported by this check")
        return [True] * int(spec["max_size"])
    if kind == "dict":
        return {name: sample_gene(sub) for name, sub in (spec.get("content") or {}).items()}
    raise ValueError(f"unsupported gene type {kind!r}")


def sample_chromosomes(chromosome_yaml: Path) -> list[dict]:
    doc = yaml.safe_load(chromosome_yaml.read_text(encoding="utf-8")) or {}
    content = (doc.get("chromosome") or {}).get("content")
    if not isinstance(content, dict):
        raise ValueError(f"{chromosome_yaml} has no chromosome.content mapping")
    base = {name: sample_gene(spec) for name, spec in content.items()}
    families = (content.get("model_family") or {}).get("values") or [None]
    samples = []
    for family in families:
        sample = dict(base)
        if family is not None:
            sample["model_family"] = family
        samples.append(sample)
    return samples


def check(chromosome_yaml: Path, fitness_py: Path, train_csv: Path = DEFAULT_TRAIN,
          assets: "list[Path] | None" = None) -> bool:
    """Return True when every sample chromosome scores without error."""
    print(f"Local check: {chromosome_yaml.name} + {fitness_py.name} on {train_csv.name}", flush=True)
    for path in [chromosome_yaml, fitness_py, train_csv, *(assets or [])]:
        if not Path(path).is_file():
            print(f"  FAILED: missing {path}", flush=True)
            return False
    try:
        samples = sample_chromosomes(chromosome_yaml)
        module = load_fitness_module(fitness_py)
    except Exception as exc:  # noqa: BLE001 — report any setup error plainly
        print(f"  FAILED before scoring: {exc}", flush=True)
        return False

    ok = True
    slowest = 0.0
    with tempfile.TemporaryDirectory(prefix="earth_local_check_") as tmp:
        for path in [train_csv, *(assets or [])]:
            shutil.copy(path, Path(tmp) / Path(path).name)
        try:
            fitness = module.FitnessClass(tmp)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED loading data in FitnessClass: {exc}", flush=True)
            return False
        for sample in samples:
            label = sample.get("model_family", "sample")
            try:
                started = time.perf_counter()
                result = fitness.calculate_fitness(sample)
                seconds = time.perf_counter() - started
                score = float(result.score)
            except Exception as exc:  # noqa: BLE001
                print(f"  {label}: FAILED: {exc}", flush=True)
                ok = False
                continue
            if (result.scalars or {}).get("error"):
                print(f"  {label}: FAILED: fitness reported an error (see 'fitness error' above)", flush=True)
                ok = False
            elif not math.isfinite(score) or score <= 0:
                print(f"  {label}: FAILED: score {score!r} must be finite and > 0", flush=True)
                ok = False
            elif score <= ERROR_SCORE_CEILING:
                print(f"  {label}: score={score:.3g} (at the floor: this sample candidate scores at or below zero; fine if expected)", flush=True)
            else:
                print(f"  {label}: score={score:.4f}  ({seconds:.1f} s for one fitness call)", flush=True)
            slowest = max(slowest, seconds)
    if ok and slowest > 0:
        rounds = math.ceil(CLASS_POP / CLASS_UNITS)
        minutes = TYPICAL_GENERATIONS * rounds * slowest / 60
        print(
            f"Run estimate: slowest call {slowest:.1f} s x {rounds} rounds per generation "
            f"(population {CLASS_POP}, {CLASS_UNITS} workers) x {TYPICAL_GENERATIONS} generations "
            f"= about {minutes:.0f} min on a laptop-speed worker (class cap {CLASS_MINUTES} min). "
            "Sample genes sit mid-range; the largest models in your ranges are slower.",
            flush=True,
        )
    print("Local check OK." if ok else "Local check FAILED.", flush=True)
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--chromosome", type=Path, default=DEFAULT_CHROMOSOME)
    parser.add_argument("--fitness", type=Path, default=DEFAULT_FITNESS)
    parser.add_argument("--train", type=Path, default=DEFAULT_TRAIN, help="Training CSV, as uploaded to Earth")
    parser.add_argument("--assets", type=Path, nargs="*", default=[], help="Extra files uploaded with the training CSV")
    args = parser.parse_args()
    return 0 if check(args.chromosome, args.fitness, args.train, args.assets) else 1


if __name__ == "__main__":
    sys.exit(main())
