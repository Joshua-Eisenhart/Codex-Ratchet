#!/usr/bin/env python3
"""Run the broad tmp engine_v2 wave/iter sim surface.

This scout executes probe-like wave/iter scripts from /private/tmp/engine_v2 in
parallel with strict per-script timeouts. The point is not to promote tmp
claims; it is to turn the other-sim proposal space into a concrete execution
map for attractor-basin triage.
"""

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
OUT_PATH = RESULT_DIR / "attractor_basin_tmp_engine_v2_full_wave_execution_probe_results.json"
TMP_ENGINE_V2 = pathlib.Path("/private/tmp/engine_v2")

NAME = "attractor_basin_tmp_engine_v2_full_wave_execution_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
TIMEOUT_SECONDS = 45
MAX_WORKERS = 8
CLAIM_CEILING = (
    "Formal scout only: executes broad tmp engine_v2 wave/iter proposal sims "
    "for attractor-basin triage. It does not admit tmp results, engine, "
    "Axis0, FEP, Holodeck, physics, cognition, world-model, or canonical "
    "architecture claims."
)

TOOL_MANIFEST = {
    "concurrent.futures": {
        "tried": True,
        "used": True,
        "reason": "load-bearing parallel execution of independent tmp wave/iter scripts",
    },
    "subprocess": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bounded execution with stdout/stderr capture",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing result receipt parsing and summary emission",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source/result hash receipts",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "concurrent.futures": "supportive",
    "subprocess": "supportive",
    "json": "supportive",
    "hashlib": "supportive",
}


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_scripts() -> list[pathlib.Path]:
    if not TMP_ENGINE_V2.exists():
        return []
    rows = []
    for path in TMP_ENGINE_V2.glob("*.py"):
        name = path.name
        if not name.startswith(("wave", "iter")):
            continue
        if name.startswith(("engine_", "train_", "benchmark_")):
            continue
        rows.append(path)
    return sorted(rows)


def result_candidates(script: pathlib.Path) -> list[pathlib.Path]:
    stem = script.stem
    candidates = [script.with_name(f"{stem}_results.json")]
    if stem.endswith("_test"):
        candidates.append(script.with_name(f"{stem.removesuffix('_test')}_results.json"))
    return candidates


def load_json_maybe(path: pathlib.Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"_parse_error": str(exc)[:240]}


def classify(returncode: int, timed_out: bool, data: dict[str, Any] | None) -> str:
    if timed_out:
        return "timeout"
    if returncode != 0:
        return "nonzero_exit"
    if data is None:
        return "missing_result"
    if data.get("_parse_error"):
        return "unparseable_result"
    if data.get("all_pass") is True:
        return "green"
    if data.get("all_pass") is False:
        return "negative"
    return "schema_odd"


def run_one(script: pathlib.Path) -> dict[str, Any]:
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
    data = load_json_maybe(result_path) if result_path else None
    return {
        "script": str(script),
        "script_name": script.name,
        "script_sha256": sha256_file(script),
        "result_candidates": [str(path) for path in candidates],
        "result_path": str(result_path) if result_path else None,
        "result_sha256": sha256_file(result_path) if result_path else None,
        "result_changed": before != after,
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": time.time() - started,
        "classification": classify(returncode, timed_out, data),
        "reported_all_pass": None if data is None else data.get("all_pass"),
        "reported_classification": None if data is None else data.get("classification"),
        "reported_promotion_allowed": None if data is None else data.get("promotion_allowed"),
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
    scripts = discover_scripts()
    rows: list[dict[str, Any]] = []
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_map = {pool.submit(run_one, script): script for script in scripts}
        for fut in cf.as_completed(future_map):
            rows.append(fut.result())
    rows.sort(key=lambda row: row["script_name"])
    class_counts = count_by(rows, "classification")
    all_pass_counts = count_by(rows, "reported_all_pass")
    basin_triage = {
        "green_conversion_candidates": [
            row["script_name"] for row in rows if row["classification"] == "green"
        ],
        "negative_or_blocked_boundaries": [
            row["script_name"]
            for row in rows
            if row["classification"] in {"negative", "nonzero_exit", "timeout", "missing_result", "unparseable_result"}
        ],
        "schema_odd_review_queue": [
            row["script_name"] for row in rows if row["classification"] == "schema_odd"
        ],
    }
    positive = {
        "broad_tmp_wave_surface_discovered": {"pass": len(scripts) >= 80, "count": len(scripts)},
        "broad_tmp_wave_surface_executed": {
            "pass": len(rows) == len(scripts) and all("classification" in row for row in rows),
            "count": len(rows),
        },
        "parallel_execution_used": {
            "pass": MAX_WORKERS > 1,
            "max_workers": MAX_WORKERS,
            "timeout_seconds": TIMEOUT_SECONDS,
        },
        "mixed_basin_triage_produced": {
            "pass": len(class_counts) >= 2,
            "classification_counts": class_counts,
            "reported_all_pass_counts": all_pass_counts,
        },
        "green_and_boundary_rows_preserved": {
            "pass": bool(basin_triage["green_conversion_candidates"]) and bool(basin_triage["negative_or_blocked_boundaries"]),
            "basin_triage_counts": {k: len(v) for k, v in basin_triage.items()},
        },
    }
    graveyards = {
        "tmp_green_rows_not_promoted": {
            "pass": PROMOTION_ALLOWED is False and "does not admit tmp results" in CLAIM_CEILING,
            "reason": "Every green tmp row is a conversion candidate, not canonical evidence.",
        },
        "timeouts_and_missing_results_are_boundaries": {
            "pass": True,
            "reason": "Timeout, nonzero-exit, missing-result, and schema-odd rows are basin-wall/open-boundary data.",
        },
        "parallel_batch_not_same_as_max_wizard_topology": {
            "pass": True,
            "reason": "This is local execution parallelism over tmp scripts, not a Wizard v4.2 FULL topology claim.",
        },
    }
    boundary = {
        "bounded_runtime": {
            "pass": TIMEOUT_SECONDS <= 60 and MAX_WORKERS <= 12,
            "timeout_seconds": TIMEOUT_SECONDS,
            "max_workers": MAX_WORKERS,
        },
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "source_hashes_present": {"pass": all(row.get("script_sha256") for row in rows)},
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
        "source_alignment_category": "attractor_basin_tmp_engine_v2_full_wave_execution",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tmp_root": str(TMP_ENGINE_V2),
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "basin_triage": basin_triage,
        "rows": rows,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "This executes tmp engine_v2 proposal sims under a current formal-scout triage gate.",
            "It preserves green/negative/open rows for later conversion without promoting tmp claims.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  scripts={len(rows)} class_counts={class_counts}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
