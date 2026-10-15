"""Validate a chromosome YAML against Earth's EVL validator.

Usage:
    python earth/validate_chromosome.py path/to/chromosome.yaml
    python earth/validate_chromosome.py --self-test

Requires EARTH_USER / EARTH_PASS in .env (same as earth_client.py).

Always runs a known-invalid negative control so a "valid" response is not a
rubber stamp.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _REPO_ROOT / ".env"
if _ENV_PATH.is_file():
    for _line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _v = _line.split("=", 1)
        os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from earth_client import BASE, auth  # noqa: E402

VALIDATE_URL = f"{BASE}/api/evl/chromosome/validate"

# Known-invalid: enum gene must use crossover: {type: error}; random is rejected.
INVALID_CHROMOSOME_YAML = """
chromosome:
  type: dict
  generation: { type: per_item, non_required_probability: 0 }
  mutation: { type: random, percentage_to_mutate: 0.15 }
  crossover: { type: per_item_crossover }
  content:
    geometry_family:
      type: enum
      values: [centroid, density, graph, hierarchy]
      generation: { type: uniform }
      mutation: { type: random }
      crossover: { type: random }
"""


def validate_yaml_text(session, headers, chromosome_yaml: str) -> dict:
    """POST a chromosome YAML string to Earth's validator.

    Returns {"valid": bool, "warnings": [...], "errors": [...]}.
    Earth signals rejection with HTTP 400; that is normalized to valid=False.
    """
    parsed = yaml.safe_load(chromosome_yaml)
    if not isinstance(parsed, dict) or "chromosome" not in parsed:
        return {
            "valid": False,
            "warnings": [],
            "errors": ["YAML root must be a mapping with key 'chromosome'"],
        }
    # Send only the chromosome block. A UI-exported YAML also carries
    # fitness_function / ai1 / ai2, which make the validator fail with HTTP 500.
    resp = session.post(VALIDATE_URL, json={"chromosome": parsed["chromosome"]},
                        headers=headers, timeout=60)
    if resp.status_code == 400:
        try:
            detail = resp.json()
        except ValueError:
            detail = resp.text
        return {"valid": False, "warnings": [], "errors": [detail]}
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "valid" in data:
        return data
    return {"valid": True, "warnings": [], "errors": [], "raw": data}


def validate_path(session, headers, path: Path) -> dict:
    return validate_yaml_text(session, headers, path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, help="Chromosome YAML to validate")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Only run the known-invalid negative control",
    )
    args = parser.parse_args()

    if not args.self_test and args.path is None:
        parser.error("pass a chromosome YAML path, or --self-test")

    print("Authenticating with Earth...", flush=True)
    session, headers = auth(password_only=True)

    print("Negative control (known-invalid enum crossover)...", flush=True)
    negative = validate_yaml_text(session, headers, INVALID_CHROMOSOME_YAML)
    print(json.dumps(negative, indent=2, default=str), flush=True)
    if negative.get("valid"):
        print(
            "INCONCLUSIVE: validator accepted a known-invalid chromosome; "
            "cannot trust positive results.",
            flush=True,
        )
        return 2

    if args.self_test:
        print("Negative control OK.", flush=True)
        return 0

    print(f"Validating {args.path}...", flush=True)
    positive = validate_path(session, headers, args.path)
    print(json.dumps(positive, indent=2, default=str), flush=True)

    if not positive.get("valid"):
        print("REJECTED by Earth validator.", flush=True)
        return 1

    print("ACCEPTED by Earth validator (negative control also rejected as expected).", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
