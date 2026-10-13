"""Local end-to-end fitness smoke test on train.csv only.

Run from repo root:
    python work/modeling/smoke_fitness.py
"""

from __future__ import annotations

import math
import shutil
import tempfile
from pathlib import Path

from fitness import FitnessClass
from pipeline import BASELINE_CHROMOSOME

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAIN_PATH = REPO_ROOT / "work" / "exploration" / "train.csv"
HOLDOUT_PATH = REPO_ROOT / "work" / "exploration" / "holdout.csv"


def main() -> None:
    if not TRAIN_PATH.is_file():
        raise SystemExit(
            f"Missing {TRAIN_PATH}. Run: python work/exploration/prepare_data.py"
        )

    with tempfile.TemporaryDirectory(prefix="earth_smoke_") as tmp:
        tmp_path = Path(tmp)
        shutil.copy(TRAIN_PATH, tmp_path / "train.csv")
        # Ensure holdout is not present in the fitness data dir.
        assert not (tmp_path / "holdout.csv").exists()
        assert HOLDOUT_PATH.is_file()  # exists elsewhere, unused here

        fitness = FitnessClass(str(tmp_path))
        result = fitness.calculate_fitness(BASELINE_CHROMOSOME)
        score = float(result.score)
        if not math.isfinite(score) or score <= 0:
            raise SystemExit(f"Invalid score: {score!r}")
        scalars = result.scalars or {}
        for key in ("f1", "precision", "recall"):
            if key not in scalars:
                raise SystemExit(f"Missing scalar {key}")
            if not isinstance(scalars[key], (int, float)):
                raise SystemExit(f"Non-numeric scalar {key}={scalars[key]!r}")

        print("Smoke test OK")
        print(f"  score={score}")
        print(f"  scalars={scalars}")


if __name__ == "__main__":
    main()
