"""Student readiness check: authenticate and read a template. No experiment.

Usage:
    python earth/check_connection.py

Requires EARTH_USER / EARTH_PASS in .env (or the environment).
A bad or missing password exits with a clear message.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from earth_client import BASE, CHURN_TEMPLATE_ID, auth  # noqa: E402


def main() -> int:
    print("Authenticating with Earth (password_only=True)...", flush=True)
    try:
        session, headers = auth(password_only=True)
    except RuntimeError as exc:
        print(f"AUTH FAILED: {exc}", flush=True)
        return 1

    if "x-jwt-org-id" not in headers:
        print(
            "AUTH FAILED: missing x-jwt-org-id. "
            "Set EARTH_ORG_ID in .env or use an access token that includes org_id.",
            flush=True,
        )
        return 1

    print(f"GET {BASE}/api/templates/{CHURN_TEMPLATE_ID}", flush=True)
    resp = session.get(
        f"{BASE}/api/templates/{CHURN_TEMPLATE_ID}",
        headers=headers,
        timeout=60,
    )
    if resp.status_code != 200:
        print(
            f"TEMPLATE LOOKUP FAILED: HTTP {resp.status_code} "
            f"body_prefix={resp.text[:200]!r}",
            flush=True,
        )
        return 1
    data = resp.json()
    title = data.get("title") or data.get("name") or "(no title)"
    tid = data.get("id") or CHURN_TEMPLATE_ID
    print(f"Template OK: id={tid} title={title!r}", flush=True)

    print(f"GET {BASE}/api/experiments/running-count", flush=True)
    count_resp = session.get(
        f"{BASE}/api/experiments/running-count",
        headers=headers,
        timeout=30,
    )
    if not count_resp.ok:
        print(
            f"RUNNING-COUNT FAILED: HTTP {count_resp.status_code} "
            f"body_prefix={count_resp.text[:200]!r}",
            flush=True,
        )
        return 1
    print(f"running-count: {count_resp.text.strip()}", flush=True)
    print("Connection check OK.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
