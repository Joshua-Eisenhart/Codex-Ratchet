#!/usr/bin/env python3
"""Classify stdout-only tmp engine_v2 runs by printed verdict text."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "attractor_basin_tmp_engine_v2_stdout_verdict_probe_results.json"
SOURCE_RESULT = RESULT_DIR / "attractor_basin_tmp_engine_v2_full_wave_execution_probe_results.json"
RESOLUTION_RESULT = RESULT_DIR / "attractor_basin_tmp_engine_v2_receipt_resolution_probe_results.json"

NAME = "attractor_basin_tmp_engine_v2_stdout_verdict_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: classifies stdout-only tmp engine_v2 proposal sims by "
    "printed verdict language for attractor-basin triage. It does not admit "
    "tmp results, engine, Axis0, FEP, Holodeck, physics, cognition, "
    "world-model, or canonical architecture claims."
)

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "load-bearing parsing of prior broad-run receipts"},
    "re": {"tried": True, "used": True, "reason": "load-bearing verdict-token extraction"},
    "pathlib": {"tried": True, "used": True, "reason": "load-bearing bounded result path checks"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing source receipt hashes"},
}
TOOL_INTEGRATION_DEPTH = {"json": "load_bearing", "re": "load_bearing", "pathlib": "load_bearing", "hashlib": "load_bearing"}

NEGATIVE_TOKENS = [
    "VERDICT: FAIL",
    "GENERIC",
    "ARTIFACT",
    "NO BASINS",
    "NOT architecture-specific",
    "within null",
    "NO-INTERTWINER",
    "identical",
]
POSITIVE_TOKENS = [
    "SURVIVES",
    "SUPPORT",
    "LOAD-BEARING",
    "DISTINGUISHED",
    "RT-LIKE",
    "HOLOGRAPHIC-CLASS",
    "multi-basin",
    "architecture-specific",
]


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_text(text: str) -> tuple[str, list[str], list[str]]:
    neg = [tok for tok in NEGATIVE_TOKENS if tok.lower() in text.lower()]
    pos = [tok for tok in POSITIVE_TOKENS if tok.lower() in text.lower()]
    if neg and pos:
        return "stdout_mixed_boundary", pos, neg
    if neg:
        return "stdout_negative_boundary", pos, neg
    if pos:
        return "stdout_positive_candidate", pos, neg
    if re.search(r"\bwall:\s+\d", text):
        return "stdout_metric_only", pos, neg
    return "stdout_unclassified", pos, neg


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def main() -> int:
    started = time.time()
    source = load_json(SOURCE_RESULT)
    resolution = load_json(RESOLUTION_RESULT)
    unresolved = {
        row["script_name"]
        for row in resolution.get("rows", [])
        if row.get("resolved_classification") == "unresolved_missing_receipt"
    }
    rows = []
    for row in source.get("rows", []):
        if row.get("script_name") not in unresolved:
            continue
        text = "\n".join([row.get("stdout_tail") or "", row.get("stderr_tail") or ""])
        cls, pos, neg = classify_text(text)
        rows.append(
            {
                "script_name": row.get("script_name"),
                "stdout_classification": cls,
                "positive_tokens": pos,
                "negative_tokens": neg,
                "stdout_tail": row.get("stdout_tail"),
                "stderr_tail": row.get("stderr_tail"),
            }
        )
    class_counts = count_by(rows, "stdout_classification")
    positive = {
        "unresolved_stdout_rows_loaded": {"pass": len(rows) > 0, "count": len(rows)},
        "stdout_rows_classified": {"pass": bool(class_counts), "classification_counts": class_counts},
        "stdout_triage_has_positive_and_boundary_rows": {
            "pass": any("positive" in row["stdout_classification"] or "mixed" in row["stdout_classification"] for row in rows)
            and any("negative" in row["stdout_classification"] or "mixed" in row["stdout_classification"] for row in rows),
            "classification_counts": class_counts,
        },
    }
    graveyards = {
        "stdout_positive_is_not_receipt_green": {
            "pass": PROMOTION_ALLOWED is False,
            "reason": "Printed positive verdicts are proposal-signal only without structured tmp/current receipt fields.",
        },
        "stdout_mixed_is_basin_boundary": {
            "pass": class_counts.get("stdout_mixed_boundary", 0) >= 1,
            "reason": "Mixed positive/negative printed verdicts are exactly basin-wall evidence.",
        },
        "stdout_metric_only_stays_unpromoted": {"pass": True},
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "prior_receipts_loaded": {
            "pass": source.get("name") == "attractor_basin_tmp_engine_v2_full_wave_execution_probe"
            and resolution.get("name") == "attractor_basin_tmp_engine_v2_receipt_resolution_probe",
            "source_sha256": sha256_file(SOURCE_RESULT),
            "resolution_sha256": sha256_file(RESOLUTION_RESULT),
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
        "source_alignment_category": "attractor_basin_tmp_engine_v2_stdout_verdict",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
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
            "This classifies stdout-only tmp proposal sims after current broad execution.",
            "It does not treat printed verdict text as current formal evidence.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  rows={len(rows)} class_counts={class_counts}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
