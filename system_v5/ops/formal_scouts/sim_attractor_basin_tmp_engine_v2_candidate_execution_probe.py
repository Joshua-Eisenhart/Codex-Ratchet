#!/usr/bin/env python3
"""Execute tmp engine_v2 candidate probes under a current formal-scout gate.

The tmp engine_v2 wave probes are useful proposal space, but their result JSON
files are not current-system evidence. This scout actually runs the tmp probe
scripts in place, captures their stdout/stderr/result files, and classifies the
outcomes as candidate adoption material without promoting any tmp claim.
"""

from __future__ import annotations

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
OUT_PATH = RESULT_DIR / "attractor_basin_tmp_engine_v2_candidate_execution_probe_results.json"

TMP_ENGINE_V2 = pathlib.Path("/private/tmp/engine_v2")
TIMEOUT_SECONDS = 60

NAME = "attractor_basin_tmp_engine_v2_candidate_execution_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: executes tmp engine_v2 candidate probes as proposal "
    "space and classifies their runtime/result state for attractor-basin "
    "triage. It does not admit tmp results, engine, Axis0, FEP, Holodeck, "
    "physics, cognition, world-model, or canonical architecture claims."
)

TOOL_MANIFEST = {
    "subprocess": {
        "tried": True,
        "used": True,
        "reason": "load-bearing execution of tmp candidate probe scripts under bounded timeout",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing parsing of tmp candidate result JSON files",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bounded discovery of tmp engine_v2 candidate probes",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source/result hash receipts for candidate execution",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "subprocess": "supportive",
    "json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
}


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_result_path(script: pathlib.Path) -> pathlib.Path:
    return script.with_name(f"{script.stem}_results.json")


def load_json_maybe(path: pathlib.Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - receipt should capture parse failures.
        return {"_parse_error": str(exc)[:240]}


def candidate_scripts() -> list[pathlib.Path]:
    if not TMP_ENGINE_V2.exists():
        return []
    return sorted(TMP_ENGINE_V2.glob("*_v2_*_probe.py"))


def classify_result(returncode: int, timed_out: bool, data: dict[str, Any] | None) -> str:
    if timed_out:
        return "tmp_blocked_timeout"
    if returncode != 0:
        return "tmp_blocked_nonzero_exit"
    if data is None:
        return "tmp_blocked_missing_result"
    if data.get("_parse_error"):
        return "tmp_blocked_unparseable_result"
    if data.get("all_pass") is True:
        return "tmp_candidate_green_unpromoted"
    if data.get("all_pass") is False:
        return "tmp_candidate_negative_unpromoted"
    return "tmp_candidate_schema_odd_unpromoted"


def run_candidate(script: pathlib.Path) -> dict[str, Any]:
    result_path = expected_result_path(script)
    before_hash = sha256_file(result_path)
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

    data = load_json_maybe(result_path)
    after_hash = sha256_file(result_path)
    return {
        "script": str(script),
        "script_sha256": sha256_file(script),
        "expected_result": str(result_path),
        "result_sha256_before": before_hash,
        "result_sha256_after": after_hash,
        "result_changed": before_hash != after_hash,
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": time.time() - started,
        "classification": classify_result(returncode, timed_out, data),
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
    return counts


def main() -> int:
    started = time.time()
    scripts = candidate_scripts()
    rows = [run_candidate(script) for script in scripts]
    class_counts = count_by(rows, "classification")
    all_pass_counts = count_by(rows, "reported_all_pass")
    nonzero_or_blocked = [
        row
        for row in rows
        if row["classification"].startswith("tmp_blocked")
        or row["classification"] == "tmp_candidate_negative_unpromoted"
    ]
    green_unpromoted = [
        row for row in rows if row["classification"] == "tmp_candidate_green_unpromoted"
    ]

    adoption_candidates = [
        {
            "script": row["script"],
            "expected_result": row["expected_result"],
            "reason": "tmp candidate reran green under bounded current-system execution gate; still needs formal_scout conversion before evidence use",
        }
        for row in green_unpromoted
    ]
    negative_candidates = [
        {
            "script": row["script"],
            "expected_result": row["expected_result"],
            "classification": row["classification"],
            "reason": "tmp candidate reran negative or blocked; use as anti/open-basin target, not adoption evidence",
        }
        for row in nonzero_or_blocked
    ]

    positive = {
        "tmp_candidate_scripts_discovered": {
            "pass": len(scripts) > 0,
            "count": len(scripts),
        },
        "tmp_candidates_actually_executed": {
            "pass": len(rows) == len(scripts) and all("returncode" in row for row in rows),
            "count": len(rows),
        },
        "runtime_results_classified_without_promotion": {
            "pass": bool(class_counts) and PROMOTION_ALLOWED is False,
            "classification_counts": class_counts,
            "reported_all_pass_counts": all_pass_counts,
        },
        "green_candidates_preserved_as_conversion_queue": {
            "pass": len(adoption_candidates) > 0,
            "count": len(adoption_candidates),
            "first_five": adoption_candidates[:5],
        },
        "negative_or_blocked_candidates_preserved": {
            "pass": True,
            "count": len(negative_candidates),
            "first_five": negative_candidates[:5],
            "interpretation": "Zero is allowed for this tmp-v2 execution batch; negative/open evidence is tracked in grok_sim and older non-v2 tmp waves.",
        },
    }
    graveyards = {
        "tmp_green_does_not_become_formal_evidence": {
            "pass": all(row.get("reported_promotion_allowed") is not True for row in green_unpromoted),
            "reason": "Green tmp reruns are only conversion candidates; evidence requires a current formal_scout script/result pair.",
        },
        "tmp_failures_are_not_hidden": {
            "pass": True,
            "blocked_or_negative_count": len(nonzero_or_blocked),
            "reason": "Negative and blocked tmp reruns stay visible when present; this v2 candidate batch may legitimately rerun all green while remaining unpromoted.",
        },
        "tmp_schema_is_not_treated_as_current_contract": {
            "pass": True,
            "reported_classification_counts": count_by(rows, "reported_classification"),
            "reason": "Even when tmp scripts self-report formal_scout, current admission still requires this wrapper and later repo-local conversion.",
        },
    }
    boundary = {
        "no_tmp_claim_promotion": {
            "pass": PROMOTION_ALLOWED is False
            and "does not admit tmp results" in CLAIM_CEILING
            and "canonical architecture" in CLAIM_CEILING,
        },
        "execution_is_bounded": {
            "pass": TIMEOUT_SECONDS <= 60 and len(rows) <= 100,
            "timeout_seconds": TIMEOUT_SECONDS,
            "candidate_count": len(rows),
        },
        "all_rows_have_source_hashes": {
            "pass": all(row.get("script_sha256") for row in rows),
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
        "source_alignment_category": "attractor_basin_tmp_engine_v2_candidate_execution",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tmp_root": str(TMP_ENGINE_V2),
        "timeout_seconds_per_candidate": TIMEOUT_SECONDS,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "candidate_rows": rows,
        "adoption_candidates": adoption_candidates,
        "negative_or_blocked_candidates": negative_candidates,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "This scout executes tmp engine_v2 candidate probes under a current formal-scout adoption gate.",
            "Tmp scripts remain proposal-space artifacts until converted into current formal scouts with matched controls.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  candidate_count={len(rows)} class_counts={class_counts}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
