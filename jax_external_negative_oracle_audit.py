#!/usr/bin/env python3
"""External negative-control oracle for the JAX manifold diagnostic suite.

This is deliberately not a promotion gate. It audits the existing 19-row JAX
receipt from outside the row-local `pass` flags: every row must satisfy an
external threshold rule, and a row-specific corrupted control must be rejected.

Purpose: answer the council self-grading concern without touching Julia or the
retired tensor lane.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp


IN_PATH = Path("jax_manifold_layer_independent_suite_results.json")
OUT_PATH = Path("jax_external_negative_oracle_audit_results.json")
EPS = 1.0e-9


def finite(x) -> bool:
    return bool(jnp.isfinite(jnp.asarray(x, dtype=jnp.float64)))


def near_zero(x, tol=EPS) -> bool:
    return finite(x) and abs(float(x)) <= tol


def positive(x, floor=EPS) -> bool:
    return finite(x) and float(x) > floor


def metric(row: dict, key: str):
    return row.get("metrics", {}).get(key)


def list_metric(row: dict, key: str):
    value = metric(row, key)
    return value if isinstance(value, list) else []


def same_list(row: dict, key: str, expected: list[int]) -> bool:
    return list_metric(row, key) == expected


def external_accept(row: dict) -> tuple[bool, list[str]]:
    """Independent row acceptance from metrics/check fields, not row['pass']."""
    rid = row.get("layer_id")
    fail: list[str] = []

    def need(name: str, ok: bool) -> None:
        if not ok:
            fail.append(name)

    checks = row.get("checks", {})
    need("all_reported_checks_true", all(bool(v) for v in checks.values()) and bool(checks))
    need("promotion_boundary_present", row.get("claim_boundary") == "diagnostic JAX layer row only; promotion_allowed=false")

    if rid == "F01_finite_carrier":
        need("normalized_s3", abs(float(metric(row, "max_s3_norm_drift"))) < 1.0e-12)
        need("trace_one", abs(float(metric(row, "density_trace_err"))) < 1.0e-12)
        need("positive_density", float(metric(row, "density_min_eval")) > -1.0e-9)
    elif rid == "N01_noncommuting_order":
        need("noncommuting_gap", float(metric(row, "order_gap_xy_yx")) > 1.0e-2)
        need("commuting_control_zero", near_zero(metric(row, "same_axis_control_gap"), 1.0e-12))
    elif rid == "response_effect_path_quotient":
        weights = jnp.asarray(list_metric(row, "weights"), dtype=jnp.float64)
        need("weights_normalized", weights.size == 2 and abs(float(jnp.sum(weights)) - 1.0) < 1.0e-9)
        need("path_entropy_finite", positive(metric(row, "path_entropy"), 1.0e-6))
        need("kraus_order_gap", positive(metric(row, "effect_kraus_order_gap"), 1.0e-3))
    elif rid == "boundary_environment_cut":
        need("bell_mi_nonzero", float(metric(row, "MI_bell")) > 1.9)
        need("product_mi_zero", near_zero(metric(row, "MI_product"), 1.0e-9))
        need("classical_mi_present", float(metric(row, "MI_classical")) > 0.9)
        need("classical_ln_zero", near_zero(metric(row, "LN_classical"), 1.0e-9))
    elif rid == "hopf_fiber_base":
        need("base_on_s2", abs(float(metric(row, "base_norm_drift"))) < 1.0e-12)
        need("fiber_invariant", abs(float(metric(row, "fiber_delta"))) < 1.0e-12)
        need("nonfiber_changes_base", float(metric(row, "nonfiber_delta_mean")) > 1.0e-2)
    elif rid == "dirac_monopole_u1_holonomy":
        need("phase_matches", abs(float(metric(row, "phase_error"))) < 1.0e-3)
        need("gauge_invariant", near_zero(metric(row, "gauge_error"), 1.0e-9))
        need("flat_control_kills", near_zero(metric(row, "flat_phase"), 1.0e-9))
    elif rid == "operator_substage_cell":
        need("order_changes_cell", float(metric(row, "rho_XY_vs_YX_gap")) > 1.0e-2)
        need("axis_changes_cell", float(metric(row, "rho_XY_vs_XZ_gap")) > 1.0e-2)
        need("trace_preserved", abs(float(metric(row, "trace_err"))) < 1.0e-12)
    elif rid == "gluing_groupoid_cocycle":
        need("cocycle_residual_small", abs(float(metric(row, "cocycle_residual"))) < 1.0e-12)
        need("bad_gluing_fails", float(metric(row, "bad_residual")) > 1.0e-2)
        need("scrambled_loop_nontrivial", float(metric(row, "scrambled_loop_gap")) > 1.0e-2)
    elif rid == "nested_hopf_shells":
        need("baseline_all_basins", same_list(row, "A_basins", [1, 2, 3, 4]))
        need("prune_kills_forbidden", same_list(row, "B_basins", [1, 2]))
        need("real_prune_fired", int(metric(row, "B_pruned")) > 0)
        need("coupling_beats_zero", float(metric(row, "coupled_alignment_delta")) > float(metric(row, "zero_control_alignment_delta")))
    elif rid == "weyl_gamma5_chirality":
        need("baseline_all_basins", same_list(row, "A", [1, 2, 3, 4]))
        need("gamma5_kills_forbidden", same_list(row, "B", [1, 2]))
        need("control_equals_baseline", same_list(row, "C", [1, 2, 3, 4]))
        need("random_keeps_forbidden", same_list(row, "random", [1, 2, 3, 4]))
        need("inverted_flips", same_list(row, "inverted", [3, 4]))
    elif rid == "qit_entropy_information":
        need("bell_ln_nonzero", float(metric(row, "LN_bell")) > 0.9)
        need("classical_ln_zero", near_zero(metric(row, "LN_classical"), 1.0e-9))
        need("product_ln_zero", near_zero(metric(row, "LN_product"), 1.0e-9))
        need("negative_conditional_entropy", float(metric(row, "S_A_given_B_bell")) < -0.9)
        need("coherent_info_positive", float(metric(row, "I_c_A_to_B_bell")) > 0.9)
        need("classical_mi_shadow_recorded", float(metric(row, "I_AB_classical")) > 0.9)
    elif rid == "capacity_path_entropy_budget":
        need("finite_boundary_entropy", positive(metric(row, "S_boundary"), 0.0))
        need("finite_path_entropy", positive(metric(row, "H_path"), 0.0))
        need("budget_admits", float(metric(row, "capacity_budget")) >= float(metric(row, "S_boundary")) + float(metric(row, "H_path")))
        need("small_budget_blocks", float(metric(row, "violated_budget_control")) < float(metric(row, "S_boundary")) + float(metric(row, "H_path")))
        need("path_registry_bound", float(metric(row, "H_path")) <= float(metric(row, "H_path_max")) + 1.0e-9)
    elif rid == "conditional_mutual_information_readout":
        need("ghz_cmi_nonzero", float(metric(row, "CMI_GHZ")) > 0.9)
        need("markov_cmi_zero", near_zero(metric(row, "CMI_markov_control"), 1.0e-9))
        need("classical_shadow_cmi", float(metric(row, "CMI_classical_shadow")) > 0.9)
        need("classical_shadow_ln_zero", near_zero(metric(row, "LN_classical_AC"), 1.0e-9))
    elif rid == "qit_relative_free_energy":
        need("relative_entropy_nonnegative", float(metric(row, "D_rho_sigma")) >= 0.0)
        need("self_relative_zero", near_zero(metric(row, "D_rho_rho"), 1.0e-9))
        need("logz_finite", finite(metric(row, "logZ")))
        need("free_energy_finite", finite(metric(row, "F_Q")))
    elif rid == "spectral_triple_dirac":
        spectrum = list_metric(row, "spectrum")
        need("commutator_nonzero", float(metric(row, "commutator_norm")) > 1.0e-2)
        need("spectrum_symmetric", spectrum == [-1.0, -1.0, 1.0, 1.0])
    elif rid == "twistor_null_incidence":
        need("null_incidence", near_zero(metric(row, "minkowski_norm"), 1.0e-9))
        need("phase_gauge_small", abs(float(metric(row, "phase_delta"))) < 1.0e-12)
        need("mixed_density_not_null", float(metric(row, "mixed_density_minkowski_norm")) > 1.0e-2)
    elif rid == "g_structure_form_identities":
        need("j_square_ok", near_zero(metric(row, "J_square_error"), 1.0e-12))
        need("metric_compat_ok", near_zero(metric(row, "metric_compat_error"), 1.0e-12))
        need("omega_nondegenerate", float(metric(row, "omega_det_abs")) > 0.9)
        need("degenerate_control_fails", near_zero(metric(row, "bad_det_abs"), 1.0e-12))
    elif rid == "left_right_weyl_terrain_loop":
        need("left_right_gap", float(metric(row, "left_right_gap")) > 1.0e-2)
        need("swap_matters", float(metric(row, "swap_matters_gap")) > 1.0e-2)
        need("sign_matters", float(metric(row, "sign_matters_gap")) > 1.0e-2)
    elif rid == "survivor_quotient_branch_prune":
        need("baseline_all_basins", same_list(row, "A", [1, 2, 3, 4]))
        need("prune_kills_forbidden", same_list(row, "B", [1, 2]))
        need("control_equals_baseline", same_list(row, "C", [1, 2, 3, 4]))
        need("real_prune_fired", int(metric(row, "B_pruned")) > 0)
    else:
        need("known_row_id", False)

    return len(fail) == 0, fail


CORRUPTIONS = {
    "F01_finite_carrier": ("metrics", "max_s3_norm_drift", 0.25),
    "N01_noncommuting_order": ("metrics", "order_gap_xy_yx", 0.0),
    "response_effect_path_quotient": ("metrics", "effect_kraus_order_gap", 0.0),
    "boundary_environment_cut": ("metrics", "LN_classical", 0.5),
    "hopf_fiber_base": ("metrics", "fiber_delta", 0.2),
    "dirac_monopole_u1_holonomy": ("metrics", "flat_phase", 0.5),
    "operator_substage_cell": ("metrics", "rho_XY_vs_YX_gap", 0.0),
    "gluing_groupoid_cocycle": ("metrics", "bad_residual", 0.0),
    "nested_hopf_shells": ("metrics", "B_basins", [1, 2, 3]),
    "weyl_gamma5_chirality": ("metrics", "random", [1, 2]),
    "qit_entropy_information": ("metrics", "LN_classical", 0.5),
    "capacity_path_entropy_budget": ("metrics", "violated_budget_control", 4.0),
    "conditional_mutual_information_readout": ("metrics", "LN_classical_AC", 0.5),
    "qit_relative_free_energy": ("metrics", "D_rho_rho", 0.25),
    "spectral_triple_dirac": ("metrics", "commutator_norm", 0.0),
    "twistor_null_incidence": ("metrics", "mixed_density_minkowski_norm", 0.0),
    "g_structure_form_identities": ("metrics", "bad_det_abs", 0.8),
    "left_right_weyl_terrain_loop": ("metrics", "swap_matters_gap", 0.0),
    "survivor_quotient_branch_prune": ("metrics", "B", [1, 2, 3]),
}


def corrupt(row: dict) -> dict:
    row = copy.deepcopy(row)
    rid = row["layer_id"]
    section, key, value = CORRUPTIONS[rid]
    row[section][key] = value
    row["pass"] = True  # The external oracle must ignore this self-report.
    return row


def main() -> None:
    receipt = json.loads(IN_PATH.read_text())
    rows = receipt.get("layer_results", [])
    results = []
    for row in rows:
        rid = row["layer_id"]
        base_ok, base_fail = external_accept(row)
        bad = corrupt(row)
        corrupt_ok, corrupt_fail = external_accept(bad)
        results.append(
            {
                "layer_id": rid,
                "external_accepts_original": base_ok,
                "external_rejects_corruption": not corrupt_ok,
                "original_failures": base_fail,
                "corruption_failures": corrupt_fail,
                "corruption": {"path": CORRUPTIONS[rid][0:2], "value": CORRUPTIONS[rid][2]},
            }
        )

    all_pass = (
        receipt.get("executed_track") == "jax"
        and receipt.get("ran_julia") is False
        and receipt.get("julia_reference_mode") == "read_only"
        and receipt.get("promotion_allowed") is False
        and len(rows) == 19
        and all(r["external_accepts_original"] and r["external_rejects_corruption"] for r in results)
    )

    OUT_PATH.write_text(
        json.dumps(
            {
                "AUDIT_PASS": bool(all_pass),
                "name": "jax_external_negative_oracle_audit",
                "classification": "external_negative_oracle_for_diagnostic_jax_receipt",
                "promotion_allowed": False,
                "executed_track": "jax",
                "ran_julia": False,
                "julia_reference_mode": "read_only",
                "purpose": "External row-wise negative oracle that does not trust row-local pass flags.",
                "source_receipt": str(IN_PATH),
                "rows_checked": len(results),
                "rows_external_accept_original": sum(1 for r in results if r["external_accepts_original"]),
                "rows_external_reject_corruption": sum(1 for r in results if r["external_rejects_corruption"]),
                "blocked_consumers": receipt.get("blocked_consumers", []),
                "council_blocker_addressed": "self-grading risk: corrupted controls are rejected even when row pass flag remains true",
                "results": results,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(
        f"external_negative_oracle rows={len(results)} "
        f"accept_original={sum(1 for r in results if r['external_accepts_original'])} "
        f"reject_corruption={sum(1 for r in results if r['external_rejects_corruption'])} "
        f"AUDIT_PASS={bool(all_pass)}"
    )


if __name__ == "__main__":
    main()
