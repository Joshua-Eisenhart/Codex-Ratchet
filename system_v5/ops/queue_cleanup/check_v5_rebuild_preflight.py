#!/usr/bin/env python3
"""Preflight for v5 clean rebuild batches."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import hashlib


ROOT = pathlib.Path(__file__).resolve().parents[3]
V4_PROBES = pathlib.Path("system_v4/probes")
V4_BASELINE = pathlib.Path("system_v5/ops/queue_cleanup/v4_probe_status_baseline_20260514.json")
V5_ALLOWED_PREFIXES = (
    "system_v5/docs/",
    "system_v5/ops/formal_scouts/",
    "system_v5/ops/queue_cleanup/",
    "system_v5/ops/quarantine/",
    "system_v5/evidence/",
    ".tmp/",
)
GENERATED_SIZE_WARNING_BYTES = 1_000_000


def git_status() -> list[dict[str, str]]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    rows = []
    for line in proc.stdout.splitlines():
        if not line:
            continue
        rows.append({"status": line[:2].strip(), "path": line[3:]})
    return rows


def staged_files() -> list[pathlib.Path]:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [pathlib.Path(line) for line in proc.stdout.splitlines() if line]


def path_status(scope: pathlib.Path) -> list[dict[str, str]]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "--", scope.as_posix()],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    rows = []
    for line in proc.stdout.splitlines():
        if not line:
            continue
        rows.append({"status": line[:2].strip(), "path": line[3:]})
    return rows


def status_digest(rows: list[dict[str, str]]) -> str:
    payload = "\n".join(sorted(f"{row['status']}\t{row['path']}" for row in rows)) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def status_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        key: sum(1 for row in rows if row["status"] == key)
        for key in sorted({row["status"] for row in rows})
    }


def main() -> int:
    status_rows = git_status()
    staged = staged_files()
    errors = []
    warnings = []

    staged_v4 = [str(path) for path in staged if path.parts[:2] == V4_PROBES.parts]
    if staged_v4:
        errors.append({"kind": "staged_v4_probe_change", "paths": staged_v4[:50], "count": len(staged_v4)})

    if V4_BASELINE.exists():
        baseline = json.loads((ROOT / V4_BASELINE).read_text(encoding="utf-8"))
        v4_rows = path_status(V4_PROBES)
        v4_digest = status_digest(v4_rows)
        if v4_digest != baseline.get("status_sha256"):
            errors.append(
                {
                    "kind": "v4_probe_reference_state_drift",
                    "scope": V4_PROBES.as_posix(),
                    "baseline_count": baseline.get("status_count"),
                    "current_count": len(v4_rows),
                    "baseline_status_counts": baseline.get("status_counts"),
                    "current_status_counts": status_counts(v4_rows),
                    "baseline_sha256": baseline.get("status_sha256"),
                    "current_sha256": v4_digest,
                    "next": "Treat this as a stop condition unless the batch intentionally updates v4/probes by manifest.",
                }
            )
    else:
        warnings.append({"kind": "missing_v4_probe_status_baseline", "path": V4_BASELINE.as_posix()})

    staged_outside = [
        str(path)
        for path in staged
        if not any(path.as_posix().startswith(prefix) for prefix in V5_ALLOWED_PREFIXES)
    ]
    if staged_outside:
        warnings.append({"kind": "staged_outside_v5_rebuild_surfaces", "paths": staged_outside[:50], "count": len(staged_outside)})

    large_staged = []
    for path in staged:
        full = ROOT / path
        if full.exists() and full.stat().st_size > GENERATED_SIZE_WARNING_BYTES:
            large_staged.append({"path": str(path), "bytes": full.stat().st_size})
    if large_staged:
        warnings.append({"kind": "large_staged_artifact", "files": large_staged})

    pycache_dirs = [str(path.relative_to(ROOT)) for path in (ROOT / "system_v5" / "ops").rglob("__pycache__")]
    if pycache_dirs:
        errors.append({"kind": "runtime_byproduct_pycache", "paths": pycache_dirs})

    summary = {
        "schema": "V5_REBUILD_PREFLIGHT_v1",
        "staged_count": len(staged),
        "status_counts": {
            key: sum(1 for row in status_rows if row["status"] == key)
            for key in sorted({row["status"] for row in status_rows})
        },
        "errors": errors,
        "warnings": warnings,
        "pass": not errors,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
