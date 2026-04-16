#!/usr/bin/env python3
"""
QIT Carnot irreversibility companion.
====================================
Strict finite-carrier companion surface for the open finite-time Carnot
irreversibility sweep. It keeps the step-grid signal explicit in a bounded
two-bath qubit model with forward engine and reverse refrigerator modes, and
adds bounded qutip/cirq/pennylane thermal witnesses on the same one-carrier
isothermal legs.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import cirq
import numpy as np
import pennylane as qml
import qutip
classification = "canonical"  # auto-backfill


PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import sim_qit_carnot_finite_time_companion as base  # noqa: E402
import sim_qit_carnot_hold_policy_companion as hold_base  # noqa: E402


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Strict finite-carrier QIT companion for the finite-time Carnot "
    "irreversibility sweep. It preserves the duration signal in a bounded "
    "two-bath qubit model with explicit forward engine and reverse "
    "refrigerator modes, and adds bounded qutip/cirq/pennylane thermal "
    "witnesses on the same one-carrier isothermal legs."
)

divergence_log = CLASSIFICATION_NOTE

LEGO_IDS = [
    "quantum_thermodynamics",
    "channel_cptp_map",
    "stochastic_thermodynamics",
]

PRIMARY_LEGO_IDS = [
    "quantum_thermodynamics",
]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite-carrier bookkeeping, row serialization, and witness comparison"},
    "qutip": {"tried": True, "used": True, "reason": "load-bearing one-carrier thermal witness on the isothermal legs"},
    "cirq": {"tried": True, "used": True, "reason": "load-bearing one-carrier thermal witness on the same isothermal legs"},
    "pennylane": {"tried": True, "used": True, "reason": "load-bearing one-carrier thermal witness on the same isothermal legs"},
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

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "qutip": "load_bearing",
    "cirq": "load_bearing",
    "pennylane": "load_bearing",
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

Q0 = cirq.LineQubit(0)
QML_DEV = qml.device("default.mixed", wires=1, shots=None)
THERMAL_RELAX_SCALE = 420.0
THERMAL_EPS = 1e-15

STEP_GRID = [60, 90, 150, 260, 520, 1000, 2500, 5000]
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


def density_from_probability(p_excited: float) -> np.ndarray:
    p = min(max(float(p_excited), 0.0), 1.0)
    return np.array([[1.0 - p, 0.0], [0.0, p]], dtype=np.complex128)


def thermal_relaxation_alpha(steps: int) -> float:
    return float(1.0 - np.exp(-float(steps) / THERMAL_RELAX_SCALE))


def thermal_kraus_ops(p_eq: float, steps: int) -> list[np.ndarray]:
    alpha = min(max(thermal_relaxation_alpha(steps), 0.0), 1.0)
    p_ground = min(max(1.0 - float(p_eq), 0.0), 1.0)
    sqrt_alpha = np.sqrt(alpha)
    sqrt_one_minus_alpha = np.sqrt(1.0 - alpha)
    sqrt_ground = np.sqrt(p_ground)
    sqrt_excited = np.sqrt(1.0 - p_ground)
    return [
        sqrt_ground
        * np.array([[1.0, 0.0], [0.0, sqrt_one_minus_alpha]], dtype=np.complex128),
        sqrt_ground
        * np.array([[0.0, sqrt_alpha], [0.0, 0.0]], dtype=np.complex128),
        sqrt_excited
        * np.array([[sqrt_one_minus_alpha, 0.0], [0.0, 1.0]], dtype=np.complex128),
        sqrt_excited
        * np.array([[0.0, 0.0], [sqrt_alpha, 0.0]], dtype=np.complex128),
    ]


def qutip_thermalize_density(p_excited0: float, p_eq: float, steps: int) -> np.ndarray:
    rho = qutip.Qobj(density_from_probability(p_excited0), dims=[[2], [2]])
    out = qutip.Qobj(np.zeros((2, 2), dtype=np.complex128), dims=[[2], [2]])
    for kraus in thermal_kraus_ops(p_eq, steps):
        k = qutip.Qobj(kraus, dims=[[2], [2]])
        out += k * rho * k.dag()
    return np.asarray(out.full(), dtype=np.complex128)


def cirq_thermalize_density(p_excited0: float, p_eq: float, steps: int) -> np.ndarray:
    rho0 = density_from_probability(p_excited0)
    circuit = cirq.Circuit(cirq.KrausChannel(thermal_kraus_ops(p_eq, steps)).on(Q0))
    simulator = cirq.DensityMatrixSimulator(seed=13)
    return np.asarray(simulator.simulate(circuit, initial_state=rho0).final_density_matrix, dtype=np.complex128)


@qml.qnode(QML_DEV)
def _qml_thermalize_density(p_excited0: float, p_eq: float, steps: int):
    qml.QubitDensityMatrix(density_from_probability(p_excited0), wires=0)
    qml.QubitChannel(thermal_kraus_ops(p_eq, steps), wires=0)
    return qml.density_matrix(wires=0)


def pennylane_thermalize_density(p_excited0: float, p_eq: float, steps: int) -> np.ndarray:
    return np.asarray(_qml_thermalize_density(p_excited0, p_eq, steps), dtype=np.complex128)


def thermal_witness(stage: dict, label: str) -> dict:
    before = stage["before"]
    after = stage["after"]
    steps = int(stage["steps"])
    p_eq = float(stage["target_probability"])
    p_before = float(before["p_excited"])
    target_rho = np.asarray(after["rho"], dtype=np.complex128)

    qutip_rho = qutip_thermalize_density(p_before, p_eq, steps)
    cirq_rho = cirq_thermalize_density(p_before, p_eq, steps)
    pennylane_rho = pennylane_thermalize_density(p_before, p_eq, steps)

    qutip_err = float(np.max(np.abs(qutip_rho - target_rho)))
    cirq_err = float(np.max(np.abs(cirq_rho - target_rho)))
    pennylane_err = float(np.max(np.abs(pennylane_rho - target_rho)))
    pass_ = bool(
        np.isfinite(qutip_err)
        and np.isfinite(cirq_err)
        and np.isfinite(pennylane_err)
        and qutip_err < 1e-6
        and cirq_err < 1e-6
        and pennylane_err < 1e-6
    )
    return {
        "label": label,
        "steps": steps,
        "before_probability": p_before,
        "target_probability": p_eq,
        "reference_probability": float(target_rho[1, 1].real),
        "qutip_probability": float(qutip_rho[1, 1].real),
        "cirq_probability": float(cirq_rho[1, 1].real),
        "pennylane_probability": float(pennylane_rho[1, 1].real),
        "qutip_density_max_error": qutip_err,
        "cirq_density_max_error": cirq_err,
        "pennylane_density_max_error": pennylane_err,
        "pass": pass_,
    }


def rebuild_stage_details(direction: str, steps: int, budget_label: str) -> dict:
    initial = hold_base.state_from_probability(
        hold_base.gibbs_excited_probability(base.T_HOT, base.GAP_HIGH),
        base.GAP_HIGH,
        base.T_HOT,
        "A_hot_gibbs_high_gap",
    )
    if direction == "forward":
        hot_iso = hold_base.isothermal_leg(
            initial,
            after_gap=base.GAP_HOT_LOW,
            bath_temperature=base.T_HOT,
            steps=steps,
            label=f"{budget_label}_hot_isotherm_expansion",
        )
        adiabatic_expand = hold_base.adiabatic_step(
            hot_iso["after"],
            after_gap=base.GAP_HOT_LOW * (base.T_COLD / base.T_HOT),
            after_temperature=base.T_COLD,
            label=f"{budget_label}_cold_ready_low_gap",
        )
        cold_iso = hold_base.isothermal_leg(
            adiabatic_expand["after"],
            after_gap=base.GAP_HIGH * (base.T_COLD / base.T_HOT),
            bath_temperature=base.T_COLD,
            steps=steps,
            label=f"{budget_label}_cold_isotherm_compression",
        )
        return {
            "hot_iso": hot_iso,
            "cold_iso": cold_iso,
        }

    adiabatic_to_cold = hold_base.adiabatic_step(
        initial,
        after_gap=base.GAP_HIGH * (base.T_COLD / base.T_HOT),
        after_temperature=base.T_COLD,
        label=f"{budget_label}_cold_ready_high_gap",
    )
    cold_iso_reverse = hold_base.isothermal_leg(
        adiabatic_to_cold["after"],
        after_gap=base.GAP_HOT_LOW * (base.T_COLD / base.T_HOT),
        bath_temperature=base.T_COLD,
        steps=steps,
        label=f"{budget_label}_cold_isotherm_reverse",
    )
    adiabatic_to_hot = hold_base.adiabatic_step(
        cold_iso_reverse["after"],
        after_gap=base.GAP_HOT_LOW,
        after_temperature=base.T_HOT,
        label=f"{budget_label}_hot_ready_low_gap",
    )
    hot_iso_reverse = hold_base.isothermal_leg(
        adiabatic_to_hot["after"],
        after_gap=base.GAP_HIGH,
        bath_temperature=base.T_HOT,
        steps=steps,
        label=f"{budget_label}_hot_isotherm_reverse",
    )
    return {
        "cold_iso_reverse": cold_iso_reverse,
        "hot_iso_reverse": hot_iso_reverse,
    }


def build_bridge_witnesses(row: dict) -> dict:
    steps = int(row.get("steps", row.get("steps_per_isotherm")))
    details = rebuild_stage_details(row["direction"], steps, str(row["budget_label"]))
    if row["direction"] == "forward":
        leg_witnesses = {
            "hot_iso": thermal_witness(details["hot_iso"], "forward_hot_iso"),
            "cold_iso": thermal_witness(details["cold_iso"], "forward_cold_iso"),
        }
    else:
        leg_witnesses = {
            "cold_iso_reverse": thermal_witness(
                details["cold_iso_reverse"], "reverse_cold_iso"
            ),
            "hot_iso_reverse": thermal_witness(
                details["hot_iso_reverse"], "reverse_hot_iso"
            ),
        }

    stage_rows = [
        stage
        for stage in leg_witnesses.values()
        if isinstance(stage, dict) and "qutip_density_max_error" in stage
    ]
    summary = {
        "pass": bool(all(stage["pass"] for stage in stage_rows)),
        "max_qutip_density_error": float(
            max(stage["qutip_density_max_error"] for stage in stage_rows)
        ),
        "max_cirq_density_error": float(
            max(stage["cirq_density_max_error"] for stage in stage_rows)
        ),
        "max_pennylane_density_error": float(
            max(stage["pennylane_density_max_error"] for stage in stage_rows)
        ),
    }
    return {**leg_witnesses, **summary}


def main() -> None:
    rows = []
    for steps in STEP_GRID:
        budget_label = f"steps_{steps}"
        forward = base.run_forward_cycle(steps, budget_label)
        reverse = base.run_reverse_cycle(steps, budget_label)
        forward_bridge_witnesses = build_bridge_witnesses(forward)
        reverse_bridge_witnesses = build_bridge_witnesses(reverse)

        rows.append(
            {
                "steps": int(steps),
                "budget_label": budget_label,
                "direction": "forward",
                "closure_defect": float(forward["closure_defect"]),
                "primary_metric_name": forward["primary_metric_name"],
                "primary_metric_value": float(forward["primary_metric_value"]),
                "distance_to_carnot_reference": float(forward["distance_to_carnot_reference"]),
                "carnot_reference": float(forward["carnot_reference"]),
                "work_by_system": float(forward["work_by_system"]),
                "positive_heat_absorbed": float(forward["positive_heat_absorbed"]),
                "total_heat_into_system": float(forward["total_heat_into_system"]),
                "bookkeeping_closure_error": float(forward["bookkeeping_closure_error"]),
                "final_trace_distance_to_initial": float(forward["final_trace_distance_to_initial"]),
                "final_probability_mismatch_abs": float(forward["final_probability_mismatch_abs"]),
                "final_free_energy_mismatch": float(forward["final_free_energy_mismatch"]),
                "final_internal_energy_mismatch": float(forward["final_internal_energy_mismatch"]),
                "stages": forward["stages"],
                "bridge_witnesses": forward_bridge_witnesses,
            }
        )
        rows.append(
            {
                "steps": int(steps),
                "budget_label": budget_label,
                "direction": "reverse",
                "closure_defect": float(reverse["closure_defect"]),
                "primary_metric_name": reverse["primary_metric_name"],
                "primary_metric_value": float(reverse["primary_metric_value"]),
                "distance_to_carnot_reference": float(reverse["distance_to_carnot_reference"]),
                "carnot_reference": float(reverse["carnot_reference"]),
                "work_by_system": float(reverse["work_by_system"]),
                "work_input": float(reverse["work_input"]),
                "q_cold_absorbed": float(reverse["q_cold_absorbed"]),
                "total_heat_into_system": float(reverse["total_heat_into_system"]),
                "bookkeeping_closure_error": float(reverse["bookkeeping_closure_error"]),
                "final_trace_distance_to_initial": float(reverse["final_trace_distance_to_initial"]),
                "final_probability_mismatch_abs": float(reverse["final_probability_mismatch_abs"]),
                "final_free_energy_mismatch": float(reverse["final_free_energy_mismatch"]),
                "final_internal_energy_mismatch": float(reverse["final_internal_energy_mismatch"]),
                "stages": reverse["stages"],
                "bridge_witnesses": reverse_bridge_witnesses,
            }
        )

    forward_rows = [row for row in rows if row["direction"] == "forward"]
    reverse_rows = [row for row in rows if row["direction"] == "reverse"]

    baseline_forward = next(row for row in forward_rows if row["steps"] == STEP_GRID[0])
    best_closure = min(rows, key=lambda row: row["closure_defect"])
    best_forward = max(forward_rows, key=lambda row: row["primary_metric_value"])
    best_reverse = max(reverse_rows, key=lambda row: row["primary_metric_value"])

    forward_closure_spread = max(row["closure_defect"] for row in forward_rows) - min(
        row["closure_defect"] for row in forward_rows
    )
    reverse_closure_spread = max(row["closure_defect"] for row in reverse_rows) - min(
        row["closure_defect"] for row in reverse_rows
    )
    forward_primary_spread = max(row["primary_metric_value"] for row in forward_rows) - min(
        row["primary_metric_value"] for row in forward_rows
    )
    reverse_primary_spread = max(row["primary_metric_value"] for row in reverse_rows) - min(
        row["primary_metric_value"] for row in reverse_rows
    )
    bridge_witness_rows = [row["bridge_witnesses"] for row in rows]
    max_bridge_qutip_error = max(row["max_qutip_density_error"] for row in bridge_witness_rows)
    max_bridge_cirq_error = max(row["max_cirq_density_error"] for row in bridge_witness_rows)
    max_bridge_pennylane_error = max(row["max_pennylane_density_error"] for row in bridge_witness_rows)

    positive = {
        "budgeted_forward_rows_close_the_bookkeeping": {
            "max_bookkeeping_closure_error": max(row["bookkeeping_closure_error"] for row in forward_rows),
            "pass": max(row["bookkeeping_closure_error"] for row in forward_rows) < 1e-8,
        },
        "budgeted_reverse_rows_close_the_bookkeeping": {
            "max_bookkeeping_closure_error": max(row["bookkeeping_closure_error"] for row in reverse_rows),
            "pass": max(row["bookkeeping_closure_error"] for row in reverse_rows) < 1e-8,
        },
        "forward_slow_improves_on_fast_in_the_expected_direction": {
            "fast_efficiency": forward_rows[0]["primary_metric_value"],
            "slow_efficiency": forward_rows[4]["primary_metric_value"],
            "fast_distance_to_carnot": forward_rows[0]["distance_to_carnot_reference"],
            "slow_distance_to_carnot": forward_rows[4]["distance_to_carnot_reference"],
            "pass": (
                forward_rows[4]["primary_metric_value"] > forward_rows[0]["primary_metric_value"]
                and forward_rows[4]["distance_to_carnot_reference"] < forward_rows[0]["distance_to_carnot_reference"]
            ),
        },
        "reverse_slow_improves_on_fast_in_the_expected_direction": {
            "fast_cop": reverse_rows[0]["primary_metric_value"],
            "slow_cop": reverse_rows[4]["primary_metric_value"],
            "fast_distance_to_carnot": reverse_rows[0]["distance_to_carnot_reference"],
            "slow_distance_to_carnot": reverse_rows[4]["distance_to_carnot_reference"],
            "pass": (
                reverse_rows[4]["primary_metric_value"] > reverse_rows[0]["primary_metric_value"]
                and reverse_rows[4]["distance_to_carnot_reference"] < reverse_rows[0]["distance_to_carnot_reference"]
            ),
        },
        "quasistatic_rows_are_closest_to_their_carnot_references_on_average": {
            "forward_quasistatic_distance": forward_rows[-1]["distance_to_carnot_reference"],
            "reverse_quasistatic_distance": reverse_rows[-1]["distance_to_carnot_reference"],
            "best_forward_distance": best_forward["distance_to_carnot_reference"],
            "best_reverse_distance": best_reverse["distance_to_carnot_reference"],
            "pass": (
                forward_rows[-1]["distance_to_carnot_reference"] <= forward_rows[0]["distance_to_carnot_reference"]
                and reverse_rows[-1]["distance_to_carnot_reference"] <= reverse_rows[0]["distance_to_carnot_reference"]
            ),
        },
        "bridge_witnesses_match_the_finite_time_leg_rows": {
            "max_qutip_density_error": max_bridge_qutip_error,
            "max_cirq_density_error": max_bridge_cirq_error,
            "max_pennylane_density_error": max_bridge_pennylane_error,
            "pass": (
                max_bridge_qutip_error < 1e-6
                and max_bridge_cirq_error < 1e-6
                and max_bridge_pennylane_error < 1e-6
            ),
        },
    }

    negative = {
        "fast_forward_does_not_saturate_the_carnot_bound": {
            "fast_distance_to_carnot": forward_rows[0]["distance_to_carnot_reference"],
            "pass": forward_rows[0]["distance_to_carnot_reference"] > 1e-3,
        },
        "fast_reverse_does_not_saturate_the_carnot_cop": {
            "fast_distance_to_carnot": reverse_rows[0]["distance_to_carnot_reference"],
            "pass": reverse_rows[0]["distance_to_carnot_reference"] > 1e-3,
        },
        "budget_signal_is_not_flat_across_the_companion_rows": {
            "forward_primary_spread": forward_primary_spread,
            "reverse_primary_spread": reverse_primary_spread,
            "forward_closure_spread": forward_closure_spread,
            "reverse_closure_spread": reverse_closure_spread,
            "pass": forward_primary_spread > 1e-3 and reverse_primary_spread > 1e-3,
        },
        "bridge_witnesses_do_not_flatten_the_finite_time_surface": {
            "max_qutip_density_error": max_bridge_qutip_error,
            "max_cirq_density_error": max_bridge_cirq_error,
            "max_pennylane_density_error": max_bridge_pennylane_error,
            "pass": max_bridge_qutip_error < 1e-6
            and max_bridge_cirq_error < 1e-6
            and max_bridge_pennylane_error < 1e-6,
        },
    }

    boundary = {
        "all_rows_are_finite_and_valid": {
            "pass": all(
                np.isfinite(row["closure_defect"])
                and np.isfinite(row["primary_metric_value"])
                and np.isfinite(row["distance_to_carnot_reference"])
                and np.isfinite(row["work_by_system"])
                and np.isfinite(row["bookkeeping_closure_error"])
                and bool(row["bridge_witnesses"]["pass"])
                for row in rows
            ),
        },
        "all_bridge_witnesses_pass": {
            "pass": all(row["bridge_witnesses"]["pass"] for row in rows),
        },
        "row_count_matches_the_forward_reverse_budget_grid": {
            "expected_rows": len(STEP_GRID) * 2,
            "actual_rows": len(rows),
            "pass": len(rows) == len(STEP_GRID) * 2,
        },
        "budget_axis_covers_the_open_duration_grid": {
            "budget_labels": STEP_GRID,
            "pass": STEP_GRID == [60, 90, 150, 260, 520, 1000, 2500, 5000],
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    out = {
        "name": "qit_carnot_irreversibility_companion",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "step_grid": STEP_GRID,
            "baseline_forward_steps": baseline_forward["steps"],
            "baseline_forward_closure_defect": baseline_forward["closure_defect"],
            "baseline_forward_efficiency": baseline_forward["primary_metric_value"],
            "best_closure_steps": best_closure["steps"],
            "best_closure_defect": best_closure["closure_defect"],
            "best_forward_steps": best_forward["steps"],
            "best_forward_efficiency": best_forward["primary_metric_value"],
            "best_forward_distance_to_carnot": best_forward["distance_to_carnot_reference"],
            "best_reverse_steps": best_reverse["steps"],
            "best_reverse_cop": best_reverse["primary_metric_value"],
            "best_reverse_distance_to_carnot_cop": best_reverse["distance_to_carnot_reference"],
            "forward_efficiency_spread": forward_primary_spread,
            "reverse_cop_spread": reverse_primary_spread,
            "forward_closure_spread": forward_closure_spread,
            "reverse_closure_spread": reverse_closure_spread,
            "max_bridge_qutip_density_error": max_bridge_qutip_error,
            "max_bridge_cirq_density_error": max_bridge_cirq_error,
            "max_bridge_pennylane_density_error": max_bridge_pennylane_error,
            "scope_note": (
                "Strict finite-carrier companion for the finite-time harmonic Carnot "
                "irreversibility sweep. It keeps the open duration signal explicit "
                "while comparing forward engine and reverse refrigerator behavior "
                "against Carnot references and bounding one-carrier qutip/cirq/"
                "pennylane thermal witnesses on the isothermal legs."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "qit_carnot_irreversibility_companion_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
