#!/usr/bin/env python3
"""Negative control proving result source pins are load-bearing in gate_check.py."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "system_v5/ops/formal_scouts/results"
GATE_CHECK = ROOT / "scripts/gate_check.py"
PATTERNS = ("foundation_*results.json", "foundation_foundation_*results.json")
WRONG_SHA = "0" * 64


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def resolve_path(value: Any) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    if not path.is_absolute():
        path = ROOT / path
    return path


def foundation_results(results_dir: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in PATTERNS:
        files.update(results_dir.glob(pattern))
    return sorted(files)


def run_gate(source: Path, result: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(GATE_CHECK), str(source), str(result)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = completed.stdout.strip()
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = {"unparsed_stdout": stdout}
    parsed["returncode"] = completed.returncode
    parsed["stderr"] = completed.stderr.strip()
    return parsed


def find_passing_rung(results_dir: Path) -> tuple[Path, Path, dict[str, Any]]:
    for result_path in foundation_results(results_dir):
        payload = load_json(result_path)
        if not payload.get("source_sha256"):
            continue
        source_path = resolve_path(payload.get("source_path"))
        if source_path is None or not source_path.exists():
            continue
        gate = run_gate(source_path, result_path)
        if gate.get("status") == "PASS" and not gate.get("warnings"):
            return source_path, result_path, gate
    raise RuntimeError("no passing hash-pinned foundation rung found")


def poison_copy(result_path: Path, source_path: Path, temp_dir: Path) -> Path:
    poisoned = temp_dir / result_path.name
    shutil.copy2(result_path, poisoned)
    payload = load_json(poisoned)
    original_sha = payload.get("source_sha256")
    if original_sha == WRONG_SHA:
        payload["source_sha256"] = "1" * 64
    else:
        payload["source_sha256"] = WRONG_SHA
    poisoned.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    stale_mtime = max(source_path.stat().st_mtime - 3600, 0)
    os.utime(poisoned, (stale_mtime, stale_mtime))
    return poisoned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()

    source_path, result_path, clean_gate = find_passing_rung(args.results_dir)
    with tempfile.TemporaryDirectory(prefix="gate_load_bearing_") as raw_temp:
        temp_dir = Path(raw_temp)
        poisoned = poison_copy(result_path, source_path, temp_dir)
        poisoned_gate = run_gate(source_path, poisoned)

    reasons = poisoned_gate.get("reasons") or []
    hash_reason = any("source_sha256 does not match" in str(reason) for reason in reasons)
    ok = clean_gate.get("status") == "PASS" and poisoned_gate.get("status") == "BLOCK" and hash_reason
    report = {
        "ok": ok,
        "source": str(source_path),
        "clean_result": str(result_path),
        "clean_status": clean_gate.get("status"),
        "clean_gate": clean_gate,
        "poisoned_status": poisoned_gate.get("status"),
        "poisoned_gate": poisoned_gate,
        "flip": f"{clean_gate.get('status')} -> {poisoned_gate.get('status')}",
        "hash_mismatch_reason_present": hash_reason,
        "poison_controls": {
            "wrong_source_sha256": True,
            "stale_mtime": True,
            "temp_copy_removed": True,
        },
    }
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
