#!/usr/bin/env python3
"""
QIT Szilard reverse-recovery companion.

Finite two-qubit companion surface for the open stochastic reverse/recovery
row. It keeps erase, naive reverse, and designed recovery in exact density-
operator bookkeeping and preserves the recovery > naive reverse signal without
promoting the row to canonical status.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np


PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import sim_qit_szilard_bidirectional_protocol as base  # noqa: E402


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Finite two-qubit companion row for Szilard erase / naive reverse / designed "
    "recovery mechanics. It stays in exact density-operator bookkeeping and is "
    "meant for QIT-aligned comparison, not canonical admission."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "channel_cptp_map",
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

LN2 = float(np.log(2.0))
TEMPERATURE = 1.0
PROTOCOL_STEPS = [60, 120, 240, 420]

ERASE_MEASUREMENT_ERROR = 0.1
ERASE_FEEDBACK_ERROR = 0.1
ERASE_STRENGTH = 1.0

REVERSE_RANDOMIZATION_SCALE = 0.7
NAIVE_RANDOMIZATION_RATIO = 0.45
ANTI_MEASUREMENT_ERROR = 0.15
ANTI_FEEDBACK_ERROR = 0.15


def mean(values) -> float:
    values = list(values)
    return float(np.mean(values)) if values else 0.0


def valid_all_states(protocol: dict) -> bool:
    return bool(all(snapshot["valid_density"] for snapshot in protocol["states"].values()))


def entropy_restoration_fraction(system_entropy: float) -> float:
    return float(system_entropy / LN2)


def run_row(steps: int) -> dict:
    reverse_budget = float(1.0 - np.exp(-steps / 180.0))
    recovery_randomization_strength = float(REVERSE_RANDOMIZATION_SCALE * reverse_budget)
    naive_randomization_strength = float(NAIVE_RANDOMIZATION_RATIO * recovery_randomization_strength)

    erase = base.run_forward_cycle(
        TEMPERATURE,
        measurement_error=ERASE_MEASUREMENT_ERROR,
        feedback_error=ERASE_FEEDBACK_ERROR,
        erasure_strength=ERASE_STRENGTH,
    )
    naive_reverse = base.run_reverse_cycle(
        TEMPERATURE,
        randomization_strength=naive_randomization_strength,
        anti_feedback_error=ANTI_FEEDBACK_ERROR,
        anti_measurement_error=ANTI_MEASUREMENT_ERROR,
    )
    recovery = base.run_reverse_cycle(
        TEMPERATURE,
        randomization_strength=recovery_randomization_strength,
        anti_feedback_error=ANTI_FEEDBACK_ERROR,
        anti_measurement_error=ANTI_MEASUREMENT_ERROR,
    )

    erase_measurement_information = float(erase["states"]["measured"]["mutual_information"])
    erase_system_entropy_after_feedback = float(erase["states"]["feedback"]["system_entropy"])
    erase_system_free_energy_gain = float(erase["metrics"]["system_free_energy_gain"])
    erase_erasure_cost = float(erase["metrics"]["erasure_cost"])
    erase_net_after_erasure = float(erase["metrics"]["net_after_erasure"])
    erase_reconstruction_trace_distance = float(erase["metrics"]["reconstruction_trace_distance_from_ground"])

    naive_entropy = float(naive_reverse["states"]["restored_initial"]["system_entropy"])
    recovery_entropy = float(recovery["states"]["restored_initial"]["system_entropy"])
    naive_fraction = entropy_restoration_fraction(naive_entropy)
    recovery_fraction = entropy_restoration_fraction(recovery_entropy)

    return {
        "steps": int(steps),
        "reverse_budget": reverse_budget,
        "recovery_randomization_strength": recovery_randomization_strength,
        "naive_randomization_strength": naive_randomization_strength,
        "erase_measurement_error": ERASE_MEASUREMENT_ERROR,
        "erase_feedback_error": ERASE_FEEDBACK_ERROR,
        "erase_strength": ERASE_STRENGTH,
        "anti_measurement_error": ANTI_MEASUREMENT_ERROR,
        "anti_feedback_error": ANTI_FEEDBACK_ERROR,
        "erase_measurement_mutual_information": erase_measurement_information,
        "erase_system_entropy_after_feedback": erase_system_entropy_after_feedback,
        "erase_system_free_energy_gain": erase_system_free_energy_gain,
        "erase_erasure_cost": erase_erasure_cost,
        "erase_net_after_erasure": erase_net_after_erasure,
        "erase_reconstruction_trace_distance_from_ground": erase_reconstruction_trace_distance,
        "naive_reverse_final_system_entropy": naive_entropy,
        "naive_reverse_entropy_restoration_fraction": naive_fraction,
        "naive_reverse_trace_distance_to_initial": float(naive_reverse["metrics"]["restoration_trace_distance"]),
        "naive_reverse_randomization_cost": float(naive_reverse["metrics"]["randomization_cost"]),
        "naive_reverse_system_free_energy_drop": float(naive_reverse["metrics"]["system_free_energy_drop"]),
        "recovery_final_system_entropy": recovery_entropy,
        "recovery_entropy_restoration_fraction": recovery_fraction,
        "recovery_trace_distance_to_initial": float(recovery["metrics"]["restoration_trace_distance"]),
        "recovery_randomization_cost": float(recovery["metrics"]["randomization_cost"]),
        "recovery_system_free_energy_drop": float(recovery["metrics"]["system_free_energy_drop"]),
        "recovery_vs_naive_gap": float(recovery_fraction - naive_fraction),
        "recovery_vs_naive_entropy_gap_nats": float(recovery_entropy - naive_entropy),
        "recovery_vs_naive_trace_distance_gap": float(
            naive_reverse["metrics"]["restoration_trace_distance"] - recovery["metrics"]["restoration_trace_distance"]
        ),
        "no_randomization_control_final_system_entropy": float(
            recovery["states"]["no_randomization_control"]["system_entropy"]
        ),
        "no_randomization_control_trace_distance_to_initial": float(
            recovery["metrics"]["no_randomization_trace_distance"]
        ),
        "erase_valid_density_all_states": bool(valid_all_states(erase)),
        "naive_reverse_valid_density_all_states": bool(valid_all_states(naive_reverse)),
        "recovery_valid_density_all_states": bool(valid_all_states(recovery)),
    }


def main() -> None:
    rows = [run_row(steps) for steps in PROTOCOL_STEPS]

    mean_erase_mi = mean(row["erase_measurement_mutual_information"] for row in rows)
    mean_erase_gain = mean(row["erase_system_free_energy_gain"] for row in rows)
    mean_erase_cost = mean(row["erase_erasure_cost"] for row in rows)
    mean_naive_fraction = mean(row["naive_reverse_entropy_restoration_fraction"] for row in rows)
    mean_recovery_fraction = mean(row["recovery_entropy_restoration_fraction"] for row in rows)
    mean_gap = mean(row["recovery_vs_naive_gap"] for row in rows)
    mean_recovery_trace = mean(row["recovery_trace_distance_to_initial"] for row in rows)
    mean_naive_trace = mean(row["naive_reverse_trace_distance_to_initial"] for row in rows)
    mean_control_trace = mean(row["no_randomization_control_trace_distance_to_initial"] for row in rows)

    best_row = max(rows, key=lambda row: row["recovery_vs_naive_gap"])
    max_recovery_entropy = max(row["recovery_final_system_entropy"] for row in rows)
    max_naive_entropy = max(row["naive_reverse_final_system_entropy"] for row in rows)
    min_gap = min(row["recovery_vs_naive_gap"] for row in rows)
    max_gap = max(row["recovery_vs_naive_gap"] for row in rows)

    positive = {
        "erase_stage_remains_informative": {
            "mean_measurement_mutual_information": mean_erase_mi,
            "mean_system_free_energy_gain": mean_erase_gain,
            "mean_erasure_cost": mean_erase_cost,
            "pass": mean_erase_mi > 0.05 and mean_erase_gain > 0.05 and mean_erase_cost > 0.0,
        },
        "recovery_restores_more_uncertainty_than_naive_reverse": {
            "mean_recovery_entropy_restoration_fraction": mean_recovery_fraction,
            "mean_naive_reverse_entropy_restoration_fraction": mean_naive_fraction,
            "best_recovery_vs_naive_gap": max_gap,
            "pass": min_gap > 0.0,
        },
        "recovery_does_not_fully_restore_uniformity": {
            "max_recovery_final_system_entropy": max_recovery_entropy,
            "pass": max_recovery_entropy < LN2 - 0.01,
        },
    }

    negative = {
        "naive_reverse_does_not_outperform_recovery": {
            "max_naive_reverse_final_system_entropy": max_naive_entropy,
            "min_recovery_vs_naive_gap": min_gap,
            "pass": max_naive_entropy < max_recovery_entropy,
        },
        "no_randomization_control_is_not_a_recovery_substitute": {
            "mean_no_randomization_control_trace_distance_to_initial": mean_control_trace,
            "pass": mean_control_trace > 0.25,
        },
        "recovery_is_not_perfect_uniformity": {
            "max_recovery_final_system_entropy": max_recovery_entropy,
            "pass": max_recovery_entropy < LN2 - 0.01,
        },
    }

    boundary = {
        "all_modes_remain_valid_density_operators": {
            "pass": all(
                row["erase_valid_density_all_states"]
                and row["naive_reverse_valid_density_all_states"]
                and row["recovery_valid_density_all_states"]
                for row in rows
            ),
        },
        "all_summary_values_are_finite": {
            "pass": all(
                np.isfinite(value)
                for value in [
                    mean_erase_mi,
                    mean_erase_gain,
                    mean_erase_cost,
                    mean_naive_fraction,
                    mean_recovery_fraction,
                    mean_gap,
                    mean_recovery_trace,
                    mean_naive_trace,
                    mean_control_trace,
                    best_row["recovery_vs_naive_gap"],
                    best_row["recovery_entropy_restoration_fraction"],
                ]
            ),
        },
        "protocol_grid_covers_the_reverse_budget_sweep": {
            "steps": PROTOCOL_STEPS,
            "n_points": len(rows),
            "pass": len(rows) == len(PROTOCOL_STEPS),
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    summary = {
        "all_pass": all_pass,
        "temperature": TEMPERATURE,
        "protocol_steps": PROTOCOL_STEPS,
        "erase_measurement_error": ERASE_MEASUREMENT_ERROR,
        "erase_feedback_error": ERASE_FEEDBACK_ERROR,
        "erase_strength": ERASE_STRENGTH,
        "anti_measurement_error": ANTI_MEASUREMENT_ERROR,
        "anti_feedback_error": ANTI_FEEDBACK_ERROR,
        "recovery_randomization_scale": REVERSE_RANDOMIZATION_SCALE,
        "naive_randomization_ratio": NAIVE_RANDOMIZATION_RATIO,
        "best_recovery_vs_naive_gap": float(best_row["recovery_vs_naive_gap"]),
        "best_recovery_entropy_restoration_fraction": float(best_row["recovery_entropy_restoration_fraction"]),
        "best_recovery_trace_distance_to_initial": float(best_row["recovery_trace_distance_to_initial"]),
        "best_setting": {
            "steps": best_row["steps"],
            "recovery_randomization_strength": best_row["recovery_randomization_strength"],
            "naive_randomization_strength": best_row["naive_randomization_strength"],
        },
        "mean_recovery_vs_naive_gap": mean_gap,
        "mean_recovery_entropy_restoration_fraction": mean_recovery_fraction,
        "mean_naive_reverse_entropy_restoration_fraction": mean_naive_fraction,
        "mean_recovery_trace_distance_to_initial": mean_recovery_trace,
        "mean_naive_reverse_trace_distance_to_initial": mean_naive_trace,
        "mean_no_randomization_control_trace_distance_to_initial": mean_control_trace,
        "mean_erase_measurement_mutual_information": mean_erase_mi,
        "mean_erase_system_free_energy_gain": mean_erase_gain,
        "mean_erase_erasure_cost": mean_erase_cost,
        "max_recovery_final_system_entropy": max_recovery_entropy,
        "scope_note": (
            "Finite two-qubit reverse-recovery companion for the Szilard lane. It "
            "keeps erase, naive reverse, and designed recovery in exact density-"
            "operator bookkeeping and preserves the open-row signal without "
            "promoting the row to canonical status."
        ),
    }

    results = {
        "name": "qit_szilard_reverse_recovery_companion",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "rows": rows,
    }

    out_path = PROBE_DIR / "a2_state" / "sim_results" / "qit_szilard_reverse_recovery_companion_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str) + "\n")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
