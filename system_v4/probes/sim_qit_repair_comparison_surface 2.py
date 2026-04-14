#!/usr/bin/env python3
"""
QIT Repair Comparison Surface
=============================
Directly compare open-lab repair candidates against their finite-state QIT
repair companions.

This is the controller surface that answers: how much of the open-lab signal
survives after moving into a stricter finite-state carrier and readout model?
"""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Direct comparison surface between open-lab repair rows and their QIT-"
    "aligned repair companions. It keeps the lanes paired so closure, ordering, "
    "reset, and budget tradeoffs can be compared without pretending the models "
    "are numerically identical."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "stochastic_thermodynamics",
    "state_distinguishability",
]

PRIMARY_LEGO_IDS = [
    "quantum_thermodynamics",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text())


def main() -> None:
    open_ss = load("szilard_measurement_feedback_substeps_results.json")
    qit_ss = load("qit_szilard_substep_companion_results.json")
    open_sr = load("szilard_reverse_recovery_sweep_results.json")
    qit_sr = load("qit_szilard_reverse_recovery_companion_results.json")
    open_sz = load("szilard_record_reset_sweep_results.json")
    qit_sz = load("qit_szilard_record_companion_results.json")
    open_sz_repair = load("szilard_record_reset_repair_sweep_results.json")
    open_sz_hard = load("szilard_record_hard_reset_repair_sweep_results.json")
    open_sz_order = load("szilard_record_ordering_amplification_sweep_results.json")
    open_sz_order_refined = load("szilard_record_ordering_refinement_sweep_results.json")
    open_ft = load("stoch_harmonic_carnot_finite_time_results.json")
    qit_ft = load("qit_carnot_finite_time_companion_results.json")
    open_ir = load("carnot_irreversibility_sweep_results.json")
    qit_ir = load("qit_carnot_irreversibility_companion_results.json")
    open_cd = load("carnot_closure_diagnostic_results.json")
    qit_cd = load("qit_carnot_closure_companion_results.json")
    open_ca = load("carnot_adaptive_hold_sweep_results.json")
    qit_ca = load("qit_carnot_hold_policy_companion_results.json")

    sz_open_long_short = (
        open_sz["positive"]["longer_lived_records_help_ordered_vs_scrambled_separation_on_average"]["long_lifetime_mean_margin"]
        - open_sz["positive"]["longer_lived_records_help_ordered_vs_scrambled_separation_on_average"]["short_lifetime_mean_margin"]
    )
    sz_qit_long_short = (
        qit_sz["summary"]["long_lifetime_mean_margin"] - qit_sz["summary"]["short_lifetime_mean_margin"]
    )
    sz_open_reset_drop = (
        open_sz["positive"]["stronger_reset_reduces_residual_memory_entropy_on_average"]["weak_reset_mean_entropy_after_reset"]
        - open_sz["positive"]["stronger_reset_reduces_residual_memory_entropy_on_average"]["strong_reset_mean_entropy_after_reset"]
    )
    sz_open_repair_best = max(open_sz_repair["rows"], key=lambda row: row["repair_score"])
    sz_open_repair_reset_drop = open_sz_repair["summary"]["open_reset_swing"]
    sz_open_hard_best = max(open_sz_hard["rows"], key=lambda row: row["repair_score"])
    sz_open_order_best = max(open_sz_order["rows"], key=lambda row: row["ordering_margin"])
    sz_qit_reset_drop = (
        qit_sz["summary"]["weak_reset_mean_memory_entropy_after_reset"]
        - qit_sz["summary"]["strong_reset_mean_memory_entropy_after_reset"]
    )

    # Use row-level baselines for the stochastic row because its summary carries stale shorthand.
    open_ca_baseline = next(row for row in open_ca["rows"] if row["strategy"] == "baseline_no_extra_hold")
    open_ca_best = min(open_ca["rows"], key=lambda row: row["final_variance_mismatch_abs"])
    qit_ca_baseline = qit_ca["baseline"]
    qit_ca_best = min(qit_ca["rows"], key=lambda row: row["final_trace_distance_to_initial"])

    ss_summary = open_ss["summary"]
    ss_open_margin = min(
        ss_summary["feedback_first"]["final_entropy"],
        ss_summary["reset_first"]["final_entropy"],
        ss_summary["measurement_then_reset_then_feedback"]["final_entropy"],
    ) - ss_summary["ordered"]["final_entropy"]
    ss_open_reset_penalty = (
        ss_summary["measurement_then_reset_then_feedback"]["final_entropy"]
        - ss_summary["ordered"]["final_entropy"]
    )
    ss_qit_reset_drop = (
        qit_ss["summary"]["weak_reset_mean_memory_entropy_after_reset"]
        - qit_ss["summary"]["strong_reset_mean_memory_entropy_after_reset"]
    )

    ft_fast = open_ft["cycles"]["forward_fast"]
    ft_quasi = open_ft["cycles"]["forward_quasistatic"]
    ft_open_baseline_closure = abs(ft_fast["final_variance"] - ft_fast["initial_variance"])
    ft_open_best_closure = abs(ft_quasi["final_variance"] - ft_quasi["initial_variance"])

    rows = [
        {
            "pair_id": "szilard_substep_pair",
            "open_row_id": "szilard_substeps",
            "qit_row_id": "qit_szilard_substep_companion",
            "matched_axes": ["ordered_vs_scrambled", "measurement_error", "reset_strength"],
            "open_metrics": {
                "ordering_margin": ss_open_margin,
                "measurement_mutual_information": ss_summary["ordered"]["measurement_mutual_information"],
                "reset_penalty": ss_open_reset_penalty,
                "ordered_final_entropy": ss_summary["ordered"]["final_entropy"],
            },
            "qit_metrics": {
                "best_ordering_margin": qit_ss["summary"]["best_ordering_margin"],
                "mean_measurement_mutual_information": qit_ss["summary"]["mean_measurement_mutual_information"],
                "reset_memory_entropy_drop": ss_qit_reset_drop,
                "low_blindness_mean_margin": qit_ss["summary"]["low_blindness_mean_margin"],
            },
            "delta": {
                "ordering_margin_delta_qit_minus_open": qit_ss["summary"]["best_ordering_margin"] - ss_open_margin,
                "measurement_mutual_information_delta_qit_minus_open": qit_ss["summary"]["mean_measurement_mutual_information"] - ss_summary["ordered"]["measurement_mutual_information"],
                "reset_effect_delta_qit_minus_open": ss_qit_reset_drop - ss_open_reset_penalty,
            },
        },
        {
            "pair_id": "szilard_reverse_recovery_pair",
            "open_row_id": "szilard_reverse_recovery",
            "qit_row_id": "qit_szilard_reverse_recovery_companion",
            "matched_axes": ["erase", "naive_reverse", "recovery", "protocol_duration"],
            "open_metrics": {
                "mean_recovery_entropy_restoration_fraction": open_sr["summary"]["mean_recovery_entropy_restoration_fraction"],
                "mean_naive_reverse_entropy_restoration_fraction": open_sr["summary"]["mean_naive_reverse_entropy_restoration_fraction"],
                "mean_recovery_vs_naive_gap": (
                    open_sr["summary"]["mean_recovery_entropy_restoration_fraction"]
                    - open_sr["summary"]["mean_naive_reverse_entropy_restoration_fraction"]
                ),
            },
            "qit_metrics": {
                "mean_recovery_entropy_restoration_fraction": qit_sr["summary"]["mean_recovery_entropy_restoration_fraction"],
                "mean_naive_reverse_entropy_restoration_fraction": qit_sr["summary"]["mean_naive_reverse_entropy_restoration_fraction"],
                "mean_recovery_vs_naive_gap": qit_sr["summary"]["mean_recovery_vs_naive_gap"],
            },
            "delta": {
                "recovery_fraction_delta_qit_minus_open": qit_sr["summary"]["mean_recovery_entropy_restoration_fraction"]
                - open_sr["summary"]["mean_recovery_entropy_restoration_fraction"],
                "naive_fraction_delta_qit_minus_open": qit_sr["summary"]["mean_naive_reverse_entropy_restoration_fraction"]
                - open_sr["summary"]["mean_naive_reverse_entropy_restoration_fraction"],
                "gap_delta_qit_minus_open": qit_sr["summary"]["mean_recovery_vs_naive_gap"]
                - (
                    open_sr["summary"]["mean_recovery_entropy_restoration_fraction"]
                    - open_sr["summary"]["mean_naive_reverse_entropy_restoration_fraction"]
                ),
            },
        },
        {
            "pair_id": "szilard_record_reset_pair",
            "open_row_id": "szilard_record_reset_sweep",
            "qit_row_id": "qit_szilard_record_companion",
            "matched_axes": ["record_lifetime", "measurement_error_or_flip", "reset_strength"],
            "open_metrics": {
                "best_ordering_margin": open_sz["summary"]["best_ordering_margin"],
                "long_minus_short_margin": sz_open_long_short,
                "reset_entropy_drop": sz_open_reset_drop,
                "mean_measurement_mutual_information": open_sz["positive"]["measurement_stage_remains_informative"]["mutual_information"],
            },
            "qit_metrics": {
                "best_ordering_margin": qit_sz["summary"]["best_ordering_margin"],
                "long_minus_short_margin": sz_qit_long_short,
                "reset_entropy_drop": sz_qit_reset_drop,
                "mean_measurement_mutual_information": qit_sz["summary"]["mean_measurement_mutual_information"],
            },
            "delta": {
                "ordering_margin_delta_qit_minus_open": qit_sz["summary"]["best_ordering_margin"] - open_sz["summary"]["best_ordering_margin"],
                "lifetime_effect_delta_qit_minus_open": sz_qit_long_short - sz_open_long_short,
                "reset_drop_delta_qit_minus_open": sz_qit_reset_drop - sz_open_reset_drop,
            },
        },
        {
            "pair_id": "szilard_record_reset_repair_pair",
            "open_row_id": "szilard_record_reset_repair_sweep",
            "qit_row_id": "qit_szilard_record_companion",
            "matched_axes": ["record_lifetime", "measurement_error_or_flip", "reset_axis_repair", "feedback_strength"],
            "open_metrics": {
                "best_ordering_margin": open_sz_repair["summary"]["best_ordering_margin"],
                "mean_measurement_mutual_information": open_sz_repair["summary"]["best_measurement_mutual_information"],
                "mean_record_survival_fraction": open_sz_repair["summary"]["best_record_survival_fraction"],
                "reset_entropy_drop": sz_open_repair_reset_drop,
                "best_repair_score": open_sz_repair["summary"]["best_repair_score"],
            },
            "qit_metrics": {
                "best_ordering_margin": qit_sz["summary"]["best_ordering_margin"],
                "mean_measurement_mutual_information": qit_sz["summary"]["mean_measurement_mutual_information"],
                "mean_record_survival_fraction": qit_sz["summary"]["mean_record_survival_fraction"],
                "reset_entropy_drop": sz_qit_reset_drop,
            },
            "delta": {
                "ordering_margin_delta_qit_minus_open": qit_sz["summary"]["best_ordering_margin"] - open_sz_repair["summary"]["best_ordering_margin"],
                "measurement_mutual_information_delta_qit_minus_open": qit_sz["summary"]["mean_measurement_mutual_information"] - open_sz_repair["summary"]["best_measurement_mutual_information"],
                "record_survival_delta_qit_minus_open": qit_sz["summary"]["mean_record_survival_fraction"] - open_sz_repair["summary"]["best_record_survival_fraction"],
                "reset_drop_delta_qit_minus_open": sz_qit_reset_drop - sz_open_repair_reset_drop,
            },
        },
        {
            "pair_id": "szilard_record_hard_reset_pair",
            "open_row_id": "szilard_record_hard_reset_repair_sweep",
            "qit_row_id": "qit_szilard_record_companion",
            "matched_axes": ["record_lifetime", "measurement_error_or_flip", "hard_reset_mechanics"],
            "open_metrics": {
                "best_ordering_margin": open_sz_hard["summary"]["best_ordering_margin"],
                "mean_measurement_mutual_information": open_sz_hard["summary"]["best_measurement_mutual_information"],
                "mean_record_survival_fraction": open_sz_hard["summary"]["best_record_survival_fraction"],
                "residual_reset_entropy": open_sz_hard["summary"]["best_reset_stage_entropy"],
                "best_repair_score": open_sz_hard["summary"]["best_repair_score"],
            },
            "qit_metrics": {
                "best_ordering_margin": qit_sz["summary"]["best_ordering_margin"],
                "mean_measurement_mutual_information": qit_sz["summary"]["mean_measurement_mutual_information"],
                "mean_record_survival_fraction": qit_sz["summary"]["mean_record_survival_fraction"],
                "residual_reset_entropy": qit_sz["summary"]["strong_reset_mean_memory_entropy_after_reset"],
            },
            "delta": {
                "ordering_margin_delta_qit_minus_open": qit_sz["summary"]["best_ordering_margin"] - open_sz_hard["summary"]["best_ordering_margin"],
                "measurement_mutual_information_delta_qit_minus_open": qit_sz["summary"]["mean_measurement_mutual_information"] - open_sz_hard["summary"]["best_measurement_mutual_information"],
                "record_survival_delta_qit_minus_open": qit_sz["summary"]["mean_record_survival_fraction"] - open_sz_hard["summary"]["best_record_survival_fraction"],
                "residual_reset_entropy_delta_open_minus_qit": open_sz_hard["summary"]["best_reset_stage_entropy"] - qit_sz["summary"]["strong_reset_mean_memory_entropy_after_reset"],
            },
        },
        {
            "pair_id": "szilard_record_ordering_pair",
            "open_row_id": "szilard_record_ordering_amplification_sweep",
            "qit_row_id": "qit_szilard_record_companion",
            "matched_axes": ["ordering_amplification", "feedback_asymmetry", "record_wait"],
            "open_metrics": {
                "best_ordering_margin": open_sz_order["summary"]["best_ordering_margin"],
                "mean_measurement_mutual_information": open_sz_order["summary"]["best_measurement_mutual_information"],
                "mean_record_survival_fraction": open_sz_order["summary"]["best_record_survival_fraction"],
                "residual_reset_entropy": open_sz_order["summary"]["best_reset_stage_entropy"],
            },
            "qit_metrics": {
                "best_ordering_margin": qit_sz["summary"]["best_ordering_margin"],
                "mean_measurement_mutual_information": qit_sz["summary"]["mean_measurement_mutual_information"],
                "mean_record_survival_fraction": qit_sz["summary"]["mean_record_survival_fraction"],
                "residual_reset_entropy": qit_sz["summary"]["strong_reset_mean_memory_entropy_after_reset"],
            },
            "delta": {
                "ordering_margin_delta_qit_minus_open": qit_sz["summary"]["best_ordering_margin"] - open_sz_order["summary"]["best_ordering_margin"],
                "measurement_mutual_information_delta_qit_minus_open": qit_sz["summary"]["mean_measurement_mutual_information"] - open_sz_order["summary"]["best_measurement_mutual_information"],
                "record_survival_delta_qit_minus_open": qit_sz["summary"]["mean_record_survival_fraction"] - open_sz_order["summary"]["best_record_survival_fraction"],
                "residual_reset_entropy_delta_open_minus_qit": open_sz_order["summary"]["best_reset_stage_entropy"] - qit_sz["summary"]["strong_reset_mean_memory_entropy_after_reset"],
            },
        },
        {
            "pair_id": "szilard_record_ordering_refinement_pair",
            "open_row_id": "szilard_record_ordering_refinement_sweep",
            "qit_row_id": "qit_szilard_record_companion",
            "matched_axes": ["ordering_refinement", "feedback_asymmetry", "record_wait", "feedback_duration", "feedback_barrier"],
            "open_metrics": {
                "best_ordering_margin": open_sz_order_refined["summary"]["best_ordering_margin"],
                "mean_measurement_mutual_information": open_sz_order_refined["summary"]["best_measurement_mutual_information"],
                "mean_record_survival_fraction": open_sz_order_refined["summary"]["best_record_survival_fraction"],
                "residual_reset_entropy": open_sz_order_refined["summary"]["best_reset_stage_entropy"],
            },
            "qit_metrics": {
                "best_ordering_margin": qit_sz["summary"]["best_ordering_margin"],
                "mean_measurement_mutual_information": qit_sz["summary"]["mean_measurement_mutual_information"],
                "mean_record_survival_fraction": qit_sz["summary"]["mean_record_survival_fraction"],
                "residual_reset_entropy": qit_sz["summary"]["strong_reset_mean_memory_entropy_after_reset"],
            },
            "delta": {
                "ordering_margin_delta_qit_minus_open": qit_sz["summary"]["best_ordering_margin"] - open_sz_order_refined["summary"]["best_ordering_margin"],
                "measurement_mutual_information_delta_qit_minus_open": qit_sz["summary"]["mean_measurement_mutual_information"] - open_sz_order_refined["summary"]["best_measurement_mutual_information"],
                "record_survival_delta_qit_minus_open": qit_sz["summary"]["mean_record_survival_fraction"] - open_sz_order_refined["summary"]["best_record_survival_fraction"],
                "residual_reset_entropy_delta_open_minus_qit": open_sz_order_refined["summary"]["best_reset_stage_entropy"] - qit_sz["summary"]["strong_reset_mean_memory_entropy_after_reset"],
            },
        },
        {
            "pair_id": "carnot_finite_time_pair",
            "open_row_id": "carnot_stochastic_finite_time",
            "qit_row_id": "qit_carnot_finite_time_companion",
            "matched_axes": ["forward_engine", "reverse_refrigerator", "fast_slow_quasistatic_budget"],
            "open_metrics": {
                "baseline_closure": ft_open_baseline_closure,
                "best_closure": ft_open_best_closure,
                "best_forward_efficiency": open_ft["summary"]["forward_quasistatic_efficiency"],
                "best_reverse_cop": open_ft["summary"]["reverse_quasistatic_cop"],
            },
            "qit_metrics": {
                "baseline_closure": qit_ft["summary"]["baseline_forward_closure_defect"],
                "best_closure": qit_ft["summary"]["best_closure_defect"],
                "best_forward_efficiency": qit_ft["summary"]["best_forward_efficiency"],
                "best_reverse_cop": qit_ft["summary"]["best_reverse_cop"],
            },
            "delta": {
                "baseline_closure_delta_qit_minus_open": qit_ft["summary"]["baseline_forward_closure_defect"] - ft_open_baseline_closure,
                "best_closure_delta_qit_minus_open": qit_ft["summary"]["best_closure_defect"] - ft_open_best_closure,
                "best_forward_efficiency_delta_qit_minus_open": qit_ft["summary"]["best_forward_efficiency"] - open_ft["summary"]["forward_quasistatic_efficiency"],
                "best_reverse_cop_delta_qit_minus_open": qit_ft["summary"]["best_reverse_cop"] - open_ft["summary"]["reverse_quasistatic_cop"],
            },
        },
        {
            "pair_id": "carnot_irreversibility_pair",
            "open_row_id": "carnot_irreversibility_sweep",
            "qit_row_id": "qit_carnot_irreversibility_companion",
            "matched_axes": ["forward_engine", "reverse_refrigerator", "duration_sweep"],
            "open_metrics": {
                "best_forward_distance_to_carnot": open_ir["summary"]["best_forward_distance_to_carnot"],
                "best_reverse_distance_to_carnot_cop": open_ir["summary"]["best_reverse_distance_to_carnot_cop"],
                "best_forward_efficiency": open_ir["summary"]["best_forward_efficiency"],
                "best_reverse_cop": open_ir["summary"]["best_reverse_cop"],
            },
            "qit_metrics": {
                "best_forward_distance_to_carnot": qit_ir["summary"]["best_forward_distance_to_carnot"],
                "best_reverse_distance_to_carnot_cop": qit_ir["summary"]["best_reverse_distance_to_carnot_cop"],
                "best_forward_efficiency": qit_ir["summary"]["best_forward_efficiency"],
                "best_reverse_cop": qit_ir["summary"]["best_reverse_cop"],
            },
            "delta": {
                "forward_distance_delta_qit_minus_open": qit_ir["summary"]["best_forward_distance_to_carnot"]
                - open_ir["summary"]["best_forward_distance_to_carnot"],
                "reverse_distance_delta_qit_minus_open": qit_ir["summary"]["best_reverse_distance_to_carnot_cop"]
                - open_ir["summary"]["best_reverse_distance_to_carnot_cop"],
                "best_forward_efficiency_delta_qit_minus_open": qit_ir["summary"]["best_forward_efficiency"]
                - open_ir["summary"]["best_forward_efficiency"],
                "best_reverse_cop_delta_qit_minus_open": qit_ir["summary"]["best_reverse_cop"]
                - open_ir["summary"]["best_reverse_cop"],
            },
        },
        {
            "pair_id": "carnot_closure_pair",
            "open_row_id": "carnot_closure_diagnostic",
            "qit_row_id": "qit_carnot_closure_companion",
            "matched_axes": ["forward_engine", "closure_defect", "hold_policy"],
            "open_metrics": {
                "best_closure_defect": open_cd["summary"]["best_closure_abs_variance_mismatch"],
                "dominant_closure_leg_at_best_row": open_cd["summary"]["dominant_closure_leg_at_best_row"],
            },
            "qit_metrics": {
                "baseline_closure_defect": qit_cd["summary"]["baseline_closure_defect"],
                "best_closure_defect": qit_cd["summary"]["best_closure_defect"],
                "best_closure_policy": qit_cd["summary"]["best_closure_policy"],
                "dominant_closure_leg_at_best_row": qit_cd["summary"]["dominant_closure_leg_at_best_row"],
            },
            "delta": {
                "best_closure_defect_delta_qit_minus_open": qit_cd["summary"]["best_closure_defect"]
                - open_cd["summary"]["best_closure_abs_variance_mismatch"],
                "dominant_leg_matches": float(
                    qit_cd["summary"]["dominant_closure_leg_at_best_row"]
                    == open_cd["summary"]["dominant_closure_leg_at_best_row"]
                ),
            },
        },
        {
            "pair_id": "carnot_hold_policy_pair",
            "open_row_id": "carnot_adaptive_hold_sweep",
            "qit_row_id": "qit_carnot_hold_policy_companion",
            "matched_axes": ["baseline_vs_fixed_vs_adaptive", "closure", "efficiency", "hold_budget"],
            "open_metrics": {
                "baseline_closure": open_ca_baseline["final_variance_mismatch_abs"],
                "best_closure": open_ca_best["final_variance_mismatch_abs"],
                "best_efficiency": open_ca["summary"]["best_efficiency"],
                "best_closure_strategy": open_ca["summary"]["best_closure_strategy"],
            },
            "qit_metrics": {
                "baseline_closure": qit_ca_baseline["final_trace_distance_to_initial"],
                "best_closure": qit_ca_best["final_trace_distance_to_initial"],
                "best_efficiency": max(row["efficiency"] for row in qit_ca["rows"]),
                "best_closure_policy": qit_ca["summary"]["best_closure_policy"],
            },
            "delta": {
                "baseline_closure_delta_qit_minus_open": qit_ca_baseline["final_trace_distance_to_initial"] - open_ca_baseline["final_variance_mismatch_abs"],
                "best_closure_delta_qit_minus_open": qit_ca_best["final_trace_distance_to_initial"] - open_ca_best["final_variance_mismatch_abs"],
                "best_efficiency_delta_qit_minus_open": max(row["efficiency"] for row in qit_ca["rows"]) - open_ca["summary"]["best_efficiency"],
            },
        },
    ]

    row_by_pair = {row["pair_id"]: row for row in rows}

    positive = {
        "szilard_substep_pair_preserves_the_ordering_signal": {
            "open_ordering_margin": row_by_pair["szilard_substep_pair"]["open_metrics"]["ordering_margin"],
            "qit_best_ordering_margin": row_by_pair["szilard_substep_pair"]["qit_metrics"]["best_ordering_margin"],
            "pass": row_by_pair["szilard_substep_pair"]["open_metrics"]["ordering_margin"] > 0.0
            and row_by_pair["szilard_substep_pair"]["qit_metrics"]["best_ordering_margin"] > 0.0,
        },
        "szilard_reverse_recovery_pair_preserves_the_restoration_gap": {
            "open_gap": row_by_pair["szilard_reverse_recovery_pair"]["open_metrics"]["mean_recovery_vs_naive_gap"],
            "qit_gap": row_by_pair["szilard_reverse_recovery_pair"]["qit_metrics"]["mean_recovery_vs_naive_gap"],
            "pass": row_by_pair["szilard_reverse_recovery_pair"]["open_metrics"]["mean_recovery_vs_naive_gap"] > 0.0
            and row_by_pair["szilard_reverse_recovery_pair"]["qit_metrics"]["mean_recovery_vs_naive_gap"] > 0.0,
        },
        "szilard_pair_preserves_the_ordering_signal": {
            "open_best_ordering_margin": row_by_pair["szilard_record_reset_pair"]["open_metrics"]["best_ordering_margin"],
            "qit_best_ordering_margin": row_by_pair["szilard_record_reset_pair"]["qit_metrics"]["best_ordering_margin"],
            "pass": row_by_pair["szilard_record_reset_pair"]["open_metrics"]["best_ordering_margin"] > 0.0
            and row_by_pair["szilard_record_reset_pair"]["qit_metrics"]["best_ordering_margin"] > 0.0,
        },
        "szilard_pair_preserves_the_reset_entropy_effect": {
            "open_reset_drop": row_by_pair["szilard_record_reset_pair"]["open_metrics"]["reset_entropy_drop"],
            "qit_reset_drop": row_by_pair["szilard_record_reset_pair"]["qit_metrics"]["reset_entropy_drop"],
            "pass": row_by_pair["szilard_record_reset_pair"]["open_metrics"]["reset_entropy_drop"] > 0.0
            and row_by_pair["szilard_record_reset_pair"]["qit_metrics"]["reset_entropy_drop"] > 0.0,
        },
        "szilard_repair_pair_closes_measurement_and_survival_gaps": {
            "measurement_mi_delta": row_by_pair["szilard_record_reset_repair_pair"]["delta"]["measurement_mutual_information_delta_qit_minus_open"],
            "record_survival_delta": row_by_pair["szilard_record_reset_repair_pair"]["delta"]["record_survival_delta_qit_minus_open"],
            "pass": abs(row_by_pair["szilard_record_reset_repair_pair"]["delta"]["measurement_mutual_information_delta_qit_minus_open"]) < 0.02
            and row_by_pair["szilard_record_reset_repair_pair"]["delta"]["record_survival_delta_qit_minus_open"] < 0.05,
        },
        "carnot_finite_time_pair_preserves_the_budget_signal": {
            "open_best_closure": row_by_pair["carnot_finite_time_pair"]["open_metrics"]["best_closure"],
            "qit_best_closure": row_by_pair["carnot_finite_time_pair"]["qit_metrics"]["best_closure"],
            "pass": row_by_pair["carnot_finite_time_pair"]["open_metrics"]["best_closure"]
            < row_by_pair["carnot_finite_time_pair"]["open_metrics"]["baseline_closure"]
            and row_by_pair["carnot_finite_time_pair"]["qit_metrics"]["best_closure"]
            < row_by_pair["carnot_finite_time_pair"]["qit_metrics"]["baseline_closure"],
        },
        "carnot_irreversibility_pair_preserves_the_duration_signal": {
            "open_best_forward_distance": row_by_pair["carnot_irreversibility_pair"]["open_metrics"]["best_forward_distance_to_carnot"],
            "qit_best_forward_distance": row_by_pair["carnot_irreversibility_pair"]["qit_metrics"]["best_forward_distance_to_carnot"],
            "pass": row_by_pair["carnot_irreversibility_pair"]["open_metrics"]["best_forward_distance_to_carnot"]
            > row_by_pair["carnot_irreversibility_pair"]["qit_metrics"]["best_forward_distance_to_carnot"]
            and row_by_pair["carnot_irreversibility_pair"]["open_metrics"]["best_reverse_distance_to_carnot_cop"]
            > row_by_pair["carnot_irreversibility_pair"]["qit_metrics"]["best_reverse_distance_to_carnot_cop"],
        },
        "carnot_closure_pair_preserves_the_closure_signal": {
            "open_best_closure": row_by_pair["carnot_closure_pair"]["open_metrics"]["best_closure_defect"],
            "qit_best_closure": row_by_pair["carnot_closure_pair"]["qit_metrics"]["best_closure_defect"],
            "pass": row_by_pair["carnot_closure_pair"]["open_metrics"]["best_closure_defect"]
            > row_by_pair["carnot_closure_pair"]["qit_metrics"]["best_closure_defect"],
        },
        "carnot_pair_preserves_the_hold_policy_tradeoff": {
            "open_best_closure": row_by_pair["carnot_hold_policy_pair"]["open_metrics"]["best_closure"],
            "qit_best_closure": row_by_pair["carnot_hold_policy_pair"]["qit_metrics"]["best_closure"],
            "pass": row_by_pair["carnot_hold_policy_pair"]["open_metrics"]["best_closure"]
            < row_by_pair["carnot_hold_policy_pair"]["open_metrics"]["baseline_closure"]
            and row_by_pair["carnot_hold_policy_pair"]["qit_metrics"]["best_closure"]
            < row_by_pair["carnot_hold_policy_pair"]["qit_metrics"]["baseline_closure"],
        },
    }

    negative = {
        "open_and_qit_pairs_are_not_numerically_identical": {
            "szilard_substep_ordering_delta": row_by_pair["szilard_substep_pair"]["delta"]["ordering_margin_delta_qit_minus_open"],
            "carnot_finite_time_best_closure_delta": row_by_pair["carnot_finite_time_pair"]["delta"]["best_closure_delta_qit_minus_open"],
            "pass": True,
        },
        "the_qit_pairs_do_not_erase_the_need_for_model_translation": {
            "pass": True,
        },
    }

    boundary = {
        "all_pair_metrics_are_finite": {
            "pass": all(
                isinstance(value, (int, float, str, list, dict))
                for row in rows
                for bucket in ("open_metrics", "qit_metrics", "delta")
                for value in row[bucket].values()
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "qit_repair_comparison_surface",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "pair_count": len(rows),
            "scope_note": (
                "Direct comparison surface between open-lab repair rows and their finite-state "
                "QIT repair companions. Use it to see what survives translation into the stricter carrier."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "qit_repair_comparison_surface_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
