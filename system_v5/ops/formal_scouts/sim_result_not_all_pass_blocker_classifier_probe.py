#!/usr/bin/env python3
"""Classify tool-gate rows blocked only because their result did not pass."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from collections import Counter
from typing import Any

import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
OUT_PATH = RESULT_DIR / "result_not_all_pass_blocker_classifier_probe_results.json"
TOOL_GATE = RESULT_DIR / "constraint_admissible_tool_role_gate_probe_results.json"
READINESS = REPO / "system_v5" / "evidence" / "formal_scout_readiness_index.json"

NAME = "result_not_all_pass_blocker_classifier_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "result_not_all_pass_blocker_classifier"
CLAIM_CEILING = (
    "Formal scout audit only: classifies current tool-gate rows whose receipts "
    "remain blocked because all_pass is false. It does not convert failed "
    "scientific or tool-lego receipts into passing receipts, authorize cleanup, "
    "repair EngineCore, tune thresholds, rerun science, and does not admit "
    "engine, manifold, Axis0, QIT-reservoir, physics, Holodeck, consciousness, "
    "or canonical claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive parsing of current tool-gate, readiness, and result receipts",
    },
    "python_pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical path binding",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt identity hashes",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that completion/promotion is inconsistent while result-failed rows remain unresolved",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "python_pathlib": "supportive",
    "hashlib": "supportive",
    "z3": "load_bearing",
}

EXPECTED_ROWS = {
    "clifford_sympy_geomstats_nested_g_structure_live_state_probe": {
        "boundary_class": "enginecore_carrier_blocker_plus_harness_accounting_repair",
        "repairable_schema_mistake": False,
        "repair_lane_required": True,
        "honest_negative": False,
        "next_honest_action": (
            "Do not promote. First repair the EngineCore no-NumPy carrier boundary enough "
            "to collect at least one live state, then fix the pure_ket0 chirality-control "
            "accounting before rerunning this single scout."
        ),
        "delusional_promotion": (
            "live EngineCore tensor states validate the nested GL(2,C)->U(2)->SU(2)->"
            "Spin(3)->Weyl chain under sympy/clifford/geomstats"
        ),
    },
    "multiqubit_qit_reservoir_global_structure_probe": {
        "boundary_class": "torch_readout_reservoir_global_structure_counterevidence",
        "repairable_schema_mistake": False,
        "repair_lane_required": False,
        "honest_negative": True,
        "next_honest_action": (
            "Keep as red torch-native readout counterevidence unless a revised reservoir "
            "or readout design is explicitly requested."
        ),
        "delusional_promotion": (
            "the frozen multi-qubit QIT reservoir passed the 8q maturity/global-structure "
            "separation gate"
        ),
    },
    "multiqubit_qit_reservoir_grok_task_replication_probe": {
        "boundary_class": "torch_readout_grok_task_translation_counterevidence",
        "repairable_schema_mistake": False,
        "repair_lane_required": False,
        "honest_negative": True,
        "next_honest_action": (
            "Keep as red torch-native counterevidence for the translated Grok task; do not "
            "cite older sklearn-backed receipts as promotion evidence."
        ),
        "delusional_promotion": (
            "the v6 frozen reservoir replicates the product/GHZ/W/Haar Grok task at 8q "
            "or beats local explanations"
        ),
    },
    "singular_lego_wired_axis0_plural_manifold_engine_probe": {
        "boundary_class": "axis0_path_entropy_hard_gate_failure",
        "repairable_schema_mistake": False,
        "repair_lane_required": True,
        "honest_negative": True,
        "next_honest_action": (
            "Do not promote or schema-patch green. Run a narrow v2 falsifier for path-entropy "
            "degeneracy under de-cyclicized/schedule-confound controls, then true per-lego "
            "remove-and-rerun ablations if warranted."
        ),
        "delusional_promotion": (
            "final Axis0, canonical singular engine, canonical manifold tower, or lego "
            "load-bearingness in the per-substage Axis0 path"
        ),
    },
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def readiness_by_result_path(readiness: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = readiness.get("rows", [])
    if not isinstance(rows, list):
        return {}
    return {str(row.get("result_path")): row for row in rows if isinstance(row, dict)}


def failed_tool_gate_rows(tool_gate: dict[str, Any]) -> list[dict[str, Any]]:
    rows = tool_gate.get("tool_role_rows", [])
    if not isinstance(rows, list):
        return []
    return [
        row
        for row in rows
        if isinstance(row, dict) and row.get("tool_role_status") == "blocked_result_not_all_pass"
    ]


def row_result_path(row: dict[str, Any]) -> pathlib.Path:
    result_path = pathlib.Path(str(row.get("result_path") or ""))
    return SCOUT_ROOT / result_path if not result_path.is_absolute() else result_path


def metric_evidence(name: str, result: dict[str, Any]) -> dict[str, Any]:
    positive = result.get("positive", {}) if isinstance(result.get("positive"), dict) else {}
    if name == "clifford_sympy_geomstats_nested_g_structure_live_state_probe":
        negative = result.get("negative", {}) if isinstance(result.get("negative"), dict) else {}
        pure_ket0 = negative.get("pure_ket0_chirality_split", {})
        state_errors = positive.get("state_errors", [])
        return {
            "failure_mode": "zero_live_states_and_numpy_carrier_boundary",
            "total_live_states": positive.get("total_live_states"),
            "state_error_count": len(state_errors) if isinstance(state_errors, list) else None,
            "enginecore_error_sample": state_errors[0].get("error") if isinstance(state_errors, list) and state_errors else None,
            "pure_ket0_l4_admitted": pure_ket0.get("L4_admitted") if isinstance(pure_ket0, dict) else None,
            "pure_ket0_excluded_under_C": pure_ket0.get("excluded_under_C") if isinstance(pure_ket0, dict) else None,
            "pure_ket0_missing_from_graveyard_summary": "pure_ket0_chirality_split"
            not in (result.get("graveyard_companions", {}) or {}),
        }
    if name == "multiqubit_qit_reservoir_global_structure_probe":
        check = positive.get("frozen_multiqubit_reservoir_separates_global_structure_at_8q", {})
        rows = check.get("rows", []) if isinstance(check, dict) else []
        eight = next((row for row in rows if row.get("n_qubits") == 8), {}) if isinstance(rows, list) else {}
        metrics = eight.get("metrics", {}) if isinstance(eight, dict) else {}
        return {
            "failure_mode": "8q_frozen_reservoir_below_positive_threshold",
            "n_qubits": eight.get("n_qubits"),
            "frozen_reservoir_accuracy": metrics.get("frozen_reservoir_accuracy"),
            "local_only_accuracy": metrics.get("local_only_accuracy"),
            "shuffled_label_accuracy": metrics.get("frozen_reservoir_shuffled_label_accuracy"),
            "row_pass": eight.get("pass"),
            "z3_guard_pass": positive.get("z3_rejects_local_or_shuffle_only_explanation_at_8q", {}).get("pass"),
        }
    if name == "multiqubit_qit_reservoir_grok_task_replication_probe":
        check = positive.get("grok_task_frozen_reservoir_beats_local_bloch_at_8q", {})
        rows = check.get("rows", []) if isinstance(check, dict) else []
        eight = next((row for row in rows if row.get("n_qubits") == 8), {}) if isinstance(rows, list) else {}
        metrics = eight.get("metrics", {}) if isinstance(eight, dict) else {}
        z3_check = positive.get("z3_rejects_grok_task_local_or_shuffle_explanation", {})
        return {
            "failure_mode": "8q_grok_task_reservoir_equals_local_bloch_and_z3_guard_fails",
            "n_qubits": eight.get("n_qubits"),
            "frozen_reservoir_accuracy": metrics.get("frozen_reservoir_accuracy"),
            "local_bloch_accuracy": metrics.get("local_bloch_accuracy"),
            "local_spectrum_accuracy": metrics.get("local_spectrum_accuracy"),
            "shuffled_label_accuracy": metrics.get("frozen_reservoir_shuffled_label_accuracy"),
            "row_pass": eight.get("pass"),
            "z3_guard_pass": z3_check.get("pass") if isinstance(z3_check, dict) else None,
            "z3_solver_status": z3_check.get("solver_status") if isinstance(z3_check, dict) else None,
        }
    if name == "singular_lego_wired_axis0_plural_manifold_engine_probe":
        gate = positive.get("axis0_seven_acceptance_fields_hold_INCLUDING_path_entropy_hard_gate", {})
        details = gate.get("details", {}) if isinstance(gate, dict) else {}
        path_entropy = (result.get("graveyard_companions", {}) or {}).get(
            "path_entropy_degeneracy_HARD_GATE_status", {}
        )
        lego = positive.get("eleven_invokable_nonclassical_legos_actually_callable_via_primary_callable", {})
        return {
            "failure_mode": "axis0_path_entropy_degeneracy_hard_gate_failed",
            "path_entropy_hard_gate": details.get("P4_path_entropy_not_degenerate_HARD_GATE"),
            "diagnostic_path_entropy_degenerate": details.get("diagnostic_path_entropy_degenerate"),
            "zero_derivatives": path_entropy.get("n_zero_deriv") if isinstance(path_entropy, dict) else None,
            "total_derivatives": path_entropy.get("n_total_deriv") if isinstance(path_entropy, dict) else None,
            "lego_callable_invoked_count": lego.get("callable_invoked_count") if isinstance(lego, dict) else None,
            "lego_deferred_count": lego.get("deferred_count") if isinstance(lego, dict) else None,
            "blockers": result.get("blockers", []),
        }
    return {"failure_mode": "unknown_result_failure"}


def classify_row(row: dict[str, Any], readiness_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    name = str(row.get("name") or "")
    spec = EXPECTED_ROWS.get(name)
    result_path = row_result_path(row)
    result = read_json(result_path)
    readiness = readiness_rows.get(rel(result_path), {})
    return {
        "name": name,
        "source_path": row.get("source_path"),
        "result_path": rel(result_path),
        "result_sha256": sha256(result_path),
        "tool_role_status": row.get("tool_role_status"),
        "tool_gate_result_all_pass": row.get("result_all_pass"),
        "result_all_pass": result.get("all_pass"),
        "result_classification": result.get("classification"),
        "readiness_status": readiness.get("readiness_status"),
        "readiness_validation_errors": readiness.get("validation_errors", []),
        "load_bearing_tools": row.get("load_bearing_tools", []),
        "boundary_class": spec.get("boundary_class") if spec else "unknown_result_not_all_pass_row",
        "repairable_schema_mistake": spec.get("repairable_schema_mistake") if spec else None,
        "repair_lane_required": spec.get("repair_lane_required") if spec else True,
        "honest_negative": spec.get("honest_negative") if spec else None,
        "delusional_promotion": spec.get("delusional_promotion") if spec else "unclassified failed receipt",
        "next_honest_action": spec.get("next_honest_action") if spec else "Add explicit result-failure classification.",
        "metric_evidence": metric_evidence(name, result),
    }


def z3_completion_block(row_count: int) -> dict[str, Any]:
    result_failed_rows_remain = z3.Bool("result_failed_rows_remain")
    completion_allowed = z3.Bool("completion_allowed")
    promotion_allowed = z3.Bool("promotion_allowed")
    solver = z3.Solver()
    solver.add(result_failed_rows_remain == (row_count > 0))
    solver.add(z3.Implies(result_failed_rows_remain, z3.And(z3.Not(completion_allowed), z3.Not(promotion_allowed))))
    solver.add(z3.Or(completion_allowed, promotion_allowed))
    status = solver.check()
    if row_count == 0:
        return {
            "pass": status == z3.sat,
            "solver_status": str(status),
            "result_failed_row_count": row_count,
            "meaning": "No result-failed tool-gate rows remain; this classifier has no active rows to block.",
        }
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "result_failed_row_count": row_count,
        "meaning": "Result-failed rows remaining make completion or promotion inconsistent.",
    }


def build_result() -> dict[str, Any]:
    start = time.time()
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    tool_gate = read_json(TOOL_GATE)
    readiness = read_json(READINESS)
    rows = failed_tool_gate_rows(tool_gate)
    classified = [classify_row(row, readiness_by_result_path(readiness)) for row in rows]
    unknown = [row for row in classified if row["name"] not in EXPECTED_ROWS]
    class_counts = Counter(row["boundary_class"] for row in classified)
    z3_check = z3_completion_block(len(rows))

    positive = {
        "tool_gate_loaded": {
            "pass": TOOL_GATE.exists() and tool_gate.get("all_pass") is True,
            "tool_gate_path": rel(TOOL_GATE),
            "tool_gate_sha256": sha256(TOOL_GATE),
        },
        "result_not_all_pass_rows_classified": {
            "pass": len(rows) == len(classified) and len(unknown) == 0,
            "blocked_result_not_all_pass_count": len(rows),
            "unknown_count": len(unknown),
            "class_counts": dict(sorted(class_counts.items())),
        },
        "all_rows_remain_red_or_blocked": {
            "pass": all(row["result_all_pass"] is False and row["tool_gate_result_all_pass"] is False for row in classified),
            "row_statuses": {
                row["name"]: {
                    "result_all_pass": row["result_all_pass"],
                    "readiness_status": row["readiness_status"],
                    "tool_role_status": row["tool_role_status"],
                }
                for row in classified
            },
        },
        "no_schema_patch_would_be_honest": {
            "pass": all(row["repairable_schema_mistake"] is False for row in classified),
            "repair_lane_required_count": sum(1 for row in classified if row["repair_lane_required"]),
        },
        "z3_blocks_completion_or_promotion": z3_check,
    }
    boundary = {
        "promotion_disabled": {"pass": PROMOTION_ALLOWED is False, "value": PROMOTION_ALLOWED},
        "cleanup_not_authorized": {
            "pass": True,
            "value": False,
            "reason": "This classifier preserves failed receipts as failed/blocker evidence.",
        },
        "claim_ceiling_blocks_broad_claims": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["does not convert", "authorize cleanup", "physics", "consciousness"]),
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    graveyard_companions = {
        "paint_failed_receipts_green_control_killed": {
            "pass": True,
            "reason": "The current source receipts remain red or non-formal-boundary; this classifier only labels why.",
        },
        "threshold_tuning_after_failure_control_killed": {
            "pass": True,
            "reason": "No threshold, predicate, or target-source row is edited by this classifier.",
        },
        "validator_pass_as_tool_gate_pass_control_killed": {
            "pass": all(row["result_all_pass"] is False and row["tool_gate_result_all_pass"] is False for row in classified),
            "reason": "A schema-ready or non-formal-boundary receipt can still be a failed tool-gate result when result all_pass is false.",
        },
    }
    checks = {**positive, **boundary, **graveyard_companions}
    all_pass = all(bool(item.get("pass")) for item in checks.values())
    return {
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
        "math_object": "tool-gate result-not-all-pass blocker partition",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "source_hashes": {
            "tool_gate": {"path": rel(TOOL_GATE), "exists": TOOL_GATE.exists(), "sha256": sha256(TOOL_GATE)},
            "readiness_index": {"path": rel(READINESS), "exists": READINESS.exists(), "sha256": sha256(READINESS)},
        },
        "summary": {
            "all_pass": all_pass,
            "blocked_result_not_all_pass_count": len(rows),
            "classified_count": len(classified),
            "unknown_count": len(unknown),
            "honest_negative_count": sum(1 for row in classified if row["honest_negative"] is True),
            "repair_lane_required_count": sum(1 for row in classified if row["repair_lane_required"]),
            "schema_patch_authorized": False,
            "cleanup_authorized": False,
            "promotion_authorized": False,
            "class_counts": dict(sorted(class_counts.items())),
        },
        "classified_rows": classified,
        "unknown_rows": unknown,
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "paint_failed_receipts_green": {
                "pass": True,
                "status": "rejected",
                "reason": "Would erase real failed evidence.",
            },
            "rerun_all_four_broadly": {
                "pass": True,
                "status": "rejected",
                "reason": "Only narrow follow-up probes are admissible; broad reruns would mix independent failures.",
            },
            "cite_validator_schema_ready_as_success": {
                "pass": True,
                "status": "rejected",
                "reason": "Validator/schema readiness is not the same as all_pass scientific/tool-role success.",
            },
        },
        "open_choices": [
            "Keep the two reservoir counterevidence rows red and cite them only as failed-result boundaries.",
            "Open a narrow Axis0 path-entropy degeneracy falsifier before any per-lego ablation claims.",
            "Open a revised reservoir/readout design only if the counterevidence rows become active research targets.",
        ],
        "blockers": [],
        "open_blockers": [
            "The current failed receipts remain failed or blocked.",
            "This receipt is not cleanup authorization and not scientific promotion evidence.",
        ],
        "why_not_v4_probes": [
            "This consumes the current v5 tool-gate and readiness receipts.",
            "It is a classifier over current failed-result rows, not a legacy v4 probe.",
            "It edits no scientific target receipt and clears no gate.",
        ],
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "blocked_result_not_all_pass_count": result["summary"]["blocked_result_not_all_pass_count"],
                "classified_count": result["summary"]["classified_count"],
                "unknown_count": result["summary"]["unknown_count"],
                "out_path": rel(OUT_PATH),
                "promotion_authorized": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
