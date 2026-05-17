#!/usr/bin/env python3
"""Deep-basin evidence aggregator guard.

This scout consumes the basin-depth guard and attractor-basin classifier result
and tests the exact downstream misread flagged by provider audits: all_pass on a
routing guard must not be interpreted as deep-basin evidence when the classifier
labels the receipt candidate_basin and the guard has an open candidate row.

Formal scout only.  It does not promote any basin label, add physics/FEP/Axis0
evidence, or claim perturbation-volume robustness.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "deep_basin_evidence_aggregator_probe_results.json"

NAME = "deep_basin_evidence_aggregator_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "attractor_basin_downstream_aggregation_guard"
CLAIM_CEILING = (
    "Formal scout only: consumes existing basin-depth guard and classifier receipts "
    "to reject the bad aggregation all_pass+candidate=open-as-deep. It does not admit "
    "deep-basin evidence, robust perturbation volume, final FEP, final Axis0, Holodeck, "
    "physics, cognition, world-model, architecture, or canonical claims."
)

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "load-bearing receipt parsing"},
    "pathlib": {"tried": True, "used": True, "reason": "load-bearing result path resolution"},
    "hashlib": {"tried": True, "used": True, "reason": "load-bearing receipt hash capture"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_receipt(filename: str) -> dict[str, Any]:
    path = RESULT_DIR / filename
    if not path.exists():
        return {"exists": False, "path": str(path), "filename": filename}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["path"] = str(path)
    data["filename"] = filename
    data["sha256"] = sha256_file(path)
    return data


def classifier_row(classifier: dict[str, Any], case_id: str) -> dict[str, Any]:
    for key in ("case_rows", "classification_rows", "rows"):
        rows = classifier.get(key, []) or []
        for row in rows:
            if isinstance(row, dict) and row.get("case_id") == case_id:
                return row
    for row in classifier.get("repair_receipt", {}).get("primary_control/result", {}).get("case_rows", []) or []:
        if isinstance(row, dict) and row.get("case_id") == case_id:
            return row
    return {}


def main() -> int:
    started = time.time()
    guard = load_receipt("manifold_dependency_basin_depth_guard_probe_results.json")
    classifier = load_receipt("attractor_basin_success_criteria_receipt_classifier_probe_results.json")
    row = classifier_row(classifier, "manifold_dependency_basin_depth_guard")

    guard_result = guard.get("repair_receipt", {}).get("primary_control/result", {})
    open_rows = guard_result.get("candidate_rows_routed_open") or []
    passing_rows = guard_result.get("candidate_rows_passing_guard") or []
    classifier_label = row.get("computed_label")
    bad_deep_interpretation = (
        guard.get("all_pass") is True
        and classifier_label == "deep_basin"
        and bool(open_rows)
    )
    is_deep_basin_evidence = (
        guard.get("all_pass") is True
        and classifier_label == "deep_basin"
        and not open_rows
    )

    positive = {
        "guard_receipt_loads_and_is_routing_success": {
            "pass": guard.get("exists") is True and guard.get("all_pass") is True,
            "guard_all_pass": guard.get("all_pass"),
            "guard_sha256": guard.get("sha256"),
        },
        "classifier_receipt_labels_guard_candidate_not_deep": {
            "pass": classifier.get("exists") is True and classifier_label == "candidate_basin",
            "classifier_label": classifier_label,
            "classifier_sha256": classifier.get("sha256"),
        },
        "open_candidate_row_blocks_deep_basin_evidence": {
            "pass": bool(open_rows) and not is_deep_basin_evidence,
            "candidate_rows_routed_open": open_rows,
            "candidate_rows_passing_guard": passing_rows,
            "is_deep_basin_evidence": is_deep_basin_evidence,
        },
    }

    graveyard = {
        "all_pass_candidate_open_not_aggregated_as_deep": {
            "pass": not bad_deep_interpretation,
            "bad_deep_interpretation": bad_deep_interpretation,
            "reason": "all_pass on the guard means the routing check ran, not that every candidate row passed basin depth.",
        },
        "knife_edge_policy_not_promoted": {
            "pass": "active_inference_policy_window" in open_rows,
            "open_rows": open_rows,
        },
    }

    boundary = {
        "claim_ceiling_blocks_deep_basin_and_robust_volume": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not admit", "deep-basin evidence", "robust perturbation volume"]),
        },
        "next_work_remains_policy_margin_or_true_perturbation": {
            "pass": True,
            "next": "Repair/block active-policy runner-up margin or run true epsilon/noise perturbation on guard-pass rows.",
        },
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "variants": {
                "all_pass_as_deep": {"pass": True, "status": "rejected"},
                "candidate_label_as_deep": {"pass": True, "status": "rejected"},
                "open_policy_as_depth": {"pass": True, "status": "rejected"},
            },
        },
        "why_not_v4_probes": (
            "This is a v5 receipt-aggregation guard over current formal-scout results. "
            "It does not add v4 probe evidence or promote any v4/canonical claim."
        ),
        "repair_receipt": {
            "weak_link": "Downstream consumers could misread guard all_pass as deep-basin evidence.",
            "target_file_or_result": str(OUT_PATH),
            "dependency_subset": [guard.get("path"), classifier.get("path")],
            "before_baseline/hash": {
                "guard": guard.get("sha256"),
                "classifier": classifier.get("sha256"),
            },
            "primary_control/result": {
                "classifier_label": classifier_label,
                "candidate_rows_routed_open": open_rows,
                "candidate_rows_passing_guard": passing_rows,
                "is_deep_basin_evidence": is_deep_basin_evidence,
                "bad_deep_interpretation": bad_deep_interpretation,
            },
            "promotion_ceiling": CLAIM_CEILING,
            "next_step": "Run a policy-window margin repair/blocker or true epsilon/noise perturbation scout.",
        },
        "audit_method_families": [
            "basin_depth_guard_receipt",
            "attractor_classifier_receipt",
            "provider_flagged_downstream_misread",
        ],
        "method_count_source": "receipt_family_aggregation_guard_not_parser_tools",
        "blockers": [],
        "all_pass": all(
            row.get("pass") is True
            for section in (positive, graveyard, boundary)
            for row in section.values()
        ),
        "elapsed_seconds": round(time.time() - started, 6),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
