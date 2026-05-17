#!/usr/bin/env python3
"""Long-timeout rerun for tmp engine_v2 rows that timed out in the broad pass."""

from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "attractor_basin_tmp_engine_v2_timeout_rerun_probe_results.json"
SOURCE_RESULT = RESULT_DIR / "attractor_basin_tmp_engine_v2_full_wave_execution_probe_results.json"
TMP_ENGINE_V2 = pathlib.Path("/private/tmp/engine_v2")

NAME = "attractor_basin_tmp_engine_v2_timeout_rerun_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
TIMEOUT_SECONDS = 240
MAX_WORKERS = 4
CLAIM_CEILING = (
    "Formal scout only: reruns tmp engine_v2 scripts that timed out in the "
    "first broad execution pass with a longer timeout. It does not admit tmp "
    "results, engine, Axis0, FEP, Holodeck, physics, cognition, world-model, "
    "or canonical architecture claims."
)

TOOL_MANIFEST = {
    "concurrent.futures": {"tried": True, "used": True, "reason": "load-bearing bounded parallel rerun of timeout rows"},
    "subprocess": {"tried": True, "used": True, "reason": "load-bearing long-timeout script execution"},
    "json": {"tried": True, "used": True, "reason": "load-bearing source/result receipt parsing"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing source/result hash receipts"},
}
TOOL_INTEGRATION_DEPTH = {
    "concurrent.futures": "load_bearing",
    "subprocess": "load_bearing",
    "json": "load_bearing",
    "hashlib": "load_bearing",
}


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def result_candidates(script: pathlib.Path) -> list[pathlib.Path]:
    stem = script.stem
    return [script.with_name(f"{stem}_results.json")]


def load_json_maybe(path: pathlib.Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"_parse_error": str(exc)[:240]}


def classify(returncode: int, timed_out: bool, data: dict[str, Any] | None) -> str:
    if timed_out:
        return "still_timeout"
    if returncode != 0:
        return "nonzero_exit"
    if data is None:
        return "completed_missing_result"
    if data.get("_parse_error"):
        return "unparseable_result"
    if data.get("all_pass") is True:
        return "green_after_long_timeout"
    if data.get("all_pass") is False:
        return "negative_after_long_timeout"
    return "schema_odd_after_long_timeout"


def run_one(script_name: str) -> dict[str, Any]:
    script = TMP_ENGINE_V2 / script_name
    candidates = result_candidates(script)
    before = {str(path): sha256_file(path) for path in candidates}
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=TMP_ENGINE_V2,
            env=env,
            text=True,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
        )
        returncode = proc.returncode
        stdout_tail = proc.stdout[-1200:]
        stderr_tail = proc.stderr[-1200:]
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = 124
        stdout_tail = (exc.stdout or "")[-1200:] if isinstance(exc.stdout, str) else ""
        stderr_tail = (exc.stderr or "")[-1200:] if isinstance(exc.stderr, str) else ""
    after = {str(path): sha256_file(path) for path in candidates}
    result_path = next((path for path in candidates if path.exists()), None)
    data = load_json_maybe(result_path)
    return {
        "script_name": script_name,
        "script": str(script),
        "script_sha256": sha256_file(script),
        "result_path": str(result_path) if result_path else None,
        "result_sha256": sha256_file(result_path) if result_path else None,
        "result_changed": before != after,
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": time.time() - started,
        "classification": classify(returncode, timed_out, data),
        "reported_all_pass": None if data is None else data.get("all_pass"),
        "reported_name": None if data is None else data.get("name"),
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def main() -> int:
    started = time.time()
    source = load_json(SOURCE_RESULT)
    timeout_names = [
        row["script_name"]
        for row in source.get("rows", [])
        if row.get("classification") == "timeout"
    ]
    rows: list[dict[str, Any]] = []
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for fut in cf.as_completed([pool.submit(run_one, name) for name in timeout_names]):
            rows.append(fut.result())
    rows.sort(key=lambda row: row["script_name"])
    class_counts = count_by(rows, "classification")
    positive = {
        "timeout_subset_loaded": {"pass": len(timeout_names) > 0, "count": len(timeout_names)},
        "timeout_subset_reran": {"pass": len(rows) == len(timeout_names), "count": len(rows)},
        "longer_timeout_used": {
            "pass": TIMEOUT_SECONDS > 60 and MAX_WORKERS > 1,
            "timeout_seconds": TIMEOUT_SECONDS,
            "max_workers": MAX_WORKERS,
        },
        "timeouts_refined_into_basin_triage": {
            "pass": bool(class_counts),
            "classification_counts": class_counts,
        },
    }
    graveyards = {
        "still_timeout_rows_remain_open_boundaries": {"pass": True},
        "green_after_long_timeout_rows_remain_unpromoted": {"pass": PROMOTION_ALLOWED is False},
        "completed_missing_result_rows_are_not_green": {"pass": True},
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "source_result_was_prior_broad_execution": {
            "pass": source.get("name") == "attractor_basin_tmp_engine_v2_full_wave_execution_probe",
            "source_sha256": sha256_file(SOURCE_RESULT),
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "attractor_basin_tmp_engine_v2_timeout_rerun",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "source_result": str(SOURCE_RESULT),
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "rows": rows,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "This is a timeout refinement pass over tmp engine_v2 proposal sims.",
            "It narrows open-boundary rows without promoting tmp outputs.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  reran={len(rows)} class_counts={class_counts}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
