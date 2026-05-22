#!/usr/bin/env python3
"""Aggregate tmp engine_v2 execution/refinement passes into one basin map."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "attractor_basin_tmp_engine_v2_execution_aggregate_probe_results.json"

NAME = "attractor_basin_tmp_engine_v2_execution_aggregate_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: aggregates tmp engine_v2 execution/refinement receipts "
    "into one attractor-basin triage map. It does not admit tmp results, "
    "engine, Axis0, FEP, Holodeck, physics, cognition, world-model, or "
    "canonical architecture claims."
)

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "load-bearing parsing of execution/refinement receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "load-bearing bounded receipt checks"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing source hash receipts"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive", "hashlib": "supportive"}

INPUTS = {
    "full_wave": RESULT_DIR / "attractor_basin_tmp_engine_v2_full_wave_execution_probe_results.json",
    "timeout_rerun": RESULT_DIR / "attractor_basin_tmp_engine_v2_timeout_rerun_probe_results.json",
    "receipt_resolution": RESULT_DIR / "attractor_basin_tmp_engine_v2_receipt_resolution_probe_results.json",
    "stdout_verdict": RESULT_DIR / "attractor_basin_tmp_engine_v2_stdout_verdict_probe_results.json",
}


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def main() -> int:
    started = time.time()
    inputs = {name: load_json(path) for name, path in INPUTS.items()}
    input_receipts = {
        name: {"path": str(path), "sha256": sha256_file(path), "all_pass": inputs[name].get("all_pass")}
        for name, path in INPUTS.items()
    }

    full_rows = inputs["full_wave"].get("rows", [])
    timeout_rows = {row["script_name"]: row for row in inputs["timeout_rerun"].get("rows", [])}
    resolution_rows = {row["script_name"]: row for row in inputs["receipt_resolution"].get("rows", [])}
    stdout_rows = {row["script_name"]: row for row in inputs["stdout_verdict"].get("rows", [])}

    aggregate_rows: list[dict[str, Any]] = []
    for row in full_rows:
        name = row["script_name"]
        final = row["classification"]
        evidence = {"first_pass": final}
        if name in timeout_rows:
            final = timeout_rows[name]["classification"]
            evidence["timeout_rerun"] = final
        if name in resolution_rows:
            final = resolution_rows[name]["resolved_classification"]
            evidence["receipt_resolution"] = final
        if name in stdout_rows:
            final = stdout_rows[name]["stdout_classification"]
            evidence["stdout_verdict"] = final
        if final in {"green", "green_after_long_timeout", "resolved_green"}:
            basin_label = "tmp_green_conversion_candidate"
        elif final in {"negative", "resolved_negative", "negative_after_long_timeout", "stdout_negative_boundary"}:
            basin_label = "tmp_negative_boundary"
        elif final in {"stdout_positive_candidate"}:
            basin_label = "tmp_stdout_positive_candidate"
        elif final in {"stdout_mixed_boundary"}:
            basin_label = "tmp_mixed_boundary"
        elif "timeout" in final or "nonzero" in final or "missing" in final or "unresolved" in final:
            basin_label = "tmp_open_boundary"
        else:
            basin_label = "tmp_schema_or_metric_review"
        aggregate_rows.append(
            {
                "script_name": name,
                "first_pass": row["classification"],
                "final_classification": final,
                "basin_label": basin_label,
                "evidence_path": evidence,
            }
        )

    final_counts = count_by(aggregate_rows, "final_classification")
    basin_counts = count_by(aggregate_rows, "basin_label")
    positive = {
        "all_input_receipts_loaded": {
            "pass": all(receipt["all_pass"] is True for receipt in input_receipts.values()),
            "input_receipts": input_receipts,
        },
        "all_broad_rows_aggregated": {"pass": len(aggregate_rows) == len(full_rows) and len(aggregate_rows) >= 100, "count": len(aggregate_rows)},
        "basin_map_has_green_and_boundaries": {
            "pass": basin_counts.get("tmp_green_conversion_candidate", 0) > 0
            and basin_counts.get("tmp_open_boundary", 0) > 0
            and basin_counts.get("tmp_negative_boundary", 0) > 0,
            "basin_counts": basin_counts,
            "final_counts": final_counts,
        },
    }
    graveyards = {
        "aggregate_does_not_promote_tmp": {"pass": PROMOTION_ALLOWED is False},
        "open_boundaries_stay_visible": {"pass": basin_counts.get("tmp_open_boundary", 0) > 0},
        "stdout_positive_not_equated_with_json_green": {"pass": basin_counts.get("tmp_stdout_positive_candidate", 0) > 0},
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "all_rows_have_labels": {"pass": all(row.get("basin_label") for row in aggregate_rows)},
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
        "source_alignment_category": "attractor_basin_tmp_engine_v2_execution_aggregate",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "input_receipts": input_receipts,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "basin_counts": basin_counts,
        "final_counts": final_counts,
        "rows": aggregate_rows,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "This aggregates current formal-scout gates over tmp engine_v2 proposal sims.",
            "It maps proposal-space trajectories into basin labels without canon promotion.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  basin_counts={basin_counts}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
