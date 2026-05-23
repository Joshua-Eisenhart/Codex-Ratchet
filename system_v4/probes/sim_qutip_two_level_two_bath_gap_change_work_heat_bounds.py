#!/usr/bin/env python3
"""QuTiP two-level two-bath gap-change work/heat calibration bounds."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import math
from pathlib import Path

import numpy as np
import qutip
from receipt_boundary import apply_default_receipt_boundary


NAME = "qutip_two_level_two_bath_gap_change_work_heat_bounds"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "builds two-level density carriers, Hamiltonians, thermal states, and energy expectation readouts",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "checks scalar work/heat bounds, graveyard collapses, and density eigenvalue validity",
    },
}
TOOL_INTEGRATION_DEPTH = {"qutip": "load_bearing", "numpy": "supportive"}


def qobj_pairs(obj: qutip.Qobj) -> list[list[list[float]]]:
    matrix = np.asarray(obj.full(), dtype=np.complex128)
    return [[[float(value.real), float(value.imag)] for value in row] for row in matrix]


def hamiltonian(gap: float) -> qutip.Qobj:
    return gap * qutip.ket2dm(qutip.basis(2, 1))


def thermal_state(beta: float, gap: float) -> qutip.Qobj:
    p_excited = 1.0 / (1.0 + math.exp(beta * gap))
    ket0 = qutip.basis(2, 0)
    ket1 = qutip.basis(2, 1)
    return (1.0 - p_excited) * qutip.ket2dm(ket0) + p_excited * qutip.ket2dm(ket1)


def density_ok(rho: qutip.Qobj, tol: float = 1e-10) -> bool:
    matrix = np.asarray(rho.full(), dtype=np.complex128)
    hermitian = np.allclose(matrix, matrix.conjugate().T, atol=tol)
    trace_one = abs(float(rho.tr().real) - 1.0) < tol
    eigs = np.linalg.eigvalsh((matrix + matrix.conjugate().T) / 2.0)
    return bool(hermitian and trace_one and np.all(eigs >= -tol))


def excited_population(rho: qutip.Qobj) -> float:
    return float(qutip.expect(qutip.ket2dm(qutip.basis(2, 1)), rho))


def run_cycle(*, beta_hot: float, beta_cold: float, gap_hot: float, gap_cold: float) -> dict[str, object]:
    hot_state = thermal_state(beta_hot, gap_hot)
    cold_state = thermal_state(beta_cold, gap_cold)
    hot_pop = excited_population(hot_state)
    cold_pop = excited_population(cold_state)
    h_hot = hamiltonian(gap_hot)
    h_cold = hamiltonian(gap_cold)

    energy_hot_state_hot_gap = float(qutip.expect(h_hot, hot_state))
    energy_hot_state_cold_gap = float(qutip.expect(h_cold, hot_state))
    energy_cold_state_cold_gap = float(qutip.expect(h_cold, cold_state))
    energy_cold_state_hot_gap = float(qutip.expect(h_hot, cold_state))

    work_out_expansion = energy_hot_state_hot_gap - energy_hot_state_cold_gap
    heat_cold = energy_cold_state_cold_gap - energy_hot_state_cold_gap
    work_in_compression = energy_cold_state_hot_gap - energy_cold_state_cold_gap
    heat_hot = energy_hot_state_hot_gap - energy_cold_state_hot_gap
    net_work_out = work_out_expansion - work_in_compression
    efficiency = net_work_out / heat_hot if heat_hot > 0 else 0.0
    carnot_bound = 1.0 - beta_hot / beta_cold if beta_cold > 0 else 1.0

    return {
        "beta_hot": beta_hot,
        "beta_cold": beta_cold,
        "gap_hot": gap_hot,
        "gap_cold": gap_cold,
        "hot_excited_population": hot_pop,
        "cold_excited_population": cold_pop,
        "hot_state": qobj_pairs(hot_state),
        "cold_state": qobj_pairs(cold_state),
        "hot_density_ok": density_ok(hot_state),
        "cold_density_ok": density_ok(cold_state),
        "energy_hot_state_hot_gap": energy_hot_state_hot_gap,
        "energy_hot_state_cold_gap": energy_hot_state_cold_gap,
        "energy_cold_state_cold_gap": energy_cold_state_cold_gap,
        "energy_cold_state_hot_gap": energy_cold_state_hot_gap,
        "work_out_expansion": work_out_expansion,
        "work_in_compression": work_in_compression,
        "Q_hot": heat_hot,
        "Q_cold": heat_cold,
        "W_out": net_work_out,
        "efficiency": efficiency,
        "carnot_bound": carnot_bound,
        "energy_accounting_residual": heat_hot + heat_cold - net_work_out,
    }


def run_positive() -> dict[str, object]:
    cycle = run_cycle(beta_hot=0.2, beta_cold=1.0, gap_hot=4.0, gap_cold=2.0)
    return {
        "cycle": cycle,
        "hot_population_exceeds_cold_population": bool(cycle["hot_excited_population"] > cycle["cold_excited_population"]),
        "work_positive": bool(cycle["W_out"] > 0.0),
        "absorbs_hot_heat": bool(cycle["Q_hot"] > 0.0),
        "rejects_cold_heat": bool(cycle["Q_cold"] < 0.0),
        "efficiency_respects_carnot_bound": bool(cycle["efficiency"] <= cycle["carnot_bound"] + 1e-12),
        "energy_accounting_closes": bool(np.isclose(cycle["energy_accounting_residual"], 0.0)),
        "densities_valid": bool(cycle["hot_density_ok"] and cycle["cold_density_ok"]),
    }


def run_graveyards() -> dict[str, object]:
    no_gap_change = run_cycle(beta_hot=0.2, beta_cold=1.0, gap_hot=3.0, gap_cold=3.0)
    matching_scaled_gaps = run_cycle(beta_hot=0.5, beta_cold=1.0, gap_hot=2.0, gap_cold=1.0)
    reversed_temperatures = run_cycle(beta_hot=1.0, beta_cold=0.2, gap_hot=4.0, gap_cold=2.0)
    no_temperature_difference = run_cycle(beta_hot=0.5, beta_cold=0.5, gap_hot=4.0, gap_cold=2.0)
    positive = run_cycle(beta_hot=0.2, beta_cold=1.0, gap_hot=4.0, gap_cold=2.0)
    return {
        "no_gap_change_gives_zero_work": {
            "W_out": no_gap_change["W_out"],
            "passed": bool(np.isclose(no_gap_change["W_out"], 0.0)),
        },
        "matching_scaled_gaps_equalize_populations_and_zero_work": {
            "hot_population": matching_scaled_gaps["hot_excited_population"],
            "cold_population": matching_scaled_gaps["cold_excited_population"],
            "W_out": matching_scaled_gaps["W_out"],
            "passed": bool(
                np.isclose(matching_scaled_gaps["hot_excited_population"], matching_scaled_gaps["cold_excited_population"])
                and np.isclose(matching_scaled_gaps["W_out"], 0.0)
            ),
        },
        "reversed_temperature_assignment_consumes_work": {
            "W_out": reversed_temperatures["W_out"],
            "passed": bool(reversed_temperatures["W_out"] < 0.0),
        },
        "same_temperature_with_gap_change_violates_hot_cold_population_order": {
            "hot_population": no_temperature_difference["hot_excited_population"],
            "cold_population": no_temperature_difference["cold_excited_population"],
            "passed": bool(no_temperature_difference["hot_excited_population"] < no_temperature_difference["cold_excited_population"]),
        },
        "super_carnot_efficiency_claim_rejected": {
            "efficiency": positive["efficiency"],
            "carnot_bound": positive["carnot_bound"],
            "claimed_efficiency": positive["carnot_bound"] + 0.05,
            "passed": bool(positive["efficiency"] <= positive["carnot_bound"] < positive["carnot_bound"] + 0.05),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["hot_population_exceeds_cold_population"]
        and positive["work_positive"]
        and positive["absorbs_hot_heat"]
        and positive["rejects_cold_heat"]
        and positive["efficiency_respects_carnot_bound"]
        and positive["energy_accounting_closes"]
        and positive["densities_valid"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "QuTiP two-level two-bath gap-change work/heat calibration only; this is a reversible finite-carrier "
            "classical baseline for heat/work accounting, not a full Carnot theorem; no QIT, GStack, axis, bridge, "
            "nonclassical, runtime-engine, or target-system admission"
        ),
        "next_lego_target": "work_heat_cycle_calibration_fixture",
        "promotion_condition": (
            "May only support later calibration planning after explicit stroke dynamics, finite-time controls, and "
            "independent tool receipts reproduce compatible heat/work bounds with adjacent graveyards."
        ),
        "demotion_condition": (
            "Demote if density validity fails, if heat/work accounting does not close, if reversed or matched-population "
            "graveyards do not collapse/invert, or if efficiency exceeds the Carnot bound."
        ),
        "blocked_until": "blocked from target cycle mechanics until explicit stroke dynamics and work-reservoir fixtures exist",
        "out_of_scope": [
            "No Lindblad bath thermalization dynamics.",
            "No finite-time irreversibility model.",
            "No measurement, feedback, QIT, GStack, axis, bridge, nonclassical, runtime-engine, or target-system admission.",
        ],
        "divergence_log": (
            "This fixture uses explicit two-level density carriers and Hamiltonian energy readouts, but it still "
            "uses ideal thermal endpoint states rather than simulating the bath strokes."
        ),
        "operation_sequence": [
            "construct two-level thermal density carriers for hot and cold inverse temperatures",
            "construct hot-gap and cold-gap Hamiltonians H = gap * |1><1|",
            "read hot-state energy at hot and cold gaps",
            "read cold-state energy at cold and hot gaps",
            "compute expansion work, cold heat rejection, compression work input, and hot heat absorption",
            "check net work, efficiency, Carnot bound, energy accounting, and adjacent graveyards",
        ],
        "carrier_topology": "finite two-level density matrix with two ideal thermal endpoint states and two Hamiltonian gaps",
        "observable": "excited populations, endpoint energies, Q_hot, Q_cold, W_out, efficiency, Carnot bound, density validity",
        "pass_fail_predicate": (
            "hot population exceeds cold population, W_out and Q_hot are positive, Q_cold is negative, accounting closes, "
            "efficiency respects the Carnot bound, and graveyards collapse or invert"
        ),
        "graveyards": [
            "no gap change gives zero work",
            "matching scaled gaps equalize populations and zero work",
            "reversed temperature assignment consumes work",
            "same temperature with gap change violates hot/cold population order",
            "super-Carnot efficiency claim rejected",
        ],
        "baselines": [
            "scalar two-bath four-stroke work/heat bound receipt",
            "QuTiP two-level thermal reset erasure-floor receipt",
            "Qiskit two-level Kraus reset erasure-floor receipt",
        ],
        "alternative_formulations": [
            "Lindblad two-bath thermalization stroke schedule",
            "finite-time irreversible gap-change schedule",
            "Qiskit density-matrix endpoint cross-check",
            "SymPy closed-form population and efficiency identities",
        ],
        "exact_tool_function_needs": {
            "qutip": ["basis", "ket2dm", "expect", "Qobj.tr"],
            "numpy": ["isclose", "eigvalsh"],
        },
        "lego_or_coupling_target": "work_heat_cycle_calibration_fixture",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
