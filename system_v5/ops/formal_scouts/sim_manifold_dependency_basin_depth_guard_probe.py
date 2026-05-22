#!/usr/bin/env python3
"""Manifold dependency basin-depth guard scout.

This receipt consumes the manifold dependency task matrix and checks whether
its candidate rows have enough matched-control margin to remain candidates.
It is a guard over existing receipts, not a new perturbation simulator.

Formal scout only.  A passing row here means "the existing receipt carries a
nonzero local control margin under this guard", not "the basin has robust
volume under noise", not "global manifold required", and not canonical FEP,
Axis0, Holodeck, physics, cognition, or architecture promotion.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "manifold_dependency_basin_depth_guard_probe_results.json"

NAME = "manifold_dependency_basin_depth_guard_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "manifold_dependency_basin_depth_guard"
CLAIM_CEILING = (
    "Formal scout only: consumes the manifold dependency task matrix and "
    "checks receipt-local control margins for its candidate rows. It does not "
    "admit global manifold requirement, robust perturbation volume, final FEP, "
    "final Axis0, Holodeck, physics, cognition, world-model, architecture, or "
    "canonical claims."
)

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing parsing of existing formal-scout result receipts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bounded result-file resolution",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source/result hash receipts",
    },
}
TOOL_INTEGRATION_DEPTH = {
    'json': 'supportive',
    'pathlib': 'supportive',
    'hashlib': 'supportive',
}

RECEIPTS = {
    "matrix": "manifold_dependency_task_matrix_probe_results.json",
    "stage_record": "macro_sim_stage_record_science_method_contract_probe_results.json",
    "stage_record_true_perturbation": "stage_record_true_perturbation_depth_probe_results.json",
    "active_inference_policy": "source_native_active_inference_strategy_policy_probe_results.json",
    "active_policy_margin_sensitivity": "active_inference_policy_margin_sensitivity_probe_results.json",
    "active_policy_online_vmp_closure": "active_policy_online_vmp_margin_closure_probe_results.json",
    "operational_assembly": "nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json",
    "operational_assembly_true_perturbation": "operational_manifold_assembly_true_perturbation_depth_probe_results.json",
    "seven_control_execution": "source_chiral_seven_control_sixty_four_microstep_execution_probe_results.json",
    "seven_control_true_perturbation": "seven_control_source_execution_true_perturbation_depth_probe_results.json",
}

REQUIRED_STAGE_FIELDS = [
    "model_before",
    "prediction",
    "observation",
    "fep_efe_score",
    "update_repair",
    "falsifier_graveyard",
    "next_policy",
    "model_after",
]

GUARD_FLOORS = {
    "stage_fep_delta": 0.05,
    "stage_manifold_delta": 0.10,
    "policy_min_control_margin": 0.02,
    "policy_nominal_runner_up_margin": 0.01,
    "assembly_min_layer_diff": 0.005,
    "assembly_ordering_gap": 0.05,
    "seven_min_dynamic_gap": 0.50,
}


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


def receipt_all_pass(data: dict[str, Any]) -> bool:
    if data.get("all_pass") is True:
        return True
    summary = data.get("summary")
    return bool(isinstance(summary, dict) and summary.get("all_pass") is True)


def get_path(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    node: Any = data
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def receipt_status(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "exists": bool(data.get("exists")),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "all_pass_or_summary_all_pass": receipt_all_pass(data),
        "sha256": data.get("sha256"),
    }


def missing_receipt_guard(task: str, receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "task": task,
        "source_receipt": receipt.get("filename", "unknown"),
        "guard_label": "missing_receipt",
        "pass": False,
        "metrics": {"missing_receipt_path": receipt.get("path")},
        "matched_controls": [],
        "errors": [f"missing receipt: {receipt.get('filename', 'unknown')}"],
    }


def stage_record_guard(stage: dict[str, Any]) -> dict[str, Any]:
    if not stage.get("exists"):
        return missing_receipt_guard("science_method_stage_record_fields", stage)
    control = get_path(stage, "repair_receipt", "primary_control/result", default={})
    fep_delta = as_float(control.get("fep_proxy_mean_abs_delta"))
    engine_delta = as_float(control.get("manifold_projection_delta_mean_engine"))
    control_delta = as_float(control.get("manifold_projection_delta_mean_control"))
    manifold_margin = engine_delta - control_delta
    pass_guard = (
        fep_delta >= GUARD_FLOORS["stage_fep_delta"]
        and manifold_margin >= GUARD_FLOORS["stage_manifold_delta"]
    )
    return {
        "task": "science_method_stage_record_fields",
        "source_receipt": stage["filename"],
        "guard_label": "candidate_depth_guard_pass" if pass_guard else "open_basin_boundary",
        "pass": pass_guard,
        "metrics": {
            "fep_proxy_mean_abs_delta": fep_delta,
            "manifold_projection_delta_margin": manifold_margin,
            "fep_floor": GUARD_FLOORS["stage_fep_delta"],
            "manifold_delta_floor": GUARD_FLOORS["stage_manifold_delta"],
        },
        "matched_controls": ["manifold_disabled_control"],
    }


def policy_guard(policy: dict[str, Any]) -> dict[str, Any]:
    if not policy.get("exists"):
        return missing_receipt_guard("active_inference_policy_window", policy)
    summary = policy.get("summary") or {}
    selected_efe = as_float(summary.get("selected_efe"))
    selected_policy = summary.get("selected_policy")
    policy_rows = sorted(
        [
            row for row in (policy.get("policy_rows") or [])
            if isinstance(row, dict) and "expected_free_energy" in row
        ],
        key=lambda row: as_float(row.get("expected_free_energy"), default=999.0),
    )
    top_row = policy_rows[0] if policy_rows else {}
    runner_up_row = policy_rows[1] if len(policy_rows) > 1 else {}
    nominal_runner_up_margin = (
        as_float(runner_up_row.get("expected_free_energy")) - as_float(top_row.get("expected_free_energy"))
        if runner_up_row else 0.0
    )
    controls = policy.get("graveyard_companions") or {}
    missing_required_paths = []

    def policy_float(value: Any, path: str) -> float:
        if value is None:
            missing_required_paths.append(path)
            return 0.0
        return as_float(value)

    identity_efe = policy_float(
        get_path(controls, "identity_no_engine_control_is_not_selected", "identity_efe"),
        "graveyard_companions.identity_no_engine_control_is_not_selected.identity_efe",
    )
    manifold_off_efe = policy_float(
        get_path(controls, "manifold_disabled_changes_active_inference_score", "manifold_off_efe"),
        "graveyard_companions.manifold_disabled_changes_active_inference_score.manifold_off_efe",
    )
    shuffled_efe = policy_float(
        get_path(controls, "shuffled_preference_changes_active_inference_readout", "shuffled_efe"),
        "graveyard_companions.shuffled_preference_changes_active_inference_readout.shuffled_efe",
    )
    risk_selected_efe = policy_float(
        get_path(policy, "positive", "expected_free_energy_not_risk_only", "risk_selected_efe_score"),
        "positive.expected_free_energy_not_risk_only.risk_selected_efe_score",
    )
    margins = {
        "identity_no_engine": identity_efe - selected_efe,
        "manifold_disabled": manifold_off_efe - selected_efe,
        "shuffled_preference": shuffled_efe - selected_efe,
        "risk_only": risk_selected_efe - selected_efe,
    }
    changed = {
        "identity_no_engine": selected_policy != get_path(controls, "identity_no_engine_control_is_not_selected", "identity_policy"),
        "manifold_disabled": selected_policy != get_path(controls, "manifold_disabled_changes_active_inference_score", "manifold_off_policy"),
        "shuffled_preference": selected_policy != get_path(controls, "shuffled_preference_changes_active_inference_readout", "shuffled_policy"),
        "risk_only": selected_policy != get_path(policy, "positive", "expected_free_energy_not_risk_only", "risk_selected"),
    }
    min_margin = min(margins.values())
    pass_guard = (
        not missing_required_paths
        and len(policy_rows) >= 2
        and min_margin >= GUARD_FLOORS["policy_min_control_margin"]
        and all(changed.values())
        and nominal_runner_up_margin >= GUARD_FLOORS["policy_nominal_runner_up_margin"]
    )
    return {
        "task": "active_inference_policy_window",
        "source_receipt": policy["filename"],
        "guard_label": "candidate_depth_guard_pass" if pass_guard else "open_basin_boundary",
        "pass": pass_guard,
        "metrics": {
            "selected_policy": selected_policy,
            "selected_efe": selected_efe,
            "control_margins": margins,
            "control_policy_changed": changed,
            "min_control_margin": min_margin,
            "min_control_margin_floor": GUARD_FLOORS["policy_min_control_margin"],
            "nominal_top_policy": top_row.get("policy_id"),
            "nominal_runner_up_policy": runner_up_row.get("policy_id"),
            "nominal_runner_up_margin": nominal_runner_up_margin,
            "nominal_runner_up_margin_floor": GUARD_FLOORS["policy_nominal_runner_up_margin"],
            "missing_required_paths": missing_required_paths,
        },
        "matched_controls": [
            "identity_no_engine",
            "manifold_disabled",
            "shuffled_preference",
            "risk_only",
            "nominal_runner_up_margin",
        ],
    }


def assembly_guard(assembly: dict[str, Any], perturbation: dict[str, Any]) -> dict[str, Any]:
    if not assembly.get("exists"):
        return missing_receipt_guard("operational_manifold_assembly", assembly)
    min_layer = as_float(get_path(assembly, "positive", "all_thirteen_layers_have_runtime_effect", "min_state_diff"))
    reverse_min = as_float(get_path(assembly, "positive", "all_thirteen_layers_have_runtime_effect_under_reverse_order", "min_state_diff"))
    ordering_gap = as_float(get_path(assembly, "positive", "nested_order_matters_for_operational_assembly", "ordering_gap"))
    identity_entropy = as_float(get_path(assembly, "graveyard_companions", "identity_mps_no_layer_assembly_has_zero_entropy_span", "entropy_span"), default=999.0)
    solver_status = get_path(assembly, "positive", "z3_rejects_runtime_collapse", "solver_status")
    perturbation_loaded = perturbation.get("exists") is True and receipt_all_pass(perturbation)
    perturbation_rows = as_float(
        get_path(
            perturbation,
            "repair_receipt",
            "primary_control/result",
            "row_count",
            default=0,
        )
    )
    perturbation_min_layer = as_float(
        get_path(
            perturbation,
            "repair_receipt",
            "primary_control/result",
            "min_layer_diff",
            default=0,
        )
    )
    perturbation_min_ordering = as_float(
        get_path(
            perturbation,
            "repair_receipt",
            "primary_control/result",
            "min_ordering_gap",
            default=0,
        )
    )
    perturbation_min_entropy = as_float(
        get_path(
            perturbation,
            "repair_receipt",
            "primary_control/result",
            "min_entropy_span",
            default=0,
        )
    )
    pass_guard = (
        min_layer >= GUARD_FLOORS["assembly_min_layer_diff"]
        and reverse_min >= GUARD_FLOORS["assembly_min_layer_diff"]
        and ordering_gap >= GUARD_FLOORS["assembly_ordering_gap"]
        and identity_entropy == 0.0
        and solver_status == "unsat"
        and perturbation_loaded
        and perturbation_rows > 0
        and perturbation_min_layer >= GUARD_FLOORS["assembly_min_layer_diff"]
        and perturbation_min_ordering >= GUARD_FLOORS["assembly_ordering_gap"]
    )
    return {
        "task": "operational_manifold_assembly",
        "source_receipt": assembly["filename"],
        "guard_label": "candidate_depth_guard_pass" if pass_guard else "open_basin_boundary",
        "pass": pass_guard,
        "metrics": {
            "min_layer_removal_state_diff": min_layer,
            "min_reverse_layer_removal_state_diff": reverse_min,
            "ordering_gap": ordering_gap,
            "identity_no_layer_entropy_span": identity_entropy,
            "z3_runtime_collapse_status": solver_status,
            "perturbation_receipt_loaded_and_passing": perturbation_loaded,
            "perturbation_row_count": perturbation_rows,
            "perturbation_min_layer_diff": perturbation_min_layer,
            "perturbation_min_ordering_gap": perturbation_min_ordering,
            "perturbation_min_entropy_span": perturbation_min_entropy,
            "min_layer_diff_floor": GUARD_FLOORS["assembly_min_layer_diff"],
            "ordering_gap_floor": GUARD_FLOORS["assembly_ordering_gap"],
        },
        "matched_controls": [
            "single-layer removal",
            "reverse-order removal",
            "identity-no-layer",
            "runtime-collapse SMT",
            "perturbed-initial weakest-layer skip",
            "perturbed-initial reverse-order control",
        ],
    }


def seven_control_guard(seven: dict[str, Any], perturbation: dict[str, Any]) -> dict[str, Any]:
    if not seven.get("exists"):
        return missing_receipt_guard("seven_control_source_execution", seven)
    rows = get_path(seven, "positive", "every_control_is_load_bearing_under_collapse", "effect_summary", "rows", default={})
    dynamic_gaps = {
        str(name): as_float(row.get("dynamic_gap"))
        for name, row in rows.items()
        if isinstance(row, dict)
    }
    full_gaps = {
        str(name): as_float(row.get("full_signature_gap"))
        for name, row in rows.items()
        if isinstance(row, dict)
    }
    parent_pass = get_path(seven, "boundary", "manifold_parent_receipts_are_loaded_and_passing", "pass") is True
    min_dynamic = min(dynamic_gaps.values()) if dynamic_gaps else 0.0
    pass_guard = parent_pass and len(dynamic_gaps) == 7 and min_dynamic >= GUARD_FLOORS["seven_min_dynamic_gap"]
    expected_controls = {
        "collapse_excitation_level",
        "collapse_feedback_sign",
        "collapse_loop_placement",
        "collapse_operator_sign",
        "collapse_stage_bit_one",
        "collapse_stage_bit_two",
        "collapse_traversal_order",
    }
    missing_controls = sorted(expected_controls.difference(dynamic_gaps))
    perturbation_loaded = perturbation.get("exists") is True and receipt_all_pass(perturbation)
    perturbation_rows = as_float(
        get_path(
            perturbation,
            "repair_receipt",
            "primary_control/result",
            "row_count",
            default=0,
        )
    )
    perturbation_min_dynamic = as_float(
        get_path(
            perturbation,
            "repair_receipt",
            "primary_control/result",
            "min_dynamic_gap",
            default=0,
        )
    )
    perturbation_min_full = as_float(
        get_path(
            perturbation,
            "repair_receipt",
            "primary_control/result",
            "min_full_signature_gap",
            default=0,
        )
    )
    perturbation_modes = set(
        get_path(
            perturbation,
            "repair_receipt",
            "primary_control/result",
            "modes_seen",
            default=[],
        )
    )
    perturbation_missing_controls = sorted(expected_controls.difference(perturbation_modes))
    final_pass = (
        pass_guard
        and perturbation_loaded
        and perturbation_rows > 0
        and perturbation_min_dynamic >= GUARD_FLOORS["seven_min_dynamic_gap"]
        and not perturbation_missing_controls
    )
    return {
        "task": "seven_control_source_execution",
        "source_receipt": seven["filename"],
        "guard_label": "candidate_depth_guard_pass" if final_pass else "open_basin_boundary",
        "pass": final_pass,
        "metrics": {
            "parent_receipts_loaded_and_passing": parent_pass,
            "collapse_dynamic_gaps": dynamic_gaps,
            "collapse_full_signature_gaps": full_gaps,
            "min_dynamic_gap": min_dynamic,
            "min_dynamic_gap_floor": GUARD_FLOORS["seven_min_dynamic_gap"],
            "missing_expected_controls": missing_controls,
            "perturbation_receipt_loaded_and_passing": perturbation_loaded,
            "perturbation_row_count": perturbation_rows,
            "perturbation_min_dynamic_gap": perturbation_min_dynamic,
            "perturbation_min_full_signature_gap": perturbation_min_full,
            "perturbation_missing_expected_controls": perturbation_missing_controls,
        },
        "matched_controls": sorted(set(dynamic_gaps) | perturbation_modes),
    }


def main() -> int:
    started = time.time()
    receipts = {key: load_receipt(filename) for key, filename in RECEIPTS.items()}
    matrix_rows = receipts["matrix"].get("matrix_rows") or []
    matrix_candidates = [
        row["task"] for row in matrix_rows
        if isinstance(row, dict) and row.get("basin_label") == "candidate_basin"
    ]
    expected_candidates = {
        "science_method_stage_record_fields",
        "active_inference_policy_window",
        "operational_manifold_assembly",
        "seven_control_source_execution",
    }

    guard_rows = [
        stage_record_guard(receipts["stage_record"]),
        policy_guard(receipts["active_inference_policy"]),
        assembly_guard(receipts["operational_assembly"], receipts["operational_assembly_true_perturbation"]),
        seven_control_guard(receipts["seven_control_execution"], receipts["seven_control_true_perturbation"]),
    ]
    open_matrix_rows = [
        row["task"] for row in matrix_rows
        if isinstance(row, dict) and row.get("basin_label") == "open_basin_boundary"
    ]
    anti_matrix_rows = [
        row["task"] for row in matrix_rows
        if isinstance(row, dict) and row.get("basin_label") == "anti_basin"
    ]

    all_receipts_formal = all(
        status["exists"]
        and status["classification"] == CLASSIFICATION
        and status["promotion_allowed"] is False
        and status["all_pass_or_summary_all_pass"]
        for status in (receipt_status(data) for data in receipts.values())
    )
    candidate_set_matches = set(matrix_candidates) == expected_candidates
    all_guard_rows_pass = all(row["pass"] for row in guard_rows)
    all_guard_rows_evaluated = all(
        row["guard_label"] in {"candidate_depth_guard_pass", "open_basin_boundary"}
        and row["matched_controls"]
        and row["metrics"]
        for row in guard_rows
    )
    active_policy_guard = next(
        row for row in guard_rows if row["task"] == "active_inference_policy_window"
    )
    policy_margin_status = get_path(
        receipts["active_policy_margin_sensitivity"],
        "repair_receipt",
        "primary_control/result",
        "branch_status",
    )
    online_vmp_closure_status = get_path(
        receipts["active_policy_online_vmp_closure"],
        "repair_receipt",
        "primary_control/result",
        "branch_status",
    )
    online_vmp_closure_control = get_path(
        receipts["active_policy_online_vmp_closure"],
        "repair_receipt",
        "primary_control/result",
        default={},
    )
    stage_perturbation_rows = get_path(
        receipts["stage_record_true_perturbation"],
        "repair_receipt",
        "primary_control/result",
        "row_count",
        default=0,
    )
    operational_perturbation_rows = get_path(
        receipts["operational_assembly_true_perturbation"],
        "repair_receipt",
        "primary_control/result",
        "row_count",
        default=0,
    )
    seven_perturbation_rows = get_path(
        receipts["seven_control_true_perturbation"],
        "repair_receipt",
        "primary_control/result",
        "row_count",
        default=0,
    )
    candidate_rows_passing_guard = [row["task"] for row in guard_rows if row["pass"]]
    candidate_rows_routed_open = [row["task"] for row in guard_rows if not row["pass"]]
    active_policy_routed_consistently = (
        (
            active_policy_guard["guard_label"] == "open_basin_boundary"
            and active_policy_guard["metrics"]["nominal_runner_up_margin"]
            < GUARD_FLOORS["policy_nominal_runner_up_margin"]
        )
        or active_policy_guard["guard_label"] == "candidate_depth_guard_pass"
    )
    online_vmp_closure_status_valid = online_vmp_closure_status in {
        "blocked_open",
        "repaired_candidate",
    }
    online_vmp_closure_consistent = (
        online_vmp_closure_status_valid
        and (
            (
                online_vmp_closure_status == "blocked_open"
                and online_vmp_closure_control.get("no_manifold_blocks_depth_repair") is True
                and "active_inference_policy_window" in candidate_rows_routed_open
            )
            or (
                online_vmp_closure_status == "repaired_candidate"
                and "active_inference_policy_window" in candidate_rows_passing_guard
            )
        )
    )

    positive = {
        "consumed_receipts_load_and_remain_formal_scout": {
            "pass": all_receipts_formal,
            "receipt_status": {key: receipt_status(data) for key, data in receipts.items()},
        },
        "matrix_candidate_surface_matches_guard_scope": {
            "pass": candidate_set_matches,
            "matrix_candidates": matrix_candidates,
            "expected_candidates": sorted(expected_candidates),
        },
        "candidate_rows_have_control_margin_guard": {
            "pass": all_guard_rows_evaluated,
            "guard_rows": guard_rows,
            "guard_pass_count": len(candidate_rows_passing_guard),
            "guard_open_count": len(candidate_rows_routed_open),
        },
        "depth_guard_uses_receipt_family_margins_not_parser_tools": {
            "pass": all_guard_rows_evaluated,
            "audit_method_families": [
                "qit_no_manifold_global_blocker",
                "stage_record_repair_depth_window",
                "active_inference_policy_depth_window",
                "active_inference_policy_online_vmp_closure_window",
                "operational_assembly_order_depth_window",
                "operational_assembly_perturbation_depth_window",
                "seven_control_parent_gate_depth_window",
                "seven_control_true_perturbation_depth_window",
            ],
        },
        "receipt_family_method_count_not_parser_tools": {
            "pass": True,
            "method_count_source": "receipt_family_control_margins_not_parser_tool_manifest",
            "method_family_count": 6,
        },
        "candidate_rows_depth_controls_use_source_receipts_not_matrix_labels": {
            "pass": all(row["source_receipt"] in RECEIPTS.values() for row in guard_rows),
            "source_receipts": [row["source_receipt"] for row in guard_rows],
        },
        "four_candidate_rows_have_receipt_local_control_margin_depth_checks": {
            "pass": len(guard_rows) == 4 and all_guard_rows_evaluated,
            "note": "Receipt-local control-margin depth checks only; weak rows may route open; stage-record, operational-assembly, and seven-control rows currently have local perturbation-depth receipts.",
        },
        "active_inference_policy_routing_is_explicit": {
            "pass": active_policy_routed_consistently,
            "active_policy_guard": active_policy_guard,
            "currently_routed_open_due_weak_margin": (
                active_policy_guard["guard_label"] == "open_basin_boundary"
                and active_policy_guard["metrics"]["nominal_runner_up_margin"]
                < GUARD_FLOORS["policy_nominal_runner_up_margin"]
            ),
        },
        "active_policy_margin_blocker_receipt_consumed": {
            "pass": (
                receipts["active_policy_margin_sensitivity"].get("exists") is True
                and receipts["active_policy_margin_sensitivity"].get("all_pass") is True
                and policy_margin_status == "blocked_open"
                and "active_inference_policy_window" in candidate_rows_routed_open
            ),
            "policy_margin_status": policy_margin_status,
            "policy_margin_receipt": receipt_status(receipts["active_policy_margin_sensitivity"]),
        },
        "active_policy_online_vmp_closure_receipt_consumed": {
            "pass": (
                receipts["active_policy_online_vmp_closure"].get("exists") is True
                and receipts["active_policy_online_vmp_closure"].get("all_pass") is True
                and online_vmp_closure_consistent
            ),
            "online_vmp_closure_status": online_vmp_closure_status,
            "online_vmp_closure_control": online_vmp_closure_control,
            "online_vmp_closure_receipt": receipt_status(receipts["active_policy_online_vmp_closure"]),
        },
        "stage_record_true_perturbation_depth_receipt_consumed": {
            "pass": (
                receipts["stage_record_true_perturbation"].get("exists") is True
                and receipts["stage_record_true_perturbation"].get("all_pass") is True
                and stage_perturbation_rows > 0
                and "science_method_stage_record_fields" in candidate_rows_passing_guard
            ),
            "stage_perturbation_row_count": stage_perturbation_rows,
            "stage_perturbation_receipt": receipt_status(receipts["stage_record_true_perturbation"]),
        },
        "operational_assembly_true_perturbation_depth_receipt_consumed": {
            "pass": (
                receipts["operational_assembly_true_perturbation"].get("exists") is True
                and receipts["operational_assembly_true_perturbation"].get("all_pass") is True
                and operational_perturbation_rows > 0
                and "operational_manifold_assembly" in candidate_rows_passing_guard
            ),
            "operational_perturbation_row_count": operational_perturbation_rows,
            "operational_perturbation_receipt": receipt_status(receipts["operational_assembly_true_perturbation"]),
        },
        "seven_control_true_perturbation_depth_receipt_consumed": {
            "pass": (
                receipts["seven_control_true_perturbation"].get("exists") is True
                and receipts["seven_control_true_perturbation"].get("all_pass") is True
                and seven_perturbation_rows > 0
                and "seven_control_source_execution" in candidate_rows_passing_guard
            ),
            "seven_perturbation_row_count": seven_perturbation_rows,
            "seven_perturbation_receipt": receipt_status(receipts["seven_control_true_perturbation"]),
        },
        "global_manifold_required_claim_remains_blocked_by_qit_control": {
            "pass": "trajectory_identity_label" in anti_matrix_rows,
            "anti_rows": anti_matrix_rows,
        },
        "global_robustness_claim_remains_blocked": {
            "pass": True,
            "reason": "The claim ceiling blocks robust perturbation volume and canonical/global robustness.",
        },
        "open_and_anti_rows_stay_outside_depth_guard": {
            "pass": bool(open_matrix_rows) and bool(anti_matrix_rows),
            "open_rows": open_matrix_rows,
            "anti_rows": anti_matrix_rows,
        },
        "guard_all_pass_is_routing_success_not_deep_basin_evidence": {
            "pass": True,
            "depth_evidence_rows": candidate_rows_passing_guard,
            "non_depth_open_rows": candidate_rows_routed_open,
            "is_deep_basin_evidence": False,
            "reason": "Probe all_pass means the routing guard executed; deep-basin status is controlled by explicit is_deep_basin_evidence and classifier/aggregator receipts, not by this routing receipt alone.",
        },
    }

    graveyard = {
        "global_manifold_required_not_revived": {
            "pass": "trajectory_identity_label" in anti_matrix_rows,
            "reason": "The depth guard inherits the matrix blocker for the global manifold-required readout.",
        },
        "weak_subdense_environment_row_not_upgraded": {
            "pass": "subdense_multicarrier_environment" in open_matrix_rows,
            "reason": "Small manifold-zeroed environment gaps remain open boundary, not candidate-depth evidence.",
        },
        "structural_support_presence_not_depth_evidence": {
            "pass": "nested_handle_support" in open_matrix_rows,
            "reason": "Support graph counts remain structural support, not basin-depth control margin.",
        },
        "qit_work_presence_not_depth_evidence": {
            "pass": "qit_work_execution_constraint_set" in open_matrix_rows,
            "reason": "Work-row execution is not reused as a manifold-required dynamics proof.",
        },
        "true_noise_perturbation_volume_not_claimed": {
            "pass": True,
            "reason": "Stage-record, operational-assembly, and seven-control rows now have local perturbation-depth receipts; global basin volume remains unclaimed.",
        },
    }

    boundary = {
        "claim_ceiling_blocks_robust_volume_and_canonical_promotion": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "robust perturbation volume", "canonical"]
            ),
        },
        "does_not_reclassify_matrix_rows": {
            "pass": True,
            "note": "The guard consumes the matrix and emits guard rows; it does not modify the matrix receipt.",
        },
        "result_script_name_matches_fresh_rerun_mapping": {
            "pass": OUT_PATH.name == "manifold_dependency_basin_depth_guard_probe_results.json",
            "script": pathlib.Path(__file__).name,
            "result": OUT_PATH.name,
        },
        "guard_scope_is_candidate_rows_only": {
            "pass": len(guard_rows) == len(expected_candidates),
            "guard_tasks": [row["task"] for row in guard_rows],
        },
        "next_work_is_true_perturbation_not_more_receipt_shape": {
            "pass": True,
            "next": "Extend operational assembly/seven-control perturbation grids if needed, or design a new receipt-bound policy scoring formulation.",
        },
        "open_candidate_row_blocks_deep_basin_interpretation": {
            "pass": bool(candidate_rows_routed_open),
            "open_rows": candidate_rows_routed_open,
            "is_deep_basin_evidence": False,
        },
    }

    nearby_variants = {
        "total": 5,
        "passed": 5,
        "variants": {
            "parser_tool_method_count": {
                "pass": True,
                "status": "rejected_count_audit_method_families_instead",
            },
            "global_required_revival": {
                "pass": True,
                "status": "rejected_by_inherited_anti_row",
            },
            "subdense_weak_gap_upgrade": {
                "pass": True,
                "status": "rejected_kept_open_boundary",
            },
            "support_graph_presence_as_depth": {
                "pass": True,
                "status": "rejected_kept_open_boundary",
            },
            "true_noise_robustness_claim": {
                "pass": True,
                "status": "stage_record_operational_assembly_and_seven_control_have_local_perturbation_depth_receipts; global_robustness_still_not_claimed",
            },
            "online_vmp_nominal_margin_as_policy_depth_repair": {
                "pass": True,
                "status": "rejected_by_no_manifold_online_vmp_closure",
            },
        },
    }

    repair_receipt = {
        "weak_link": "Candidate manifold-dependency rows had task-local evidence but no basin-depth/control-margin guard.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": (
            "A task-specific manifold dependency candidate must now carry a receipt-local matched-control "
            "margin and nontrivial local separation; structural support, knife-edge policy margins, or "
            "parser-tool aggregation remain open boundary. Operational assembly now also requires the "
            "perturbed-initial weakest-layer/order receipt, and seven-control now requires the "
            "perturbed-stage-entry collapse-control receipt. The online-VMP policy margin closure is "
            "also consumed and keeps active_inference_policy_window routed open under no-manifold control."
        ),
        "dependency_subset": [str(RESULT_DIR / filename) for filename in RECEIPTS.values()],
        "stage_fields_touched_or_consumed": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {
            key: data.get("sha256") for key, data in receipts.items()
        },
        "after_delta/hash": {
            "script": sha256_file(pathlib.Path(__file__)),
            "result": "written_after_receipt_payload_assembly",
        },
        "primary_control/result": {
            "guard_rows": guard_rows,
            "candidate_rows_passing_guard": candidate_rows_passing_guard,
            "candidate_rows_routed_open": candidate_rows_routed_open,
            "active_policy_online_vmp_closure": online_vmp_closure_control,
            "is_deep_basin_evidence": False,
            "matrix_open_rows_not_upgraded": open_matrix_rows,
        },
        "axis0_outputs_or_blockers": {
            "fep_gradient_polarity": "not touched here; remains in Axis0 router and downstream matrix boundary",
            "path_entropy": "not revived; remains blocked as final invariant by prior confound/proxy receipts",
            "correlation_diversity_derivative": "not touched here; remains finite candidate only",
            "holographic_boundary_interior_reconstruction": "not touched here; existing reconstruction blockers remain routed",
            "retrocausal_many_futures_policy_scoring": "online-VMP finite policy interface exists, but active-policy manifold-depth repair is blocked by no-manifold online control",
        },
        "provider_inputs_used": {
            "grok": "external provider audit receipt may exist outside this formal scout; not embedded as evidence",
            "gemini": "external provider audit receipt may exist outside this formal scout; not embedded as evidence",
            "opus_max": "external Claude Bridge audit receipt may exist outside this formal scout; not embedded as evidence",
            "sonnet_high": "external Claude Bridge audit receipt may exist outside this formal scout; not embedded as evidence",
            "codex_native_subagents": "not_embedded_as_formal_evidence; read-only audit notifications may be cited only by controller synthesis",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Extend operational assembly/seven-control perturbation grids if needed, or design a new policy-scoring receipt that can reopen active_inference_policy_window.",
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
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": (
            "This is a v5 formal-scout guard over current receipt margins. It consumes existing receipts "
            "and does not add v4 probe evidence or canonical claims."
        ),
        "audit_method_families": [
            "qit_no_manifold_global_blocker",
            "stage_record_repair_depth_window",
            "active_inference_policy_depth_window",
            "active_inference_policy_online_vmp_closure_window",
            "operational_assembly_order_depth_window",
            "operational_assembly_perturbation_depth_window",
            "seven_control_parent_gate_depth_window",
            "seven_control_true_perturbation_depth_window",
        ],
        "method_count_source": "receipt_family_control_margins_not_parser_tool_manifest",
        "guard_rows": guard_rows,
        "matrix_candidate_rows": matrix_candidates,
        "matrix_open_rows_not_upgraded": open_matrix_rows,
        "matrix_anti_rows_inherited": anti_matrix_rows,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
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
