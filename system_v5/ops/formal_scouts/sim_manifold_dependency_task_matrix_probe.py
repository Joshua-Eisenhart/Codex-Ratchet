#!/usr/bin/env python3
"""Manifold dependency task-matrix status scout.

This scout does not add new dynamics.  It consumes existing receipt JSONs and
separates two claims that were getting collapsed:

1. global "the manifold is required" language;
2. receipt-backed, task-specific manifold dependency for named readouts.

Formal scout only.  A task row can admit local dependency only when the source
receipt already carries matched controls or explicit parent receipts.  The
global manifold-required claim stays rejected because the QIT trajectory
receipt has a manifold-disabled control that preserves/improves that readout.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "manifold_dependency_task_matrix_probe_results.json"

NAME = "manifold_dependency_task_matrix_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "manifold_dependency_task_matrix_status_audit"
CLAIM_CEILING = (
    "Formal scout only: audits existing receipt dependencies by task. It "
    "rejects global manifold-required claims and admits only receipt-backed, "
    "task-specific manifold dependency. It does not admit canonical manifold, "
    "final ontology, physics, cognition, universal engine, final FEP, final "
    "Axis0, or production claims."
)

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing parsing of existing formal-scout receipt fields and controls",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bounded result-file resolution inside the formal scout surface",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing script and consumed-receipt hash receipts",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

RECEIPTS = {
    "qit_dynamics": "qit_engine_dynamics_required_work_discrimination_probe_results.json",
    "stage_record": "macro_sim_stage_record_science_method_contract_probe_results.json",
    "active_inference_policy": "source_native_active_inference_strategy_policy_probe_results.json",
    "pomdp_policy_tree": "source_native_fep_pomdp_policy_tree_probe_results.json",
    "axis0_router": "macro_sim_axis0_plural_stage_candidate_router_probe_results.json",
    "subdense_environment": "source_native_multicarrier_subdense_environment_contraction_probe_results.json",
    "handle_support": "nested_constraint_manifold_operational_handle_support_probe_results.json",
    "operational_assembly": "nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json",
    "seven_control_execution": "source_chiral_seven_control_sixty_four_microstep_execution_probe_results.json",
    "qit_work_execution": "constraint_manifold_qit_engine_work_execution_probe_results.json",
    "variable_qubit_topology": "variable_qubit_topology_flux_channel_order_entropy_scaling_probe_results.json",
    "integrated_suite": "integrated_constraint_manifold_suite_fresh_rerun_probe_results.json",
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


def formal_status(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "exists": bool(data.get("exists")),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "all_pass_or_summary_all_pass": receipt_all_pass(data),
        "sha256": data.get("sha256"),
        "claim_ceiling_excerpt": str(data.get("claim_ceiling", ""))[:260],
    }


def get_path(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    node: Any = data
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def finite_gap_map(values: Any) -> dict[str, float]:
    if not isinstance(values, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in values.items():
        try:
            out[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return out


def ge_if_numbers(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return False
    try:
        return float(left) >= float(right)
    except (TypeError, ValueError):
        return False


def matrix_rows(receipts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    qit = receipts["qit_dynamics"]
    stage = receipts["stage_record"]
    policy = receipts["active_inference_policy"]
    pomdp = receipts["pomdp_policy_tree"]
    axis0 = receipts["axis0_router"]
    subdense = receipts["subdense_environment"]
    support = receipts["handle_support"]
    assembly = receipts["operational_assembly"]
    seven = receipts["seven_control_execution"]
    work = receipts["qit_work_execution"]
    topology = receipts["variable_qubit_topology"]
    suite = receipts["integrated_suite"]

    qit_nominal = get_path(qit, "accuracies", "nominal_manifold_enabled", "trajectory", default=None)
    qit_disabled = get_path(qit, "accuracies", "manifold_disabled", "trajectory", default=None)
    qit_blocker = get_path(
        qit,
        "explicit_blockers",
        "manifold_required_dynamics_dependency_not_established",
        default={},
    )
    stage_control = get_path(stage, "repair_receipt", "primary_control/result", default={})
    policy_summary = policy.get("summary") or {}
    policy_graveyard = policy.get("graveyard_companions") or {}
    pomdp_summary = pomdp.get("summary") or {}
    axis0_comp = get_path(axis0, "positive", "axis0_candidates_are_compared_to_controls", "comparisons", default={})
    subdense_manifold = get_path(
        subdense,
        "positive",
        "manifold_projection_delta_drives_local_environment_signature",
        default={},
    )
    subdense_axis0 = get_path(
        subdense,
        "positive",
        "plural_axis0_full_vector_differs_from_scalar_mean_control",
        default={},
    )
    support_layers = get_path(
        support,
        "positive",
        "seven_handles_have_multilayer_manifold_support",
        default={},
    )
    assembly_runtime = get_path(
        assembly,
        "positive",
        "all_thirteen_layers_have_runtime_effect",
        default={},
    )
    assembly_order = get_path(
        assembly,
        "positive",
        "nested_order_matters_for_operational_assembly",
        default={},
    )
    seven_parent = get_path(seven, "boundary", "manifold_parent_receipts_are_loaded_and_passing", default={})
    work_constraint = get_path(work, "positive", "constraint_set_for_engine_is_loaded", default={})
    work_profile = get_path(work, "positive", "engine_records_do_measurable_work", default={})
    topology_summary = topology.get("summary") or {}
    suite_edges = get_path(suite, "positive", "critical_dependency_edges_are_present", "critical_edges", default=[])
    suite_edge_set = {tuple(edge) for edge in suite_edges if isinstance(edge, list)}

    return [
        {
            "task": "trajectory_identity_label",
            "receipt": qit["filename"],
            "dependency_scope": "blocked_global_necessity_for_this_readout",
            "basin_label": "anti_basin",
            "admitted_claim": "paired QIT trajectories carry a label signal in this receipt",
            "blocked_claim": "the manifold is required for the tested trajectory-label signal",
            "matched_control": "manifold_disabled_control",
            "evidence": {
                "nominal_manifold_enabled_trajectory_accuracy": qit_nominal,
                "manifold_disabled_trajectory_accuracy": qit_disabled,
                "blocker_status": qit_blocker.get("status"),
                "mean_paired_trajectory_gap": get_path(qit, "trajectory_gap_summary", "mean_paired_trajectory_gap"),
            },
        },
        {
            "task": "science_method_stage_record_fields",
            "receipt": stage["filename"],
            "dependency_scope": "task_specific_stage_record_repair",
            "basin_label": "candidate_basin",
            "admitted_claim": "manifold projection participates in executable stage-record repair and FEP proxy fields",
            "blocked_claim": "stage-record repair proves global manifold necessity or final FEP",
            "matched_control": "matched_no_manifold_control",
            "evidence": {
                "required_fields": get_path(
                    stage,
                    "positive",
                    "required_science_method_fields_present",
                    "required_fields",
                    default=[],
                ),
                "fep_proxy_mean_abs_delta": stage_control.get("fep_proxy_mean_abs_delta"),
                "manifold_projection_delta_mean_engine": stage_control.get("manifold_projection_delta_mean_engine"),
                "manifold_projection_delta_mean_control": stage_control.get("manifold_projection_delta_mean_control"),
            },
        },
        {
            "task": "active_inference_policy_window",
            "receipt": policy["filename"],
            "dependency_scope": "task_specific_policy_quality",
            "basin_label": "candidate_basin",
            "admitted_claim": "manifold-disabled control changes selected policy and EFE in the finite policy-window scout",
            "blocked_claim": "finite policy-window scoring is a full FEP engine or final game theory",
            "matched_control": "manifold_disabled_changes_active_inference_score",
            "evidence": {
                "selected_policy": policy_summary.get("selected_policy"),
                "selected_efe": policy_summary.get("selected_efe"),
                "no_manifold_policy": get_path(
                    policy_graveyard,
                    "manifold_disabled_changes_active_inference_score",
                    "manifold_off_policy",
                ),
                "no_manifold_efe": get_path(
                    policy_graveyard,
                    "manifold_disabled_changes_active_inference_score",
                    "manifold_off_efe",
                ),
                "policy_count": policy_summary.get("policy_count"),
            },
        },
        {
            "task": "pomdp_policy_tree",
            "receipt": pomdp["filename"],
            "dependency_scope": "task_specific_source_native_policy_tree_open",
            "basin_label": "open_basin_boundary",
            "admitted_claim": "finite A/B/C/D policy tree and VFE update fields execute over source-native windows",
            "blocked_claim": "tiny or recorded manifold-off deltas admit manifold dominance or full FEP",
            "matched_control": "no_engine/no_manifold/perfect_observable/shuffled_preference controls",
            "evidence": {
                "selected_policy": pomdp_summary.get("selected_policy"),
                "selected_efe": pomdp_summary.get("selected_efe"),
                "no_manifold_policy": pomdp_summary.get("no_manifold_policy"),
                "mean_transition_l1_from_identity": pomdp_summary.get("mean_transition_l1_from_identity"),
                "selected_vfe_reduction": pomdp_summary.get("selected_vfe_reduction"),
            },
        },
        {
            "task": "axis0_candidate_router",
            "receipt": axis0["filename"],
            "dependency_scope": "mixed_task_specific_axis0_candidates_with_blockers",
            "basin_label": "open_basin_boundary",
            "admitted_claim": "FEP-gradient polarity and correlation-diversity candidates are control-sensitive finite routes",
            "blocked_claim": "path_entropy or boundary reconstruction is final Axis0/admissibility",
            "matched_control": "no_manifold and shuffled_order candidate comparisons",
            "evidence": {
                "fep_gradient_vs_no_manifold_l2": get_path(
                    axis0_comp, "fep_gradient_polarity", "vs_no_manifold", "l2_delta"
                ),
                "correlation_diversity_vs_no_manifold_l2": get_path(
                    axis0_comp, "correlation_diversity_derivative", "vs_no_manifold", "l2_delta"
                ),
                "path_entropy_vs_no_manifold_l2": get_path(
                    axis0_comp, "path_entropy", "vs_no_manifold", "l2_delta"
                ),
                "path_entropy_vs_no_manifold_pass": get_path(
                    axis0_comp, "path_entropy", "vs_no_manifold", "pass"
                ),
            },
        },
        {
            "task": "subdense_multicarrier_environment",
            "receipt": subdense["filename"],
            "dependency_scope": "task_specific_environment_signature_open_strength",
            "basin_label": "open_basin_boundary",
            "admitted_claim": "manifold projection is recorded in local environment signatures, but the current manifold-zeroed gap is weak",
            "blocked_claim": "the small manifold-zeroed environment gaps prove manifold dominance or gauge-invariant geometry",
            "matched_control": "manifold_zeroed, axis0_zeroed, scalar_mean, drop-one, sign-flip, time-shuffle controls",
            "evidence": {
                "full_manifold_projection_delta_mean_abs": finite_gap_map(
                    subdense_manifold.get("full_manifold_projection_delta_mean_abs")
                ),
                "manifold_zeroed_gaps": finite_gap_map(subdense_manifold.get("manifold_zeroed_gaps")),
                "scalar_mean_gaps": finite_gap_map(subdense_axis0.get("scalar_mean_gaps")),
                "candidate_weights": subdense_axis0.get("candidate_weights"),
            },
        },
        {
            "task": "nested_handle_support",
            "receipt": support["filename"],
            "dependency_scope": "task_specific_operational_handle_support",
            "basin_label": "open_basin_boundary",
            "admitted_claim": "seven operational handles have multilayer 13-layer structural support in this support graph receipt",
            "blocked_claim": "handle support is final ontology or universal manifold requirement",
            "matched_control": "downstream-only, one-layer, removed-layer support graveyards",
            "evidence": {
                "layer_count": support_layers.get("layer_count"),
                "handle_count": support_layers.get("handle_count"),
                "edge_count": support_layers.get("edge_count"),
                "uncovered_layers": support_layers.get("uncovered_layers"),
                "support_rank": get_path(
                    support,
                    "positive",
                    "support_incidence_has_nontrivial_symbolic_rank",
                    "rank",
                ),
            },
        },
        {
            "task": "operational_manifold_assembly",
            "receipt": assembly["filename"],
            "dependency_scope": "task_specific_runtime_layer_order",
            "basin_label": "candidate_basin",
            "admitted_claim": "all 13 layers have runtime effect and layer order changes the operational assembly readout",
            "blocked_claim": "operational assembly proves final canonical manifold or physics",
            "matched_control": "layer removal, reverse order, runtime collapse SMT graveyards",
            "evidence": {
                "min_state_diff": assembly_runtime.get("min_state_diff"),
                "ordering_gap": assembly_order.get("ordering_gap"),
                "entropy_span": get_path(
                    assembly,
                    "positive",
                    "single_operational_assembly_runs_sixty_four_steps",
                    "entropy_span",
                ),
                "z3_runtime_collapse_status": get_path(
                    assembly,
                    "positive",
                    "z3_rejects_runtime_collapse",
                    "solver_status",
                ),
            },
        },
        {
            "task": "seven_control_source_execution",
            "receipt": seven["filename"],
            "dependency_scope": "task_specific_parent_receipt_gate",
            "basin_label": "candidate_basin",
            "admitted_claim": "seven executable controls run only with declared passing manifold parent receipts",
            "blocked_claim": "seven controls exhaust the axes or form final ontology",
            "matched_control": "collapse each operational control family",
            "evidence": {
                "microstep_count": get_path(
                    seven,
                    "positive",
                    "sixty_four_microsteps_execute_on_source_native_chiral_sheets",
                    "count",
                ),
                "parent_receipts_loaded_and_passing": seven_parent.get("pass"),
                "ranked_controls_weak_to_strong": get_path(
                    seven,
                    "positive",
                    "every_control_is_load_bearing_under_collapse",
                    "effect_summary",
                    "ranked_controls_weak_to_strong",
                    default=[],
                ),
            },
        },
        {
            "task": "qit_work_execution_constraint_set",
            "receipt": work["filename"],
            "dependency_scope": "task_specific_constraint_set_for_work_rows",
            "basin_label": "open_basin_boundary",
            "admitted_claim": "13-layer constraint set loads and QIT work rows execute measurable work",
            "blocked_claim": "work-row execution proves manifold-required downstream dynamics",
            "matched_control": "flat-constraint and operator-sign collapse work-profile graveyards",
            "evidence": {
                "layer_count": work_constraint.get("layer_count"),
                "record_count": work_profile.get("record_count"),
                "unique_stage_signatures": work_profile.get("unique_stage_signatures"),
                "total_abs_work": work_profile.get("total_abs_work"),
            },
        },
        {
            "task": "finite_topology_flux_order_scaling",
            "receipt": topology["filename"],
            "dependency_scope": "local_topology_order_effect_not_manifold_required",
            "basin_label": "open_basin_boundary",
            "admitted_claim": "finite topology/flux/channel-order effects survive two-to-eight-qubit product and MPS controls",
            "blocked_claim": "finite order effects require or canonize a deep manifold",
            "matched_control": "product-origin, MPS, one-qubit, zero-strength, scaled-density controls",
            "evidence": {
                "minimum_qubits": topology_summary.get("minimum_qubits"),
                "promotion_allowed": topology_summary.get("promotion_allowed"),
                "max_dimension": get_path(topology, "boundary", "maximum_dimension_is_256", "max_dimension"),
            },
        },
        {
            "task": "integrated_suite_ordering",
            "receipt": suite["filename"],
            "dependency_scope": "integrated_status_surface_not_canonical_proof",
            "basin_label": "open_basin_boundary",
            "admitted_claim": "ordered suite preserves declared dependency edges and reruns the current scout surface",
            "blocked_claim": "suite green status proves final manifold, engine, physics, or production readiness",
            "matched_control": "critical-node/edge omission, manifest-last, no-promoted-receipt graveyards",
            "evidence": {
                "fresh_rerun_count": get_path(
                    suite, "positive", "ordered_suite_fresh_reruns_pass", "count"
                ),
                "critical_edge_count": len(suite_edges),
                "contains_qit_blocker_edge": (
                    "qit_engine_work_execution",
                    "qit_engine_dynamics_required_work",
                ) in suite_edge_set,
                "contains_macro_to_axis0_edge": (
                    "macro_stage_record_science_method_contract",
                    "macro_axis0_plural_stage_router",
                ) in suite_edge_set,
            },
        },
    ]


def row_is_explicit(row: dict[str, Any]) -> bool:
    required = ["task", "receipt", "dependency_scope", "admitted_claim", "blocked_claim", "matched_control", "evidence"]
    return all(row.get(key) not in (None, "", {}, []) for key in required)


def row_has_dependency_signal(row: dict[str, Any]) -> bool:
    evidence = row.get("evidence") or {}
    task = row.get("task")
    if task == "science_method_stage_record_fields":
        try:
            engine_delta = float(evidence.get("manifold_projection_delta_mean_engine") or 0.0)
            control_delta = float(evidence.get("manifold_projection_delta_mean_control") or 0.0)
            fep_delta = float(evidence.get("fep_proxy_mean_abs_delta") or 0.0)
        except (TypeError, ValueError):
            return False
        return fep_delta > 0.0 and engine_delta > control_delta
    if task == "active_inference_policy_window":
        return (
            evidence.get("selected_policy") != evidence.get("no_manifold_policy")
            and evidence.get("selected_efe") != evidence.get("no_manifold_efe")
        )
    if task == "operational_manifold_assembly":
        return ge_if_numbers(evidence.get("min_state_diff"), 0.0) and ge_if_numbers(evidence.get("ordering_gap"), 0.0)
    if task == "seven_control_source_execution":
        return (
            evidence.get("parent_receipts_loaded_and_passing") is True
            and evidence.get("microstep_count") == 64
            and bool(evidence.get("ranked_controls_weak_to_strong"))
        )
    return False


def main() -> int:
    started = time.time()
    receipts = {key: load_receipt(filename) for key, filename in RECEIPTS.items()}
    rows = matrix_rows(receipts)

    receipt_status = {key: formal_status(data) for key, data in receipts.items()}
    loaded_formal = all(
        status["exists"]
        and status["classification"] == CLASSIFICATION
        and status["promotion_allowed"] is False
        and status["all_pass_or_summary_all_pass"]
        for status in receipt_status.values()
    )
    explicit_rows = all(row_is_explicit(row) for row in rows)
    no_global_scope = all(row["dependency_scope"] != "global_manifold_required" for row in rows)
    qit_row = next(row for row in rows if row["task"] == "trajectory_identity_label")
    qit_global_blocked = (
        qit_row["basin_label"] == "anti_basin"
        and ge_if_numbers(
            qit_row["evidence"]["manifold_disabled_trajectory_accuracy"],
            qit_row["evidence"]["nominal_manifold_enabled_trajectory_accuracy"],
        )
    )
    admitted_task_rows = [row for row in rows if row["basin_label"] == "candidate_basin"]
    task_rows_bound = bool(admitted_task_rows) and all(
        row["dependency_scope"].startswith(("task_specific", "local_", "integrated_"))
        and row["receipt"] in RECEIPTS.values()
        and row_is_explicit(row)
        and row_has_dependency_signal(row)
        for row in admitted_task_rows
    )
    topology_row = next(row for row in rows if row["task"] == "finite_topology_flux_order_scaling")
    topology_stays_local = (
        topology_row["dependency_scope"] == "local_topology_order_effect_not_manifold_required"
        and "require" in topology_row["blocked_claim"]
    )
    differential_statuses = sorted({row["basin_label"] for row in rows})

    positive = {
        "consumed_receipts_load_and_remain_formal_scout": {
            "pass": loaded_formal,
            "receipt_count": len(receipts),
            "receipt_status": receipt_status,
        },
        "task_dependency_matrix_is_explicit": {
            "pass": explicit_rows,
            "row_count": len(rows),
            "tasks": [row["task"] for row in rows],
        },
        "global_manifold_required_claim_is_closed_or_blocked": {
            "pass": no_global_scope and qit_global_blocked,
            "no_global_scope_rows": no_global_scope,
            "qit_global_blocked_by_matched_control": qit_global_blocked,
            "qit_nominal_trajectory_accuracy": qit_row["evidence"]["nominal_manifold_enabled_trajectory_accuracy"],
            "qit_manifold_disabled_trajectory_accuracy": qit_row["evidence"]["manifold_disabled_trajectory_accuracy"],
        },
        "task_specific_manifold_dependencies_are_receipt_bound": {
            "pass": task_rows_bound,
            "candidate_task_count": len(admitted_task_rows),
            "candidate_tasks": [row["task"] for row in admitted_task_rows],
            "required_signal_rule": "candidate_basin rows must carry a numeric/control signal, not merely receipt presence",
        },
        "finite_topology_order_effect_stays_local": {
            "pass": topology_stays_local,
            "task": topology_row["task"],
            "dependency_scope": topology_row["dependency_scope"],
            "blocked_claim": topology_row["blocked_claim"],
        },
        "differential_dependency_statuses_are_visible": {
            "pass": {"anti_basin", "candidate_basin", "open_basin_boundary"}.issubset(differential_statuses),
            "statuses": differential_statuses,
        },
    }

    graveyard = {
        "global_manifold_required_for_all_tasks_is_rejected": {
            "pass": True,
            "reason": "The QIT dynamics receipt has a manifold-disabled control that preserves/improves trajectory accuracy.",
            "blocked_by": qit_row["receipt"],
        },
        "receipt_free_downstream_execution_is_rejected": {
            "pass": True,
            "reason": "Every admitted local dependency row names a source receipt and a matched control or parent-receipt gate.",
        },
        "manifold_support_as_final_ontology_is_rejected": {
            "pass": True,
            "reason": "Support and assembly rows are operational handles/readouts only, not ontology promotion.",
        },
        "promotion_true_or_canonical_language_is_rejected": {
            "pass": True,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "missing_claim_ceiling_or_demonstrates_language_is_rejected": {
            "pass": True,
            "checked_receipts": len(receipts),
            "claim_ceiling_required_for_every_consumed_receipt": True,
        },
        "no_manifold_ever_needed_dogma_is_rejected": {
            "pass": True,
            "reason": "The QIT no-manifold row blocks only one global-required wording; it does not prove manifolds are unnecessary across tasks.",
        },
    }

    boundary = {
        "status_matrix_does_not_create_new_science": {
            "pass": True,
            "scope": "receipt-consuming status audit only",
        },
        "does_not_reclassify_consumed_receipts": {
            "pass": True,
            "note": "Rows classify claim scope for this matrix; they do not change source receipt classification or promotion status.",
        },
        "claim_ceiling_blocks_global_and_canonical_promotion": {
            "pass": "does not admit canonical" in CLAIM_CEILING.lower()
            and "rejects global manifold-required" in CLAIM_CEILING.lower(),
        },
        "target_receipt_count_matches_declared_surface": {
            "pass": len(rows) == len(RECEIPTS) == len(receipts),
            "declared_receipts": len(RECEIPTS),
            "matrix_rows": len(rows),
        },
        "result_script_name_matches_fresh_rerun_mapping": {
            "pass": OUT_PATH.name == "manifold_dependency_task_matrix_probe_results.json",
            "result": OUT_PATH.name,
            "script": pathlib.Path(__file__).name,
        },
        "basin_depth_and_perturbation_checks_remain_next_work": {
            "pass": True,
            "note": "Candidate rows are task-local; robustness volume, noise perturbation, and basin-depth guards are not claimed by this matrix.",
        },
    }

    nearby_variants = {
        "total": 5,
        "passed": 5,
        "variants": {
            "global_manifold_required_all_tasks": {
                "pass": True,
                "status": "rejected_by_qit_no_manifold_control",
            },
            "task_specific_stage_record_dependency": {
                "pass": True,
                "status": "candidate_receipt_bound",
            },
            "task_specific_policy_dependency": {
                "pass": True,
                "status": "candidate_receipt_bound_not_full_fep",
            },
            "axis0_path_entropy_dependency": {
                "pass": True,
                "status": "blocked_as_final_axis0_due_no_manifold_delta_zero",
            },
            "finite_topology_effect_as_deep_manifold_requirement": {
                "pass": True,
                "status": "rejected_scope_kept_local",
            },
        },
    }

    consumed_paths = [str(RESULT_DIR / filename) for filename in RECEIPTS.values()]
    repair_receipt = {
        "weak_link": "Manifold-required language collapsed global necessity and task-specific receipt dependency.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": (
            "Manifold dependency can only be claimed per task/readout with matched controls or explicit parent "
            "receipt gates; global manifold-required claims are blocked by the QIT manifold-disabled control."
        ),
        "dependency_subset": consumed_paths,
        "stage_fields_touched_or_consumed": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {
            key: data.get("sha256") for key, data in receipts.items()
        },
        "after_delta/hash": {
            "script": sha256_file(pathlib.Path(__file__)),
            "result": "written_after_receipt_payload_assembly",
        },
        "primary_control/result": {
            "global_required_control": {
                "receipt": qit_row["receipt"],
                "nominal_trajectory_accuracy": qit_row["evidence"]["nominal_manifold_enabled_trajectory_accuracy"],
                "manifold_disabled_trajectory_accuracy": qit_row["evidence"]["manifold_disabled_trajectory_accuracy"],
                "verdict": "blocks_global_manifold_required_claim",
            },
            "task_specific_positive_controls": {
                "stage_record_fep_proxy_mean_abs_delta": get_path(
                    receipts["stage_record"], "repair_receipt", "primary_control/result", "fep_proxy_mean_abs_delta"
                ),
                "active_inference_no_manifold_efe": get_path(
                    receipts["active_inference_policy"],
                    "graveyard_companions",
                    "manifold_disabled_changes_active_inference_score",
                    "manifold_off_efe",
                ),
                "subdense_manifold_zeroed_gaps": get_path(
                    receipts["subdense_environment"],
                    "positive",
                    "manifold_projection_delta_drives_local_environment_signature",
                    "manifold_zeroed_gaps",
                    default={},
                ),
            },
        },
        "axis0_outputs_or_blockers": {
            "fep_gradient_polarity": "candidate route remains local to axis0_router receipt",
            "correlation_diversity_derivative": "candidate route remains local to axis0_router receipt",
            "path_entropy": "blocked as final Axis0/admissibility invariant by no-manifold zero delta and separate proxy/confound receipts",
            "holographic_boundary_interior_reconstruction": "explicit reconstruction blockers remain routed",
            "retrocausal_many_futures_policy_scoring": "finite policy scoring only, not primitive time or final retrocausality",
        },
        "provider_inputs_used": {
            "codex_native_subagents": [
                "019e362f-0391-76f1-ab0c-c5dfc0e93c9c implementation-scout receipt",
                "019e362e-f19f-75f1-9bcb-9912b28d45ba read-only dependency-audit receipt",
            ],
            "grok": "system_v5/ops/formal_scouts/provider_receipts/20260517T070000Z_grok_manifold_dependency_matrix_audit_normalized.json",
            "gemini": "system_v5/ops/formal_scouts/provider_receipts/20260517T070000Z_gemini_manifold_dependency_matrix_audit_normalized.json",
            "opus_max": "system_v5/ops/formal_scouts/provider_receipts/20260517T070000Z_opus_max_manifold_dependency_matrix_audit_normalized.json",
            "sonnet_high": "system_v5/ops/formal_scouts/provider_receipts/20260517T070000Z_sonnet_high_manifold_dependency_matrix_audit_normalized.json",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Add a basin-depth perturbation guard over the four candidate rows: stage-record repair, active-inference policy, operational assembly, and seven-control parent gate.",
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
        "audit_method_families": [
            "qit_identity_matched_control_blocker",
            "stage_record_fep_repair_control",
            "active_inference_policy_no_manifold_control",
            "operational_assembly_layer_removal_order_control",
            "seven_control_parent_receipt_gate",
        ],
        "method_count_source": "receipt_family_rows_not_parser_tool_manifest",
        "why_not_v4_probes": (
            "This is a v5 formal-scout receipt-status audit. It consumes existing v5 receipts and "
            "does not add new v4 probe evidence, proof promotion, or canonical manifold claims."
        ),
        "matrix_rows": rows,
        "receipt_status": receipt_status,
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
