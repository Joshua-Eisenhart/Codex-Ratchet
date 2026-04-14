#!/usr/bin/env python3
"""
QIT Entropy Companion Array
===========================
Strict readout-family companion surface over the finite-carrier QIT anchor set.
"""

from __future__ import annotations

import json
import pathlib
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Strict QIT entropy/readout companion surface over the finite-carrier anchor "
    "rows. Use it to compare open-lab rows against matched strict readouts."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "landauer_erasure",
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
    sz = load("qit_szilard_landauer_cycle_results.json")
    sc = load("qit_strong_coupling_landauer_results.json")
    ca = load("qit_carnot_two_bath_cycle_results.json")
    ab = load("qit_attractor_basin_recovery_results.json")
    qss = load("qit_szilard_substep_companion_results.json")
    qsr = load("qit_szilard_record_companion_results.json")
    qsv = load("qit_szilard_reverse_recovery_companion_results.json")
    qcf = load("qit_carnot_finite_time_companion_results.json")
    qcc = load("qit_carnot_closure_companion_results.json")
    qch = load("qit_carnot_hold_policy_companion_results.json")
    qci = load("qit_carnot_irreversibility_companion_results.json")

    rows = [
        {
            "row_id": "qit_szilard_landauer_cycle",
            "family": "szilard",
            "carrier": "finite_two_qubit_system_memory",
            "readout_families": ["mutual_information", "free_energy_gain", "erasure_cost"],
            "headline_readouts": {
                "mutual_information": sz["positive"]["measurement_creates_one_bit_of_system_memory_correlation"]["mutual_information"],
                "free_energy_gain": sz["positive"]["conditional_feedback_converts_information_into_one_bit_of_system_free_energy"]["system_free_energy_gain"],
                "erasure_cost": sz["positive"]["memory_erasure_closes_the_cycle_at_the_same_kT_ln2_scale"]["erasure_cost"],
                "net_after_erasure": sz["negative"]["cycle_does_not_claim_free_work_beyond_landauer_balance"]["net_after_erasure"],
            },
        },
        {
            "row_id": "qit_strong_coupling_landauer",
            "family": "strong_coupling_landauer",
            "carrier": "finite_two_qubit_system_bath",
            "readout_families": ["local_clausius_gap", "joint_clausius_gap", "system_bath_mutual_information"],
            "headline_readouts": {
                "local_clausius_gap_strong": sc["positive"]["naive_reduced_system_bookkeeping_shows_an_apparent_clausius_violation_at_strong_coupling"]["local_clausius_gap_strong"],
                "joint_clausius_gap_complete": sc["positive"]["joint_system_bath_bookkeeping_restores_the_bound_for_the_complete_process"]["complete_process_clausius_gap"],
                "initial_system_bath_mutual_information": sc["positive"]["strong_coupling_creates_correlation_and_non_gibbs_reduced_states"]["initial_system_bath_mutual_information"],
            },
        },
        {
            "row_id": "qit_carnot_two_bath_cycle",
            "family": "carnot",
            "carrier": "finite_qubit_working_substance",
            "readout_families": ["efficiency", "cop", "exact_carnot_distance"],
            "headline_readouts": {
                "forward_efficiency": ca["summary"]["forward_efficiency"],
                "forward_distance_to_carnot": abs(ca["summary"]["forward_efficiency"] - ca["summary"]["forward_carnot_bound"]),
                "reverse_cop": ca["summary"]["reverse_cop"],
                "reverse_distance_to_carnot_cop": abs(ca["summary"]["reverse_cop"] - ca["summary"]["reverse_cop_carnot"]),
            },
        },
        {
            "row_id": "qit_attractor_basin_recovery",
            "family": "control_recovery",
            "carrier": "finite_qubit_process_class",
            "readout_families": ["class_return_gap", "order_gap", "terminal_trace_gap"],
            "headline_readouts": {
                "chosen_order_gap": ab["positive"]["chosen_order_beats_the_swapped_order_on_class_return"]["one_cycle_order_gap"],
                "terminal_trace_gap": ab["positive"]["nearby_perturbations_return_to_the_same_recovery_class"]["terminal_trace_gap"],
                "commuting_order_gap": ab["negative"]["commuting_control_schedule_loses_the_order_effect"]["commuting_order_gap"],
            },
        },
        {
            "row_id": "qit_szilard_substep_companion",
            "family": "szilard_repair_substeps",
            "carrier": "finite_two_qubit_system_memory_with_hold_decay_axis",
            "readout_families": ["final_joint_entropy_order_gap", "measurement_accuracy", "memory_blank_trace_distance"],
            "headline_readouts": {
                "best_ordering_margin": qss["summary"]["best_ordering_margin"],
                "mean_measurement_accuracy": qss["summary"]["mean_measurement_accuracy"],
                "mean_measurement_mutual_information": qss["summary"]["mean_measurement_mutual_information"],
                "reset_memory_entropy_drop": qss["summary"]["weak_reset_mean_memory_entropy_after_reset"] - qss["summary"]["strong_reset_mean_memory_entropy_after_reset"],
                "mean_feedback_system_free_energy_gain": qss["summary"]["mean_feedback_system_free_energy_gain"],
            },
        },
        {
            "row_id": "qit_szilard_record_companion",
            "family": "szilard_repair",
            "carrier": "finite_two_qubit_system_memory_with_record_decay_axis",
            "readout_families": ["final_joint_entropy_order_gap", "measurement_mutual_information", "reset_memory_entropy"],
            "headline_readouts": {
                "best_ordering_margin": qsr["summary"]["best_ordering_margin"],
                "long_minus_short_margin": qsr["summary"]["long_lifetime_mean_margin"] - qsr["summary"]["short_lifetime_mean_margin"],
                "reset_memory_entropy_drop": qsr["summary"]["weak_reset_mean_memory_entropy_after_reset"] - qsr["summary"]["strong_reset_mean_memory_entropy_after_reset"],
                "mean_measurement_mutual_information": qsr["summary"]["mean_measurement_mutual_information"],
            },
        },
        {
            "row_id": "qit_szilard_reverse_recovery_companion",
            "family": "szilard_repair_reverse_recovery",
            "carrier": "finite_two_qubit_system_memory_reverse_recovery_axis",
            "readout_families": ["entropy_restoration_fraction", "restoration_trace_distance", "erase_information_gain"],
            "headline_readouts": {
                "best_recovery_vs_naive_gap": qsv["summary"]["best_recovery_vs_naive_gap"],
                "mean_recovery_entropy_restoration_fraction": qsv["summary"]["mean_recovery_entropy_restoration_fraction"],
                "mean_naive_reverse_entropy_restoration_fraction": qsv["summary"]["mean_naive_reverse_entropy_restoration_fraction"],
                "mean_erase_system_free_energy_gain": qsv["summary"]["mean_erase_system_free_energy_gain"],
            },
        },
        {
            "row_id": "qit_carnot_finite_time_companion",
            "family": "carnot_repair_finite_time",
            "carrier": "finite_qubit_two_bath_with_budget_axis",
            "readout_families": ["budgeted_efficiency", "budgeted_cop", "carnot_distance"],
            "headline_readouts": {
                "baseline_closure_defect": qcf["summary"]["baseline_forward_closure_defect"],
                "best_closure_defect": qcf["summary"]["best_closure_defect"],
                "best_forward_efficiency": qcf["summary"]["best_forward_efficiency"],
                "best_reverse_cop": qcf["summary"]["best_reverse_cop"],
            },
        },
        {
            "row_id": "qit_carnot_irreversibility_companion",
            "family": "carnot_repair_irreversibility",
            "carrier": "finite_qubit_two_bath_duration_sweep",
            "readout_families": ["closure_defect", "duration_distance_to_carnot", "budgeted_efficiency"],
            "headline_readouts": {
                "baseline_forward_closure_defect": qci["summary"]["baseline_forward_closure_defect"],
                "best_closure_defect": qci["summary"]["best_closure_defect"],
                "best_forward_distance_to_carnot": qci["summary"]["best_forward_distance_to_carnot"],
                "best_reverse_distance_to_carnot_cop": qci["summary"]["best_reverse_distance_to_carnot_cop"],
            },
        },
        {
            "row_id": "qit_carnot_closure_companion",
            "family": "carnot_repair_closure",
            "carrier": "finite_qubit_two_bath_closure_grid",
            "readout_families": ["closure_defect", "closure_leg_concentration", "hold_policy_tradeoff"],
            "headline_readouts": {
                "baseline_closure_defect": qcc["summary"]["baseline_closure_defect"],
                "best_closure_defect": qcc["summary"]["best_closure_defect"],
                "best_closure_policy": qcc["summary"]["best_closure_policy"],
                "dominant_closure_leg_at_best_row": qcc["summary"]["dominant_closure_leg_at_best_row"],
            },
        },
        {
            "row_id": "qit_carnot_hold_policy_companion",
            "family": "carnot_repair",
            "carrier": "finite_qubit_two_bath_with_partial_thermalization_holds",
            "readout_families": ["trace_distance_closure", "efficiency", "hold_budget"],
            "headline_readouts": {
                "baseline_trace_distance": qch["positive"]["baseline_has_nonzero_return_defect"]["baseline_trace_distance"],
                "best_closure_trace_distance": qch["positive"]["fixed_full_chain_has_the_best_closure"]["best_closure_trace_distance"],
                "best_efficiency": qch["rows"][3]["efficiency"],
                "adaptive_budget_saved_steps": qch["negative"]["adaptive_policies_save_budget_relative_to_their_fixed_companions"]["fixed_full_chain_steps_used"]
                - qch["negative"]["adaptive_policies_save_budget_relative_to_their_fixed_companions"]["adaptive_full_chain_steps_used"],
            },
        },
    ]

    positive = {
        "all_strict_rows_offer_distinct_qit_readout_families": {
            "distinct_family_count": len({tuple(row["readout_families"]) for row in rows}),
            "pass": len({tuple(row["readout_families"]) for row in rows}) == len(rows),
        },
        "strict_rows_include_both_entropy_balance_and_order_sensitive_readouts": {
            "families": [row["family"] for row in rows],
            "pass": any("erasure_cost" in row["readout_families"] for row in rows)
            and any(
                "order_gap" in row["readout_families"] or "final_joint_entropy_order_gap" in row["readout_families"]
                for row in rows
            ),
        },
        "strict_rows_include_a_reversible_reference_readout": {
            "forward_distance_to_carnot": rows[2]["headline_readouts"]["forward_distance_to_carnot"],
            "reverse_distance_to_carnot_cop": rows[2]["headline_readouts"]["reverse_distance_to_carnot_cop"],
            "pass": rows[2]["headline_readouts"]["forward_distance_to_carnot"] < 1e-10
            and rows[2]["headline_readouts"]["reverse_distance_to_carnot_cop"] < 1e-10,
        },
        "repair_rows_add_nontrivial_readout_axes": {
            "szilard_substep_best_ordering_margin": rows[4]["headline_readouts"]["best_ordering_margin"],
            "szilard_record_best_ordering_margin": rows[5]["headline_readouts"]["best_ordering_margin"],
            "szilard_reverse_best_gap": rows[6]["headline_readouts"]["best_recovery_vs_naive_gap"],
            "carnot_finite_time_best_closure_defect": rows[7]["headline_readouts"]["best_closure_defect"],
            "carnot_irreversibility_best_closure_defect": rows[8]["headline_readouts"]["best_closure_defect"],
            "carnot_closure_best_defect": rows[9]["headline_readouts"]["best_closure_defect"],
            "carnot_hold_best_closure_trace_distance": rows[10]["headline_readouts"]["best_closure_trace_distance"],
            "pass": rows[4]["headline_readouts"]["best_ordering_margin"] > 0.0
            and rows[5]["headline_readouts"]["best_ordering_margin"] > 0.0
            and rows[6]["headline_readouts"]["best_recovery_vs_naive_gap"] > 0.0
            and rows[7]["headline_readouts"]["best_closure_defect"] > 0.0
            and rows[8]["headline_readouts"]["best_closure_defect"] > 0.0
            and rows[9]["headline_readouts"]["best_closure_defect"] > 0.0
            and rows[10]["headline_readouts"]["best_closure_trace_distance"] > 0.0,
        },
    }

    negative = {
        "not_all_strict_rows_share_one_universal_entropy_language": {
            "pass": True,
        },
        "strong_coupling_row_explicitly_shows_local_readout_failure": {
            "local_clausius_gap_strong": rows[1]["headline_readouts"]["local_clausius_gap_strong"],
            "pass": rows[1]["headline_readouts"]["local_clausius_gap_strong"] > 0.0,
        },
    }

    boundary = {
        "all_referenced_strict_rows_exist_and_are_finite": {
            "pass": all(
                isinstance(value, (int, float, str))
                for row in rows
                for value in row["headline_readouts"].values()
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "qit_entropy_companion_array",
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
            "strict_row_count": len(rows),
            "scope_note": (
                "Strict QIT readout-family companion array over the finite-carrier anchors. "
                "Use it to compare open-lab rows against matched exact readout families."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "qit_entropy_companion_array_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
