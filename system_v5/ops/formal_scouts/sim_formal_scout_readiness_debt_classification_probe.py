#!/usr/bin/env python3
"""Classify the formal-scout readiness debt without changing failed receipts."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "formal_scout_readiness_debt_classification_probe_results.json"
READINESS = REPO / "system_v5" / "evidence" / "formal_scout_readiness_index.json"
PLAN = REPO / "system_v5" / "ops" / "NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md"
HANDOFF = REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md"

NAME = "formal_scout_readiness_debt_classification_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "formal_scout_readiness_debt_classification"
CLAIM_CEILING = (
    "Administrative readiness-debt classifier only: classifies the current "
    "validator-red formal-scout rows and separates explicitly preserved red "
    "evidence from actionable readiness repair debt. It does not change "
    "failed scientific or blocked administrative receipts into passing "
    "receipts, does not authorize cleanup, and does not promote any engine, "
    "manifold, basin, tensor-network, or nonclassical claim."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive readiness-index parsing and result serialization",
    },
    "python_pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive repository path handling",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source and readiness hash receipts",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "python_pathlib": "supportive",
    "hashlib": "supportive",
}

ROW_CLASSES = {
    "system_v5/ops/formal_scouts/sim_chiral_trajectory_persistent_homology_readout_feature_probe.py": {
        "boundary_class": "intentional_negative_feature_underperforms_raw_baseline",
        "next_move": "Keep as red negative evidence unless a new feature design rerun is explicitly requested.",
        "reason": "Persistence features clear an above-chance threshold but underperform the raw-trajectory baseline and fail one cluster-tightness boundary.",
    },
    "system_v5/ops/formal_scouts/sim_grok_numpy_nonclassical_quarantine_audit_probe.py": {
        "boundary_class": "legacy_grok_numpy_quarantine_blocker",
        "next_move": "Keep as quarantine context or split legacy/Grok rows into native nonclassical versus classical/control receipts.",
        "reason": "The receipt intentionally exposes NumPy-load-bearing legacy/Grok rows as blocked from nonclassical promotion.",
    },
    "system_v5/ops/formal_scouts/sim_multiqubit_qit_reservoir_global_structure_probe.py": {
        "boundary_class": "torch_readout_reservoir_global_structure_counterevidence",
        "next_move": "Keep as red torch-native readout evidence unless a revised reservoir/readout design is explicitly requested.",
        "reason": "After replacing sklearn classifier plumbing with torch-native readout, the N=8 frozen reservoir row remains below the positive threshold and the structural-static baseline dominates the task.",
    },
    "system_v5/ops/formal_scouts/sim_multiqubit_qit_reservoir_grok_task_replication_probe.py": {
        "boundary_class": "torch_readout_grok_task_translation_counterevidence",
        "next_move": "Keep as red torch-native counterevidence for this translated task; do not cite the older sklearn-backed receipt as promotion evidence.",
        "reason": "The torch-native readout does not reproduce the translated Grok-task positive predicate at 8q, and local-spectrum leakage blocks the local-blind replication reading.",
    },
    "system_v5/ops/formal_scouts/sim_xgi_hypergraph_multi_layer_coupling_centrality_probe.py": {
        "boundary_class": "failed_xgi_coupling_diagnostic_scout",
        "next_move": "Keep as red XGI coupling-diagnostic scout or rerun with a revised XGI clustering/ablation design.",
        "reason": "The current XGI rerun has 4/5 positive predicates plus failed layer-removal and randomization graveyard controls; pairwise centrality divergence is diagnostic only.",
    },
    "system_v5/ops/formal_scouts/sim_engine_core_importer_boundary_classifier_probe.py": {
        "boundary_class": "intentional_engine_core_importer_boundary_sentinel",
        "next_move": "Keep as red boundary-sentinel evidence while direct EngineCore importers remain visible; consume the finite-boundary coverage audit for covered finite rows.",
        "reason": "The classifier intentionally remains validator-red after D70 because direct EngineCore importers are still present, but no dynamic candidate rows require boundary promotion.",
    },
    "system_v5/ops/formal_scouts/sim_engine_core_boundary_row_triage_probe.py": {
        "boundary_class": "intentional_engine_core_finite_boundary_triage_sentinel",
        "next_move": "Keep as red boundary-sentinel evidence while the current finite/readout rows remain quarantine-covered and gate-blocked.",
        "reason": "The triage receipt intentionally remains validator-red because finite-boundary coverage quarantines rows without clearing the raw gate or allowing promotion.",
    },
    "system_v5/ops/formal_scouts/sim_engine_core_finite_boundary_coverage_audit_probe.py": {
        "boundary_class": "intentional_engine_core_finite_boundary_coverage_sentinel",
        "next_move": "Keep as red coverage-sentinel evidence while stale finite receipts remain noncovering and current finite rows remain gate-blocked.",
        "reason": "The coverage audit intentionally remains validator-red after D75 because finite-boundary coverage is quarantine-only and stale noncovering receipts must not be treated as current gate clearance.",
    },
    "system_v5/ops/formal_scouts/sim_engine_core_dynamic_boundary_port_demote_classifier_probe.py": {
        "boundary_class": "intentional_engine_core_dynamic_boundary_empty_sentinel",
        "next_move": "Keep as red boundary-sentinel evidence that the dynamic EngineCore frontier is empty, not as a completion or promotion receipt.",
        "reason": "The dynamic classifier intentionally remains validator-red after D70 with dynamic row count zero because an empty dynamic frontier does not close the finite-boundary blocker class.",
    },
    "system_v5/ops/formal_scouts/sim_two_root_constraint_estate_tool_gate_blocker_partition_probe.py": {
        "boundary_class": "open_missing_n01_order_evidence_partition",
        "next_move": "Use the partition as the next B2 frontier: repair or reclassify the missing-N01/order-evidence rows before final synthesis.",
        "reason": "The partition receipt is intentionally red while it exposes the current selected blocker class rather than closing the estate.",
    },
    "system_v5/ops/formal_scouts/sim_two_root_constraint_classical_admin_load_bearing_partition_repair_probe.py": {
        "boundary_class": "blocked_b2_tool_role_partition_repair",
        "next_move": "Continue B2 repair from the current raw partition, or preserve B2 open in a blocked synthesis.",
        "reason": "The row-level receipt classifies all selected rows, but the raw partition still reports the selected blocker class.",
    },
    "system_v5/ops/formal_scouts/sim_two_root_constraint_final_synthesis_receipt.py": {
        "boundary_class": "historical_blocked_final_synthesis_receipt",
        "next_move": "Use the D86 final synthesis receipt for current closeout status; this readiness classifier does not own cleanup authorization or goal completion.",
        "reason": "Earlier runs of the final synthesis were intentionally blocked while B2/B3/B4/B5/B6 were unresolved. D86 supersedes that local readiness-history row for current tooling closeout.",
    },
    "system_v5/ops/formal_scouts/sim_formal_scout_readiness_debt_classification_probe.py": {
        "boundary_class": "self_referential_prior_b3_classifier_failure",
        "next_move": "Rerun this classifier after patching the self-classification path; it should disappear from readiness once green.",
        "reason": "A prior B3 classifier run failed because a newly red administrative receipt was not yet classified.",
    },
    "system_v5/ops/formal_scouts/sim_numpy_quarantine_source_native_nonclassical_gate_probe.py": {
        "boundary_class": "active_numpy_scipy_spectral_backend_quarantine_gate",
        "next_move": "Port or demote the current hard source and receipt quarantine rows reported by the NumPy/SciPy/spectral backend gate before treating the nonclassical/source-native backend surface as clean.",
        "reason": "The stricter gate intentionally fails closed when nonclassical/formal-scout support uses NumPy, load-bearing SciPy, or NumPy-backed NetworkX spectral calls.",
    },
}

ENGINE_CORE_FINITE_BOUNDARY_STALE_ROWS = [
    "system_v5/ops/formal_scouts/sim_engine_core_finite_boundary_axis0_fep_gradient_receipt_probe.py",
    "system_v5/ops/formal_scouts/sim_engine_core_finite_boundary_constraint_manifold_delta_neural_readout_receipt_probe.py",
    "system_v5/ops/formal_scouts/sim_engine_core_finite_boundary_source_native_active_inference_strategy_policy_receipt_probe.py",
    "system_v5/ops/formal_scouts/sim_engine_core_finite_boundary_source_native_fep_pomdp_policy_tree_receipt_probe.py",
    "system_v5/ops/formal_scouts/sim_engine_core_finite_boundary_source_native_holodeck_hash_memory_placeholder_receipt_probe.py",
    "system_v5/ops/formal_scouts/sim_engine_core_finite_boundary_source_native_hopf_fep_igt_chirality_prediction_receipt_probe.py",
    "system_v5/ops/formal_scouts/sim_engine_core_finite_boundary_source_native_multicarrier_subdense_environment_contraction_receipt_probe.py",
    "system_v5/ops/formal_scouts/sim_engine_core_finite_boundary_source_native_peps3d_32_64_site_capacity_receipt_probe.py",
    "system_v5/ops/formal_scouts/sim_engine_core_finite_boundary_source_native_peps3d_48_site_regime_crossing_receipt_probe.py",
    "system_v5/ops/formal_scouts/sim_engine_core_finite_boundary_source_native_peps3d_52_56_60_site_regime_ladder_receipt_probe.py",
]
for source_path in ENGINE_CORE_FINITE_BOUNDARY_STALE_ROWS:
    ROW_CLASSES[source_path] = {
        "boundary_class": "stale_engine_core_finite_boundary_quarantine_receipt",
        "next_move": "Keep as red nonclearance evidence unless a new current-gate finite-boundary receipt is explicitly requested.",
        "reason": "The live tool-role gate now classifies the target as tool_role_candidate, so this finite-boundary quarantine receipt no longer covers a current EngineCore importer-boundary row.",
    }

PRESERVED_RED_BOUNDARY_CLASSES = {
    "failed_xgi_coupling_diagnostic_scout",
    "intentional_engine_core_dynamic_boundary_empty_sentinel",
    "intentional_engine_core_finite_boundary_coverage_sentinel",
    "intentional_engine_core_finite_boundary_triage_sentinel",
    "intentional_engine_core_importer_boundary_sentinel",
    "intentional_negative_feature_underperforms_raw_baseline",
    "legacy_grok_numpy_quarantine_blocker",
    "stale_engine_core_finite_boundary_quarantine_receipt",
    "torch_readout_grok_task_translation_counterevidence",
    "torch_readout_reservoir_global_structure_counterevidence",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def source_hashes() -> dict[str, Any]:
    paths = {
        "readiness_index": READINESS,
        "active_plan": PLAN,
        "active_handoff": HANDOFF,
    }
    return {
        name: {"path": rel(path), "exists": path.exists(), "sha256": sha256(path)}
        for name, path in paths.items()
    }


def counts_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row[key]] = counts.get(row[key], 0) + 1
    return dict(sorted(counts.items()))


def classify_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    classified = []
    unknown = []
    for row in rows:
        source_path = str(row.get("source_path") or "")
        spec = ROW_CLASSES.get(source_path)
        if spec is None:
            unknown.append(row)
            spec = {
                "boundary_class": "unknown_readiness_validator_failure",
                "next_move": "Add explicit readiness classification before closeout.",
                "reason": "No B3 readiness classifier exists for this validator-red row.",
            }
        classified.append({**row, **spec})
    return classified, unknown


def main() -> int:
    start = time.time()
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    readiness = read_json(READINESS)
    summary = readiness.get("summary", {})
    failed_rows = readiness.get("validator_failed_rows", [])
    if not isinstance(failed_rows, list):
        failed_rows = []
    classified, unknown = classify_rows(failed_rows)
    class_counts = counts_by(classified, "boundary_class")
    validator_fail_count = int(summary.get("validator_fail_count") or 0)
    actionable_rows = [
        row
        for row in classified
        if row["boundary_class"] not in PRESERVED_RED_BOUNDARY_CLASSES
    ]
    preserved_rows = [
        row
        for row in classified
        if row["boundary_class"] in PRESERVED_RED_BOUNDARY_CLASSES
    ]
    readme_coverage_pass = (
        summary.get("readme_missing_count") == 0
        and summary.get("readme_status_mismatch_count") == 0
    )
    validator_red_rows_classified = (
        len(unknown) == 0
        and len(classified) == validator_fail_count
        and readme_coverage_pass
        and len(actionable_rows) == 0
    )

    positive = {
        "readiness_index_loaded": {
            "pass": READINESS.exists(),
            "readiness_path": rel(READINESS),
        },
        "validator_failed_rows_classified": {
            "pass": len(unknown) == 0 and len(classified) == validator_fail_count,
            "classified_count": len(classified),
            "expected_count": validator_fail_count,
            "unknown_count": len(unknown),
            "class_counts": class_counts,
        },
        "readme_coverage_already_repaired": {
            "pass": readme_coverage_pass,
            "readme_missing_count": summary.get("readme_missing_count"),
            "readme_status_mismatch_count": summary.get("readme_status_mismatch_count"),
        },
        "validator_red_rows_are_preserved_or_actionable": {
            "pass": len(unknown) == 0,
            "preserved_red_count": len(preserved_rows),
            "actionable_readiness_debt_count": len(actionable_rows),
            "preserved_boundary_classes": sorted(PRESERVED_RED_BOUNDARY_CLASSES),
        },
    }
    boundary = {
        "validator_red_rows_classified": {
            "pass": True,
            "value": validator_red_rows_classified,
            "reason": (
                "All current validator-red rows are classified as preserved red evidence with no actionable readiness repair rows."
                if validator_red_rows_classified
                else "Some validator-red rows remain unknown, uncovered by README status, or actionable repair debt."
            ),
        },
        "promotion_allowed": {"pass": True, "value": PROMOTION_ALLOWED},
        "cleanup_authorized": {
            "pass": True,
            "value": False,
            "reason": "Readiness preservation is not cleanup authorization.",
        },
    }
    graveyard_companions = {
        "paint_failed_receipts_green_control_killed": {
            "pass": True,
            "reason": "The validator-red receipts remain red; this file only classifies them.",
        },
        "readme_coverage_as_readiness_completion_control_killed": {
            "pass": validator_fail_count >= 1,
            "validator_fail_count": validator_fail_count,
            "reason": "README coverage can be green while validator-red rows still block completion.",
        },
    }
    all_pass = (
        all(item.get("pass") is True for item in positive.values())
        and all(item.get("pass") is True for item in boundary.values())
        and all(item.get("pass") is True for item in graveyard_companions.values())
    )
    output = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "generated_at": generated_at,
        "runtime_seconds": round(time.time() - start, 6),
        "all_pass": all_pass,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "B3 formal-scout readiness validator-failure boundary classification",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "summary": {
            "all_pass": all_pass,
            "completion_status": (
                "b3_validator_red_rows_classified_no_actionable_rows"
                if all_pass and validator_red_rows_classified
                else "b3_validator_red_rows_classified_unresolved"
                if all_pass
                else "b3_readiness_classification_failed"
            ),
            "validator_fail_count": summary.get("validator_fail_count"),
            "readme_missing_count": summary.get("readme_missing_count"),
            "readme_status_mismatch_count": summary.get("readme_status_mismatch_count"),
            "classified_count": len(classified),
            "unknown_count": len(unknown),
            "preserved_red_count": len(preserved_rows),
            "actionable_readiness_debt_count": len(actionable_rows),
            "validator_red_rows_classified": validator_red_rows_classified,
            "freshness_debt_cleared": False,
            "cleanup_authorized": False,
            "goal_complete": False,
            "class_counts": class_counts,
        },
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": {
            "total": 2,
            "passed": 2,
            "paint_failed_receipts_green": {
                "pass": True,
                "status": "rejected",
                "reason": "Would erase real negative/blocker evidence.",
            },
            "delete_failed_receipts": {
                "pass": True,
                "status": "rejected",
                "reason": "Would hide failed evidence instead of closing or preserving it.",
            },
        },
        "classified_rows": classified,
        "unknown_rows": unknown,
        "preserved_red_rows": preserved_rows,
        "actionable_readiness_debt_rows": actionable_rows,
        "open_choices": [
            "Keep the current red receipts as intentional negative/quarantine/counterevidence without promotion.",
            "Rerun one or more red scouts with a revised design and let validator status change only through new evidence.",
            "Split legacy/Grok quarantine rows into native nonclassical versus classical/control receipts if needed.",
        ],
        "blockers": [],
        "open_blockers": (
            [
                "B3 readiness validator-red rows include actionable or unknown rows after classification.",
                "This receipt is not cleanup authorization and not scientific promotion evidence.",
            ]
            if not validator_red_rows_classified
            else [
                "This receipt is not cleanup authorization and not scientific promotion evidence.",
                "This receipt does not clear dirty-source or fresh-rerun freshness debt.",
            ]
        ),
        "why_not_v4_probes": "B3 closeout boundary receipt only; does not run science sims or promote manifold claims.",
    }
    OUT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "validator_fail_count": summary.get("validator_fail_count"),
                "classified_count": len(classified),
                "unknown_count": len(unknown),
                "out_path": rel(OUT_PATH),
                "preserved_red_count": len(preserved_rows),
                "actionable_readiness_debt_count": len(actionable_rows),
                "validator_red_rows_classified": validator_red_rows_classified,
                "freshness_debt_cleared": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
