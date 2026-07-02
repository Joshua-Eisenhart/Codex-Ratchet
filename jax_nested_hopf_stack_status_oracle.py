#!/usr/bin/env python3
"""Aggregate status oracle for current JAX nested-Hopf/G-structure receipts.

This is a lightweight controller-side receipt checker. It does not run Julia,
does not import PyTorch, and does not promote any layer. It answers: which JAX
diagnostic receipts are present, green, boundary-fenced, and externally checked?
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OUT = Path("jax_nested_hopf_stack_status_oracle_results.json")

REQUIRED = {
    "foliation_invariant_mirror": Path("jax_nested_hopf_foliation_invariant_mirror_results.json"),
    "leaf_area_radial_dirac_mirror": Path("jax_nested_leaf_area_radial_dirac_mirror_results.json"),
    "gstructure_16_placement": Path("jax_gstructure_16_placement_spin3_audit_results.json"),
    "gstructure_16_selector": Path("jax_gstructure_16_branch_prune_selector_audit_results.json"),
    "gstructure_16_external_oracle": Path("jax_gstructure_16_external_negative_oracle_results.json"),
    "weyl_terrain_16_lindblad": Path("jax_weyl_terrain_16_placements_lindblad_audit_results.json"),
    "julia_reference_runner": Path("jax_julia_reference_geometric_constraint_layer_runner_results.json"),
}

OPTIONAL_IN_PROGRESS = {}

COMPOSITION_ROWS = {
    "s3_su2_spin3_carrier": Path("jax_s3_su2_spin3_carrier_mirror_results.json"),
    "gstructure_chirality_bakeoff": Path("jax_gstructure_chirality_reduction_bakeoff_results.json"),
    "dirac_gamma5_branch_prune": Path("jax_dirac_gamma5_chirality_branch_prune_audit_results.json"),
}

NESTING_ORDER_GATE = Path("jax_nested_hopf_nesting_order_gate_results.json")
COVERAGE_GATE = Path("jax_independent_layer_geometry_coverage_gate_results.json")

NESTING_ORDER_BLOCKED_REASON = (
    "Nesting/order/coupling/basin work requires the independent JAX layer/geometry "
    "coverage gate to close first. Coverage-gate closure is diagnostic/fenced "
    "evidence only; it is not layer admission or stacking readiness."
)

BLOCKED_REASON_RECEIPTS = {
    "flux_impedance_falsifier": Path(
        "system_v5/ops/wizard_admissions/"
        "blocked_flux_impedance_dependency_preflight_20260602T080320Z.json"
    ),
}

DOWNSTREAM_BLOCKED_ROWS = {
    "bottom_up_nested": {
        "path": Path("jax_nested_hopf_bottom_up_branch_prune_audit_results.json"),
        "blocked_status": "blocked_until_all_layers_and_geometries_simed",
        "blocked_reason": NESTING_ORDER_BLOCKED_REASON,
        "required_dependency_closure": ["all independent layer receipts", "all independent geometry receipts", "coverage audit for missing/red geometries"],
    },
    "bottom_up_external_oracle": {
        "path": Path("jax_nested_hopf_bottom_up_external_oracle_results.json"),
        "blocked_status": "blocked_until_all_layers_and_geometries_simed",
        "blocked_reason": NESTING_ORDER_BLOCKED_REASON,
        "required_dependency_closure": ["all independent layer receipts", "all independent geometry receipts", "bottom-up nesting target becomes active"],
    },
    "pairwise_leaf_coupling": {
        "path": Path("jax_nested_hopf_pairwise_leaf_coupling_audit_results.json"),
        "blocked_status": "blocked_until_all_layers_and_geometries_simed",
        "blocked_reason": NESTING_ORDER_BLOCKED_REASON,
        "required_dependency_closure": ["all independent leaf/geometry receipts", "pairwise coupling declared as a post-geometry nesting check"],
    },
    "bottom_up_robustness_sweep": {
        "path": Path("jax_nested_hopf_bottom_up_robustness_sweep_results.json"),
        "blocked_status": "blocked_until_all_layers_and_geometries_simed",
        "blocked_reason": NESTING_ORDER_BLOCKED_REASON,
        "required_dependency_closure": ["bottom-up nesting active", "base bottom-up nesting receipt admitted for robustness sweep"],
    },
    "weyl_dirac_radial_coupling": {
        "path": Path("jax_weyl_dirac_coupling_radial_mirror_results.json"),
        "blocked_status": "blocked_until_all_layers_and_geometries_simed",
        "blocked_reason": NESTING_ORDER_BLOCKED_REASON,
        "required_dependency_closure": ["independent Weyl spinor geometry receipt", "independent nested Hopf torus receipt", "declared coupling/nesting stage"],
    },
    "multishell_lindblad_cascade": {
        "path": Path("jax_multishell_lindblad_cascade_mirror_results.json"),
        "blocked_status": "blocked_until_all_layers_and_geometries_simed",
        "blocked_reason": NESTING_ORDER_BLOCKED_REASON,
        "required_dependency_closure": ["all shell geometries independently simed", "cascade nesting stage opened"],
    },
    "multishell_coexistence": {
        "path": Path("jax_multishell_coexistence_mirror_results.json"),
        "blocked_status": "blocked_until_all_layers_and_geometries_simed",
        "blocked_reason": NESTING_ORDER_BLOCKED_REASON,
        "required_dependency_closure": ["all shell geometries independently simed", "coexistence/nesting stage opened"],
    },
    "emergent_basin_recurrence_prune": {
        "path": Path("jax_emergent_basin_recurrence_prune_mirror_results.json"),
        "blocked_status": "blocked_until_all_layers_and_geometries_simed",
        "blocked_reason": NESTING_ORDER_BLOCKED_REASON,
        "required_dependency_closure": ["all layer/geometries independently simed", "nesting-order map fixed", "then basin/subbasin readout"],
    },
    "noncommutative_finitude_ratchet_basin_hierarchy": {
        "path": Path("jax_noncommutative_finitude_ratchet_basin_hierarchy_results.json"),
        "blocked_status": "blocked_until_all_layers_and_geometries_simed",
        "blocked_reason": NESTING_ORDER_BLOCKED_REASON,
        "required_dependency_closure": ["all layer/geometries independently simed", "nesting-order stage opened", "then ratchet order search"],
    },
    "noncommutative_finitude_ratchet_deepening_falsifier": {
        "path": Path("jax_noncommutative_finitude_ratchet_deepening_falsifier_results.json"),
        "blocked_status": "blocked_until_ratchet_hierarchy_exists",
        "blocked_reason": NESTING_ORDER_BLOCKED_REASON,
        "required_dependency_closure": ["ratchet basin hierarchy diagnostic", "tested fourth-level refinement controls"],
    },
    "flux_impedance_falsifier": {
        "path": Path("jax_flux_impedance_falsifier_results.json"),
        "blocked_status": "blocked_by_dependency",
        "blocked_reason": (
            "Flux is not an admissible repair/run target until every layer and geometry is "
            "independently simed, then the nesting order is established: Weyl spinors nested "
            "on nested Hopf tori, those tori nested through the ordered geometric layers, and "
            "the geometries nested inside the Weyl-spinor carrier."
        ),
        "required_dependency_closure": [
            "all independent layer receipts",
            "all independent geometry receipts",
            "finite F01/N01 carrier/root receipts",
            "Weyl L/R spinors on nested Hopf tori",
            "nested Hopf tori ordered through the layer stack",
            "geometries nested into the Weyl-spinor carrier",
            "order-erased and label-erased negatives over the nested stack",
        ],
    }
}


def load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def pass_field(d: dict[str, Any]) -> bool:
    if "AUDIT_PASS" in d:
        return bool(d["AUDIT_PASS"])
    if "all_pass" in d:
        return bool(d["all_pass"])
    return False


def boundary_ok(d: dict[str, Any]) -> bool:
    return (
        d.get("promotion_allowed") is False
        and d.get("ran_julia") is not True
        and d.get("ran_pytorch") is not True
    )


def check_special(name: str, d: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []

    def need(label: str, ok: bool) -> None:
        if not ok:
            failures.append(label)

    if name == "gstructure_16_selector":
        runs = d.get("runs", {})
        need("A_all_16", runs.get("A", {}).get("populated") == list(range(1, 17)))
        need("B_allowed_1_8", runs.get("B", {}).get("populated") == list(range(1, 9)))
        need("C_equals_A", runs.get("C", {}).get("populated") == runs.get("A", {}).get("populated"))
        need("inverted_forbidden_9_16", runs.get("inverted", {}).get("populated") == list(range(9, 17)))
    elif name == "bottom_up_nested":
        runs = d.get("nested_runs", {})
        need("genuine_all_16", runs.get("genuine", {}).get("populated_placements") == list(range(1, 17)))
        need("commuting_collapses", runs.get("commuting_control", {}).get("populated_placements") == [1])
        need("expansive_prunes", runs.get("expansive_prune_control", {}).get("pruned", 0) > 0)
        need("ratchet_off_differs", runs.get("ratchet_off_control", {}).get("leaf_histogram") != runs.get("genuine", {}).get("leaf_histogram"))
    elif name == "gstructure_16_external_oracle":
        need("placement_accepts_original", d.get("placement_external_accepts_original") is True)
        need("placement_rejects_corruption", d.get("placement_external_rejects_corruption") is True)
        need("selector_accepts_original", d.get("selector_external_accepts_original") is True)
        need("selector_rejects_corruption", d.get("selector_external_rejects_corruption") is True)
    elif name == "bottom_up_external_oracle":
        need("reject_basin", d.get("reject_corrupt_basin") is True)
        need("reject_order", d.get("reject_corrupt_order") is True)
        need("reject_boundary", d.get("reject_corrupt_boundary") is True)
    elif name == "pairwise_leaf_coupling":
        checks = d.get("checks", {})
        for key in (
            "g0_joint_equals_product",
            "g_positive_shifts_state",
            "g_positive_turns_on_correlations",
            "identity_coupler_sham_inert",
            "identity_coupler_sham_lower_than_exchange",
            "gamma_theta_is_sigma_x_dirac_gamma",
            "identity_is_not_dirac_gamma",
        ):
            need(key, checks.get(key) is True)
    elif name == "foliation_invariant_mirror":
        checks = d.get("checks", {})
        for key in ("tangent_rank", "leaf_area", "nesting_disjointness", "hopf_linking", "z3_disjointness", "foliation_coverage"):
            need(key, checks.get(key) is True)
    elif name == "leaf_area_radial_dirac_mirror":
        checks = d.get("checks", {})
        for key in ("leaf_area_ratchet", "radial_dirac_coupling", "entropy_area_proxy"):
            need(key, checks.get(key) is True)
    elif name == "bottom_up_robustness_sweep":
        checks = d.get("checks", {})
        for key in (
            "at_least_five_deterministic_cases",
            "all_cases_pass",
            "rejected_lane_rejected",
            "ran_julia_false",
            "ran_pytorch_false",
        ):
            need(key, checks.get(key) is True)
    elif name == "s3_su2_spin3_carrier":
        checks = d.get("checks", {})
        for key in ("s3_su2_so3_carrier", "axis_angle_double_cover", "so3_frame_reduction_pin_control", "weyl_chirality_sign_control"):
            need(key, checks.get(key) is True)
    elif name == "weyl_dirac_radial_coupling":
        checks = d.get("checks", {})
        for key in ("carrier", "chirality", "radial_chain", "two_leaf_spectral_controls", "unitarity_density"):
            need(key, checks.get(key) is True)
    elif name == "gstructure_chirality_bakeoff":
        checks = d.get("checks", {})
        for key in (
            "chk_spin3_su2",
            "chk_pin3_reflection_flip",
            "chk_sl2c_weyl_split",
            "chk_gamma_anchor",
            "chk_negatives",
            "chk_selected_finite_carrier",
            "chk_twistor_diagnostic",
            "chk_spin8_triality_diagnostic",
        ):
            need(key, checks.get(key) is True)
        need("selected_only_spin3_su2", d.get("selected_finite_chirality_carriers") == ["Spin3_SU2"])
    elif name == "dirac_gamma5_branch_prune":
        checks = d.get("checks", {})
        for key in (
            "gamma5_genuine",
            "A_reaches_forbidden",
            "B_kills_all_forbidden",
            "B_preserves_allowed",
            "control_C_equals_A",
            "B_pruned_some_A_none",
            "rate_matched_random_KEEPS_forbidden",
            "inverted_sign_flips_to_forbidden",
            "norm_drift_small",
        ):
            need(key, checks.get(key) is True)
        runs = d.get("runs", {})
        need("A_all_four", runs.get("A", {}).get("populated") == [1, 2, 3, 4])
        need("B_gamma5_allowed_only", runs.get("B_gamma5", {}).get("populated") == [1, 2])
        need("C_control_equals_A", runs.get("C_control", {}).get("populated") == [1, 2, 3, 4])
        need("D_inverted_forbidden_only", runs.get("D_inverted_sign", {}).get("populated") == [3, 4])
        need("random_control_keeps_forbidden", runs.get("rate_matched_random_populated") == [1, 2, 3, 4])
    elif name == "noncommutative_finitude_ratchet_basin_hierarchy":
        checks = d.get("checks", {})
        for key in (
            "A_topology_basins_all_4",
            "A_placement_subbasins_all_16",
            "B_prune_fires",
            "B_preserves_topology_basins",
            "B_preserves_placement_subbasins",
            "B_order_subsubbasins_refine_subbasins",
            "C_noop_equals_A",
            "E_commuting_product_collapses_topology",
            "E_commuting_product_collapses_subbasins",
            "noncommuting_static_witness",
            "commuting_static_negative",
            "noncommuting_dynamic_order_gap",
            "same_word_dynamic_control_zero",
            "reversed_order_changes_state",
            "bookkeeping",
            "f01_retraction",
            "finite_bloch_ball",
        ):
            need(key, checks.get(key) is True)
        runs = d.get("runs", {})
        need("A_all_hierarchy", runs.get("A", {}).get("populated_topology_basins") == [1, 2, 3, 4]
             and runs.get("A", {}).get("populated_placement_subbasins") == list(range(1, 17))
             and runs.get("A", {}).get("populated_order_subsubbasin_count") == 64)
        need("B_pruned_hierarchy", runs.get("B", {}).get("pruned", 0) > 0
             and runs.get("B", {}).get("populated_topology_basins") == [1, 2, 3, 4]
             and runs.get("B", {}).get("populated_placement_subbasins") == list(range(1, 17))
             and runs.get("B", {}).get("populated_order_subsubbasin_count") >= 48)
        need("E_product_single_cell", runs.get("E", {}).get("populated_topology_basins") == [1]
             and runs.get("E", {}).get("populated_placement_subbasins") == [1]
             and runs.get("E", {}).get("populated_order_subsubbasin_count") == 1)
    elif name == "noncommutative_finitude_ratchet_deepening_falsifier":
        checks = d.get("checks", {})
        for key in (
            "prior_subsub_hierarchy_present_A",
            "prior_subsub_hierarchy_present_B",
            "product_negative_collapses_prior_hierarchy",
            "leaf_radial_candidates_do_not_overrefine",
            "recurrence_candidate_rejected_as_noisy_or_control_leaky",
            "prune_still_fires",
            "f01_retraction",
            "finite_bloch_ball",
        ):
            need(key, checks.get(key) is True)
        rows = d.get("rows", {})
        need("A_B_64_E_1", rows.get("A", {}).get("subsub_cells") == 64
             and rows.get("B", {}).get("subsub_cells") == 64
             and rows.get("E", {}).get("subsub_cells") == 1)
    elif name == "nesting_order_gate":
        checks = d.get("checks", {})
        for key in (
            "coverage_receipt_closed",
            "pairwise_leaf_coupling_passes",
            "four_topologies",
            "eight_terrain_names",
            "sixteen_weyl_placements",
            "dependency_order_gate",
            "noncommuting_order_dynamic_gate",
            "leaf_area_order_ratchet_gate",
            "flux_axis_physics_still_blocked",
        ):
            need(key, checks.get(key) is True)
        need("nesting_order_gate_closed", d.get("nesting_order_gate_closed") is True)
    return not failures, failures


def summarize(name: str, path: Path, required: bool) -> dict[str, Any]:
    d = load(path)
    if d is None:
        return {
            "name": name,
            "path": str(path),
            "required": required,
            "present": False,
            "pass": False if required else None,
            "boundary_ok": False if required else None,
            "special_ok": False if required else None,
            "failures": ["missing"] if required else ["optional_missing"],
        }
    special_ok, special_failures = check_special(name, d)
    row_pass = pass_field(d)
    row_boundary = boundary_ok(d)
    failures: list[str] = []
    if not row_pass:
        failures.append("pass_field_false")
    if not row_boundary:
        failures.append("boundary_not_fenced")
    if not special_ok:
        failures.extend(special_failures)
    return {
        "name": name,
        "path": str(path),
        "required": required,
        "present": True,
        "pass": row_pass,
        "boundary_ok": row_boundary,
        "special_ok": special_ok,
        "failures": failures,
        "classification": d.get("classification"),
        "promotion_allowed": d.get("promotion_allowed"),
        "ran_julia": d.get("ran_julia"),
        "ran_pytorch": d.get("ran_pytorch"),
    }


def summarize_blocked(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    path = spec["path"]
    d = load(path)
    blocked_receipt_path = BLOCKED_REASON_RECEIPTS.get(name)
    blocked_receipt = load(blocked_receipt_path) if blocked_receipt_path is not None else None
    return {
        "name": name,
        "path": str(path),
        "present": d is not None,
        "blocked_status": spec["blocked_status"],
        "blocked_reason": spec["blocked_reason"],
        "required_dependency_closure": spec["required_dependency_closure"],
        "blocked_reason_receipt_path": str(blocked_receipt_path) if blocked_receipt_path is not None else None,
        "blocked_reason_receipt_present": blocked_receipt is not None,
        "blocked_reason_receipt_valid": (
            blocked_receipt is not None
            and blocked_receipt.get("kind") == "blocked_reason"
            and bool(blocked_receipt.get("reason"))
            and bool(blocked_receipt.get("next_admissible_step"))
        ),
        "blocked_reason_receipt_created_at": blocked_receipt.get("created_at") if blocked_receipt is not None else None,
        "current_receipt_pass": pass_field(d) if d is not None else None,
        "boundary_ok": boundary_ok(d) if d is not None else None,
        "classification": d.get("classification") if d is not None else None,
        "promotion_allowed": d.get("promotion_allowed") if d is not None else None,
        "ran_julia": d.get("ran_julia") if d is not None else None,
        "ran_pytorch": d.get("ran_pytorch") if d is not None else None,
    }


def main() -> int:
    rows = [summarize(name, path, True) for name, path in REQUIRED.items()]
    optional = [summarize(name, path, False) for name, path in OPTIONAL_IN_PROGRESS.items()]
    composition = [summarize(name, path, False) for name, path in COMPOSITION_ROWS.items()]
    nesting_order_gate = summarize("nesting_order_gate", NESTING_ORDER_GATE, False)
    coverage_gate = load(COVERAGE_GATE) or {}
    downstream_blocked = [summarize_blocked(name, spec) for name, spec in DOWNSTREAM_BLOCKED_ROWS.items()]
    julia_reference = load(REQUIRED["julia_reference_runner"]) or {}
    missing_independent = julia_reference.get("missing_independent_jax_rows", julia_reference.get("missing_jax_rows", []))
    red_independent = julia_reference.get("red_independent_reference_rows", [])
    unresolved_red_independent = julia_reference.get("red_independent_reference_rows_unresolved", red_independent)
    future_phase_refs = julia_reference.get("future_phase_reference_layers", [])
    required_ok = all(r["present"] and r["pass"] and r["boundary_ok"] and r["special_ok"] for r in rows)
    optional_present_ok = all((not r["present"]) or (r["pass"] and r["boundary_ok"] and r["special_ok"]) for r in optional)
    coverage_gate_closed = coverage_gate.get("coverage_closed") is True
    independent_layer_geometry_coverage_closed = (
        required_ok
        and not missing_independent
        and not unresolved_red_independent
        and coverage_gate_closed
    )
    nesting_order_gate_closed = (
        independent_layer_geometry_coverage_closed
        and nesting_order_gate["present"]
        and nesting_order_gate["pass"]
        and nesting_order_gate["boundary_ok"]
        and nesting_order_gate["special_ok"]
    )
    bottom_up_green = summarize("bottom_up_nested", DOWNSTREAM_BLOCKED_ROWS["bottom_up_nested"]["path"], False)
    bottom_up_external_green = summarize("bottom_up_external_oracle", DOWNSTREAM_BLOCKED_ROWS["bottom_up_external_oracle"]["path"], False)
    bottom_up_robustness_green = summarize("bottom_up_robustness_sweep", DOWNSTREAM_BLOCKED_ROWS["bottom_up_robustness_sweep"]["path"], False)
    ratchet_hierarchy_green = summarize(
        "noncommutative_finitude_ratchet_basin_hierarchy",
        DOWNSTREAM_BLOCKED_ROWS["noncommutative_finitude_ratchet_basin_hierarchy"]["path"],
        False,
    )
    ratchet_deepening_green = summarize(
        "noncommutative_finitude_ratchet_deepening_falsifier",
        DOWNSTREAM_BLOCKED_ROWS["noncommutative_finitude_ratchet_deepening_falsifier"]["path"],
        False,
    )
    post_nesting_rows = [
        bottom_up_green,
        bottom_up_external_green,
        bottom_up_robustness_green,
        ratchet_hierarchy_green,
        ratchet_deepening_green,
    ]
    post_nesting_green = [r for r in post_nesting_rows if r["present"] and r["pass"] and r["boundary_ok"] and r["special_ok"]]
    composition_green = [r for r in composition if r["present"] and r["pass"] and r["boundary_ok"] and r["special_ok"]]
    composition_red = [r for r in composition if r["present"] and not (r["pass"] and r["boundary_ok"] and r["special_ok"])]
    composition_missing = [r for r in composition if not r["present"]]
    receipt = {
        "name": "jax_nested_hopf_stack_status_oracle",
        "classification": "status_oracle",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "claim_ceiling": "Aggregate status only. It does not promote layers, does not claim layer-stacking readiness, does not open flux/Axis0/FEP/physics, and does not select an official G-structure.",
        "active_stage": (
            "post_nesting_order_bounded_ratchet_basin_diagnostics"
            if nesting_order_gate_closed and ratchet_hierarchy_green["present"] and ratchet_hierarchy_green["pass"] and ratchet_hierarchy_green["special_ok"]
            else "nesting_order_search"
            if independent_layer_geometry_coverage_closed
            else "independent_layer_and_geometry_sims"
        ),
        "phase_order": [
            "1_get_every_layer_independently_simed",
            "2_get_every_geometry_independently_simed",
            "3_run_coverage_audit_for_missing_red_or_label_only_geometries",
            "4_only_then_run_nesting_order_search",
            "5_only_after_nesting_order_closure_run_flux_or_axis_readouts",
        ],
        "next_admissible_move": (
            "Post-nesting JAX diagnostics are green. Next admissible move is external/council audit or a blocked-dependency flux preflight artifact; flux/Axis0/FEP/physics remain not opened."
            if nesting_order_gate_closed and ratchet_hierarchy_green["present"] and ratchet_hierarchy_green["pass"] and ratchet_hierarchy_green["special_ok"]
            else "Coverage closed locally; run explicit nesting-order gate before ratchet/basin/flux."
            if independent_layer_geometry_coverage_closed
            else "Repair red independent layer/geometry references and fill any missing independent rows. Do not advance nesting order, basin hierarchy, or flux as the active target yet."
        ),
        "independent_layer_geometry_coverage": {
            "closed": independent_layer_geometry_coverage_closed,
            "coverage_gate_path": str(COVERAGE_GATE),
            "coverage_gate_closed": coverage_gate_closed,
            "coverage_gate_unreadable_count": len(coverage_gate.get("unreadable_individual_receipts", [])),
            "coverage_gate_failed_or_unfenced_count": len(coverage_gate.get("failed_or_unfenced_individual_receipts", [])),
            "missing_independent_jax_rows": missing_independent,
            "red_independent_reference_rows": red_independent,
            "red_independent_reference_rows_unresolved": unresolved_red_independent,
            "red_independent_reference_supersession_receipts": julia_reference.get("red_independent_reference_supersession_receipts", {}),
            "future_phase_reference_layers_blocked": future_phase_refs,
            "nesting_order_allowed": nesting_order_gate_closed,
            "blocked_reason": (
                "Nesting order stays blocked until the diagnostic independent coverage gate closes with readable "
                "JAX rows and unresolved red independent reference rows are zero. This is not layer admission."
            ) if not independent_layer_geometry_coverage_closed else (
                "diagnostic coverage gate closed locally; nesting claims require the separate nesting-order gate "
                "and still do not imply layer admission or stacking readiness"
            ),
        },
        "required_rows": rows,
        "optional_in_progress_rows": optional,
        "composition_rows": composition,
        "nesting_order_gate": nesting_order_gate,
        "post_nesting_diagnostic_rows": post_nesting_rows,
        "downstream_blocked_rows": downstream_blocked,
        "composition_summary": {
            "green": [r["name"] for r in composition_green],
            "diagnostic_green_not_promotion": [r["name"] for r in composition_green],
            "red_or_blocked": [r["name"] for r in composition_red],
            "missing_or_pending": [r["name"] for r in composition_missing],
            "downstream_blocked": [r["name"] for r in downstream_blocked],
            "post_nesting_green": [r["name"] for r in post_nesting_green],
        },
        "required_ok": required_ok,
        "optional_present_ok": optional_present_ok,
        "independent_layer_geometry_coverage_closed": independent_layer_geometry_coverage_closed,
        "nesting_order_gate_closed": nesting_order_gate_closed,
        "nesting_order_allowed": nesting_order_gate_closed,
        "post_nesting_green_count": len(post_nesting_green),
        "flux_allowed": False,
        "axis0_allowed": False,
        "composition_green_count": len(composition_green),
        "composition_red_or_blocked_count": len(composition_red),
        "composition_missing_count": len(composition_missing),
        "downstream_blocked_count": len(downstream_blocked),
        "AUDIT_PASS": required_ok and optional_present_ok,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        "jax_nested_hopf_stack_status "
        f"required={sum(1 for r in rows if r['present'])}/{len(rows)} "
        f"optional_present={sum(1 for r in optional if r['present'])}/{len(optional)} "
        f"composition_green={len(composition_green)} red={len(composition_red)} missing={len(composition_missing)} "
        f"downstream_blocked={len(downstream_blocked)} "
        f"coverage_closed={independent_layer_geometry_coverage_closed} "
        f"nesting_order_gate_closed={nesting_order_gate_closed} "
        f"post_nesting_green={len(post_nesting_green)}/{len(post_nesting_rows)} "
        f"red_refs={red_independent} "
        f"unresolved_red_refs={unresolved_red_independent} "
        f"AUDIT_PASS={required_ok and optional_present_ok}"
    )
    return 0 if required_ok and optional_present_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
