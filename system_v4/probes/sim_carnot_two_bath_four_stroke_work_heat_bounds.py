#!/usr/bin/env python3
"""Classical four-stroke Carnot-cycle calibration with graveyards."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
from pathlib import Path

import numpy as np


NAME = "carnot_two_bath_four_stroke_work_heat_bounds"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "computes bounded scalar heat/work/efficiency cycle and graveyard controls",
    }
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def carnot_cycle(th: float, tc: float, delta_s: float) -> dict[str, float]:
    q_hot = th * delta_s
    q_cold = -tc * delta_s
    work_out = q_hot + q_cold
    eta = work_out / q_hot if q_hot else 0.0
    eta_bound = 1.0 - tc / th
    return {
        "T_hot": float(th),
        "T_cold": float(tc),
        "delta_entropy": float(delta_s),
        "Q_hot": float(q_hot),
        "Q_cold": float(q_cold),
        "W_out": float(work_out),
        "eta": float(eta),
        "eta_bound": float(eta_bound),
    }


def reversed_cycle(th: float, tc: float, delta_s: float) -> dict[str, float]:
    forward = carnot_cycle(th, tc, delta_s)
    return {
        "W_out": float(-forward["W_out"]),
        "Q_hot": float(-forward["Q_hot"]),
        "Q_cold": float(-forward["Q_cold"]),
    }


def run_positive() -> dict[str, object]:
    cycle = carnot_cycle(600.0, 300.0, 1.25)
    return {
        "four_stroke_cycle": cycle,
        "work_positive": bool(cycle["W_out"] > 0.0),
        "efficiency_matches_bound": bool(np.isclose(cycle["eta"], cycle["eta_bound"])),
        "heat_conservation": bool(np.isclose(cycle["W_out"], cycle["Q_hot"] + cycle["Q_cold"])),
    }


def run_negative() -> dict[str, object]:
    same_bath = carnot_cycle(400.0, 400.0, 1.25)
    no_entropy_change = carnot_cycle(600.0, 300.0, 0.0)
    reverse = reversed_cycle(600.0, 300.0, 1.25)
    super_bound_claim = 0.75
    bound = carnot_cycle(600.0, 300.0, 1.25)["eta_bound"]
    return {
        "same_bath_zero_work": bool(np.isclose(same_bath["W_out"], 0.0)),
        "no_entropy_change_zero_work": bool(np.isclose(no_entropy_change["W_out"], 0.0)),
        "reversed_cycle_consumes_work": bool(reverse["W_out"] < 0.0),
        "super_bound_claim_rejected": bool(super_bound_claim > bound),
        "graveyard_values": {
            "same_bath": same_bath,
            "no_entropy_change": no_entropy_change,
            "reversed": reverse,
            "super_bound_claim": super_bound_claim,
            "bound": bound,
        },
    }


def run_parameter_sweep() -> dict[str, object]:
    cases = [
        carnot_cycle(th, tc, delta_s)
        for th, tc in [(450.0, 300.0), (600.0, 300.0), (900.0, 450.0)]
        for delta_s in [0.25, 1.0, 2.0]
    ]
    forward_bounds_hold = all(
        row["T_hot"] > row["T_cold"] > 0.0
        and row["delta_entropy"] >= 0.0
        and row["W_out"] >= 0.0
        and row["eta"] <= row["eta_bound"] + 1e-12
        for row in cases
    )
    return {
        "case_count": len(cases),
        "forward_bounds_hold": bool(forward_bounds_hold),
        "cases": cases,
    }


def run_boundary() -> dict[str, object]:
    equal_temperature = carnot_cycle(500.0, 500.0, 1.0)
    cold_near_zero = carnot_cycle(500.0, 1e-9, 1.0)
    return {
        "equal_temperature_eta_zero": bool(np.isclose(equal_temperature["eta"], 0.0)),
        "cold_near_zero_eta_near_one": bool(np.isclose(cold_near_zero["eta"], 1.0)),
        "equal_temperature": equal_temperature,
        "cold_near_zero": cold_near_zero,
    }


def main() -> int:
    positive = run_positive()
    negative = run_negative()
    parameter_sweep = run_parameter_sweep()
    boundary = run_boundary()
    all_pass = (
        positive["work_positive"]
        and positive["efficiency_matches_bound"]
        and positive["heat_conservation"]
        and negative["same_bath_zero_work"]
        and negative["no_entropy_change_zero_work"]
        and negative["reversed_cycle_consumes_work"]
        and negative["super_bound_claim_rejected"]
        and parameter_sweep["forward_bounds_hold"]
        and boundary["equal_temperature_eta_zero"]
        and boundary["cold_near_zero_eta_near_one"]
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": bool(all_pass),
        "claim_ceiling": (
            "classical reversible two-bath four-stroke cycle calibration only; "
            "no QIT, GStack, axis, bridge, nonclassical, or target-system claim"
        ),
        "next_lego_target": "work_heat_cycle_calibration_fixture",
        "promotion_condition": (
            "May only support later calibration planning after a non-scalar bath/dynamics formulation "
            "reproduces these bounds with the same graveyards."
        ),
        "demotion_condition": (
            "Demote if same-bath or no-entropy-change graveyards produce work, if reversed direction "
            "does not consume work, or if efficiency exceeds the Carnot bound."
        ),
        "blocked_until": "blocked from target cycle mechanics until non-scalar stroke dynamics and tool receipts exist",
        "out_of_scope": [
            "No Lindblad evolution.",
            "No Hamiltonian stroke dynamics.",
            "No measurement, feedback, QIT, GStack, axis, bridge, or nonclassical claim.",
        ],
        "divergence_log": (
            "Numpy scalar thermodynamic bookkeeping is a classical calibration baseline. "
            "It checks cycle accounting and graveyards but cannot prove target-system mechanics."
        ),
        "operation_sequence": [
            "hot isothermal heat absorption Q_hot = T_hot * delta_entropy",
            "adiabatic expansion represented by entropy-preserving work bookkeeping",
            "cold isothermal heat rejection Q_cold = -T_cold * delta_entropy",
            "adiabatic compression closes the scalar state",
        ],
        "carrier_topology": "scalar thermodynamic state with two reservoirs and a closed entropy interval",
        "observable": "Q_hot, Q_cold, W_out, eta, eta_bound, and graveyard booleans",
        "pass_fail_predicate": (
            "W_out > 0, eta equals 1 - T_cold/T_hot, heat accounting closes, and all graveyards collapse or invert"
        ),
        "graveyards": [
            "same-bath cycle gives zero work",
            "zero entropy displacement gives zero work",
            "reversed direction consumes work",
            "super-bound efficiency claim is rejected",
        ],
        "graveyard_companions": [
            {
                "name": "same_bath_zero_work",
                "expected_failure_mode": "thermal asymmetry collapses",
                "predicate": "W_out == 0",
            },
            {
                "name": "no_entropy_change_zero_work",
                "expected_failure_mode": "stroke displacement collapses",
                "predicate": "W_out == 0",
            },
            {
                "name": "reversed_cycle_consumes_work",
                "expected_failure_mode": "direction inverts",
                "predicate": "W_out < 0",
            },
            {
                "name": "super_bound_claim_rejected",
                "expected_failure_mode": "bound violation rejected",
                "predicate": "claimed_eta > eta_bound",
            },
        ],
        "baselines": [
            "closed-form Carnot bound eta = 1 - T_cold/T_hot",
            "scalar heat/work conservation W = Q_hot + Q_cold",
        ],
        "baseline_variants": [
            "closed-form Carnot bound eta = 1 - T_cold/T_hot",
            "scalar heat/work conservation W = Q_hot + Q_cold",
            "finite parameter sweep over T_hot > T_cold > 0 and delta_entropy >= 0",
        ],
        "alternative_formulations": [
            "finite-time irreversible stroke schedule",
            "Lindblad two-bath open-system stroke schedule",
            "Hamiltonian parameter-change work integral",
        ],
        "exact_tool_function_needs": {"numpy": ["isclose"]},
        "tool_function_needs": {"numpy": ["isclose"]},
        "lego_or_coupling_target": "work_heat_cycle_calibration_fixture",
        "lego_coupling_target": "work_heat_cycle_calibration_fixture",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "parameter_sweep": parameter_sweep,
        "boundary": boundary,
        "promotion_allowed": False,
        "pass": bool(all_pass),
    }
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
