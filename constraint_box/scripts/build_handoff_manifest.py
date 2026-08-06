#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import py_compile
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "HANDOFF_MANIFEST.json"
VERIFICATION = ROOT / "receipts" / "BUILD_VERIFICATION.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def run_tests() -> dict[str, Any]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        env=environment,
        timeout=60,
    )
    combined = proc.stdout + proc.stderr
    match = re.search(rb"Ran ([0-9]+) tests", combined)
    return {
        "command": "PYTHONPATH=src python -m unittest discover -s tests -v",
        "exit_code": proc.returncode,
        "test_count": int(match.group(1)) if match else None,
        "output_sha256": hashlib.sha256(combined).hexdigest(),
        "ok_marker": b"\nOK\n" in combined or combined.rstrip().endswith(b"OK"),
    }


def validate_sources_and_json() -> dict[str, Any]:
    python_files = sorted(
        path
        for base in (ROOT / "src", ROOT / "workers", ROOT / "scripts")
        for path in base.rglob("*.py")
    )
    for path in python_files:
        py_compile.compile(str(path), doraise=True)
    json_files = sorted(
        path
        for path in ROOT.rglob("*.json")
        if path not in {MANIFEST, VERIFICATION}
    )
    for path in json_files:
        json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=no_duplicate_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON constant: {value}")
            ),
        )
    return {
        "python_files_compiled": len(python_files),
        "json_files_strictly_parsed": len(json_files),
    }


def receipt_summary() -> list[dict[str, Any]]:
    rows = []
    for path in sorted((ROOT / "receipts").glob("*.json")):
        if path == VERIFICATION:
            continue
        body = json.loads(path.read_text(encoding="utf-8"))
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha(path),
                "schema": body.get("schema"),
                "state": body.get("state") or body.get("disposition"),
                "tier": body.get("layer_id") or body.get("tier_id"),
            }
        )
    return rows


def inventory() -> list[dict[str, Any]]:
    rows = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path in {MANIFEST, VERIFICATION}:
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha(path),
            }
        )
    return rows


def main() -> None:
    checks = validate_sources_and_json()
    tests = run_tests()
    receipts = receipt_summary()
    verification = {
        "schema": "constraintbox.build-verification.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tests": tests,
        "checks": checks,
        "receipt_states": receipts,
        "promotion_allowed": False,
    }
    if tests["exit_code"] != 0 or not tests["ok_marker"]:
        raise SystemExit("test suite failed; manifest not finalized")
    VERIFICATION.write_text(
        json.dumps(verification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema": "constraintbox.handoff-manifest.v1",
        "package": "CONSTRAINTBOX_UNIFIED_SIM_SYSTEM_20260725_v4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "build_verification_sha256": sha(VERIFICATION),
        "files": inventory(),
        "promotion_allowed": False,
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
