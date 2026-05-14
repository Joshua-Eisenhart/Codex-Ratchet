#!/usr/bin/env python3
"""Build a dry-run quarantine manifest for one generated v4 probe family."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parents[3]
PROBES = ROOT / "system_v4" / "probes"
ADMISSION_DIR = ROOT / "system_v5" / "ops" / "wizard_admissions"
OUT_DIR = ROOT / "system_v5" / "ops" / "queue_cleanup"


def git_status_map() -> dict[str, str]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "--", str(PROBES.relative_to(ROOT))],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    statuses: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if not line:
            continue
        statuses[line[3:]] = line[:2].strip()
    return statuses


def admitted_stems() -> set[str]:
    if not ADMISSION_DIR.exists():
        return set()
    return {path.stem for path in ADMISSION_DIR.glob("*.json")}


def select_family(family: str, statuses: dict[str, str], admitted: set[str]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
    rows = []
    excluded = []
    errors = []
    pattern = f"sim_{family}_"
    for path in sorted(PROBES.glob(f"{pattern}*_survivor_classes.py")):
        rel = path.relative_to(ROOT).as_posix()
        status = statuses.get(rel, "tracked_or_clean")
        stem = path.stem
        is_admitted = stem in admitted or stem.removeprefix("sim_") in admitted
        if is_admitted:
            excluded.append(
                {
                    "path": rel,
                    "git_status": status,
                    "is_admitted_reference": True,
                    "excluded_reason": "admitted reference",
                }
            )
            continue
        row_errors = []
        if status != "??":
            row_errors.append(f"not untracked: {status}")
        if not path.is_file():
            row_errors.append("missing file")
        if path.parent != PROBES:
            row_errors.append("outside direct probe directory")
        if row_errors:
            errors.append(f"{rel}: {', '.join(row_errors)}")
        rows.append(
            {
                "path": rel,
                "git_status": status,
                "is_admitted_reference": is_admitted,
                "proposed_action": "quarantine_by_manifest",
                "dry_run_only": True,
            }
        )
    if not rows:
        errors.append(f"no files selected for family {family}")
    return rows, excluded, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", default="toponetx_simplex_width")
    parser.add_argument("--out", type=pathlib.Path)
    args = parser.parse_args()

    statuses = git_status_map()
    admitted = admitted_stems()
    rows, excluded, errors = select_family(args.family, statuses, admitted)
    status_counts = Counter(str(row["git_status"]) for row in rows)
    out = args.out or OUT_DIR / f"v4_quarantine_dry_run_manifest_{args.family}_20260514.json"
    manifest = {
        "schema": "V4_QUARANTINE_DRY_RUN_MANIFEST_v1",
        "family": args.family,
        "scope": "system_v4/probes direct files only",
        "dry_run_only": True,
        "move_executed": False,
        "selected_count": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "excluded_admitted_reference_count": len(excluded),
        "errors": errors,
        "pass": not errors,
        "destination_if_approved": f"system_v5/ops/quarantine/{args.family}/",
        "selection_rule": f"untracked direct files matching sim_{args.family}_*_survivor_classes.py",
        "excluded_admitted_references": excluded[:200],
        "rows": rows,
    }
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: manifest[key] for key in ["schema", "family", "selected_count", "status_counts", "errors", "pass"]}, indent=2, sort_keys=True))
    return 0 if manifest["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
