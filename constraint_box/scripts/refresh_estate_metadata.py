#!/usr/bin/env python3
"""Refresh every adopted package from the live PyPI authority.

Writes constraint_box/receipts/estate_metadata_authority_v1.json, which the
hook kernel's `estate_metadata_refreshed` event reads. The kernel recomputes its
verdict from that file; this script only measures.

It does NOT rewrite the local registry. The registry stays as it is, and the
receipt records where the two disagree. Overwriting the registry with PyPI
values would destroy the disagreement, which is the evidence.

Run:
  <interpreter> constraint_box/scripts/refresh_estate_metadata.py
  <interpreter> -m constraint_box.hookkernel.kernel estate_metadata_refreshed

stdlib only.
"""
from __future__ import annotations

import concurrent.futures
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))

from constraint_box.hookkernel.pypi_authority import age_days, compare, fetch  # noqa: E402

STALE_DAYS_MAX = 548


def requirement_names(path):
    if not path.exists():
        return set()
    return {
        re.split(r"[=<>#\s\[]", line.strip())[0]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def main() -> int:
    req = ROOT / "requirements" / "candidates"
    adopted = requirement_names(req / "cb-light-extended.in") | requirement_names(
        req / "cb-candidates-passing.in"
    )
    registry = json.loads(
        (ROOT / "config" / "cb_light_library_candidates.json").read_text(encoding="utf-8")
    )
    declared = {c["pypi_name"]: c.get("verified", {}) for c in registry.get("candidates", [])}

    def one(name):
        observed = fetch(name)
        status, detail = compare(declared.get(name, {}), observed)
        return {
            "name": name,
            "status": status,
            "detail": detail,
            "observed": {
                k: observed.get(k)
                for k in ("latest_version", "release_date", "requires_python", "yanked")
            },
            "age_days": age_days(observed),
            "raw_sha256": observed.get("raw_sha256"),
            "retrieved_at": observed.get("retrieved_at"),
        }

    with concurrent.futures.ThreadPoolExecutor(16) as pool:
        rows = sorted(pool.map(one, sorted(adopted)), key=lambda r: r["name"])

    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    stale_live = [r["name"] for r in rows if (r["age_days"] or 0) > STALE_DAYS_MAX]
    yanked = [r["name"] for r in rows if r["observed"].get("yanked")]

    receipt = {
        "schema": "cb.estate-metadata-authority.v1",
        "authority": "https://pypi.org/pypi/{name}/json",
        "adopted_checked": len(rows),
        "status_counts": counts,
        "stale_by_live_data": stale_live,
        "yanked_current_release": yanked,
        "stale_days_max": STALE_DAYS_MAX,
        "promotion_allowed": False,
        "ceiling": "live PyPI metadata observed with per-row raw response hash; "
                   "no platform, install or integration claim is made here",
        "rows": rows,
    }
    out = ROOT / "receipts" / "estate_metadata_authority_v1.json"
    out.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")

    print(f"adopted checked : {len(rows)}")
    for status, n in sorted(counts.items()):
        print(f"  {status:<32} {n}")
    print(f"stale by LIVE data (>{STALE_DAYS_MAX}d): {len(stale_live)}"
          + (f" -> {', '.join(stale_live)}" if stale_live else ""))
    if yanked:
        print(f"YANKED current release: {', '.join(yanked)}")
    print(f"\nwrote {out}")
    disagree = [r for r in rows if r["status"] == "METADATA_SOURCE_DISAGREEMENT"]
    if disagree:
        print(f"\n{len(disagree)} rows disagree with the authority:")
        for r in disagree:
            for field, sides in r["detail"]["fields"].items():
                print(f"  {r['name']:<24} {field:<16} registry={sides['registry']}  pypi={sides['pypi']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
