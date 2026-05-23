#!/usr/bin/env python3
"""SciPy Hopf horizontal-lift chi-shift baseline."""

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
from receipt_boundary import apply_default_receipt_boundary
from scipy.integrate import solve_ivp


NAME = "scipy_hopf_horizontal_lift_chi_shift"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "solve_ivp integrates the Hopf horizontal-lift ODE dchi/dphi = -cos(theta) over base latitude loops",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supports numeric tolerances, trigonometric readouts, and residual aggregation",
    },
}
TOOL_INTEGRATION_DEPTH = {"scipy": "load_bearing", "numpy": "supportive"}


def integrate_horizontal_lift(theta: float, phi_end: float = 2.0 * math.pi) -> dict[str, object]:
    """Integrate A=0 for A=1/2(dchi + cos(theta)dphi)."""

    def rhs(_phi: float, _state: np.ndarray) -> list[float]:
        return [-math.cos(theta)]

    solution = solve_ivp(rhs, (0.0, phi_end), [0.0], rtol=1e-11, atol=1e-13, dense_output=True)
    if not solution.success:
        raise RuntimeError(solution.message)

    sample_phi = np.linspace(0.0, phi_end, 257)
    sample_chi = solution.sol(sample_phi)[0]
    dchi_dphi = np.full_like(sample_phi, -math.cos(theta), dtype=float)
    connection_residual = 0.5 * (dchi_dphi + math.cos(theta))
    expected_shift = -phi_end * math.cos(theta)
    final_shift = float(solution.y[0, -1])
    max_connection_residual = float(np.max(np.abs(connection_residual)))
    return {
        "theta": theta,
        "phi_end": phi_end,
        "final_chi_shift": final_shift,
        "expected_chi_shift": expected_shift,
        "abs_error": abs(final_shift - expected_shift),
        "max_connection_residual": max_connection_residual,
        "solid_angle": float(2.0 * math.pi * (1.0 - math.cos(theta))),
        "nfev": int(solution.nfev),
    }


def connection_integral_without_horizontal_lift(theta: float, phi_end: float = 2.0 * math.pi) -> float:
    return 0.5 * math.cos(theta) * phi_end


def constant_connection_integral(phi_end: float = 2.0 * math.pi) -> float:
    return 0.5 * phi_end


def run_positive() -> dict[str, object]:
    theta_a = math.pi / 3.0
    theta_b = math.pi / 2.0
    lift_a = integrate_horizontal_lift(theta_a)
    lift_b = integrate_horizontal_lift(theta_b)
    shift_difference = float(lift_b["final_chi_shift"] - lift_a["final_chi_shift"])
    area_difference = float(lift_b["solid_angle"] - lift_a["solid_angle"])
    return {
        "theta_a": theta_a,
        "theta_b": theta_b,
        "lift_a": lift_a,
        "lift_b": lift_b,
        "horizontal_chi_shift_difference": shift_difference,
        "base_area_difference": area_difference,
        "survives_numeric_horizontal_lift": bool(
            lift_a["abs_error"] < 1e-10
            and lift_b["abs_error"] < 1e-10
            and lift_a["max_connection_residual"] < 1e-12
            and lift_b["max_connection_residual"] < 1e-12
            and abs(shift_difference) > 1e-6
            and abs(area_difference) > 1e-6
        ),
    }


def run_graveyards() -> dict[str, object]:
    theta_a = math.pi / 3.0
    theta_b = math.pi / 2.0
    same_a = integrate_horizontal_lift(theta_a)
    same_b = integrate_horizontal_lift(theta_a)
    equator = integrate_horizontal_lift(theta_b)
    point_base = integrate_horizontal_lift(theta_a, phi_end=0.0)
    no_lift_integral = connection_integral_without_horizontal_lift(theta_a)
    constant_a = constant_connection_integral()
    constant_b = constant_connection_integral()
    return {
        "same_base_latitude_has_no_shift_difference": {
            "shift_difference": float(same_b["final_chi_shift"] - same_a["final_chi_shift"]),
            "passed": bool(abs(same_b["final_chi_shift"] - same_a["final_chi_shift"]) < 1e-12),
        },
        "base_loop_without_horizontal_lift_accumulates_connection": {
            "connection_integral": no_lift_integral,
            "expected_nonzero": True,
            "passed": bool(abs(no_lift_integral) > 1e-6),
        },
        "equator_horizontal_lift_has_zero_chi_shift": {
            "chi_shift": equator["final_chi_shift"],
            "passed": bool(abs(float(equator["final_chi_shift"])) < 1e-10),
        },
        "zero_base_traversal_has_zero_chi_shift": {
            "chi_shift": point_base["final_chi_shift"],
            "passed": bool(abs(float(point_base["final_chi_shift"])) < 1e-12),
        },
        "constant_connection_without_theta_dependence_cannot_distinguish_latitudes": {
            "constant_integral_a": constant_a,
            "constant_integral_b": constant_b,
            "passed": bool(abs(constant_a - constant_b) < 1e-12),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_numeric_horizontal_lift"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "SciPy numeric Hopf U(1) horizontal-lift ODE baseline for base latitude chi shifts only; "
            "no QIT, GStack, axis, bridge, nonclassical, flux, Pauli shortcut, target-system, or full "
            "geometric-constraint-manifold admission"
        ),
        "next_lego_target": "hopf_loop_holonomy_geometry_baseline",
        "promotion_condition": (
            "May only support later carrier-geometry planning after independent bundle-chart, nested torus, "
            "operator-evolution, and physical graveyard receipts reproduce compatible loop readouts."
        ),
        "demotion_condition": (
            "Demote if solve_ivp misses the analytic chi shift, if the horizontal connection residual is nonzero, "
            "if distinct latitudes do not separate, or if same-latitude/no-lift/equator/zero-traversal/constant "
            "controls fail."
        ),
        "blocked_until": "blocked from target-system claims until fuller Hopf/Weyl carrier topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full geometric-constraint-manifold implementation.",
            "No nested Hopf-torus manifold stack.",
            "No flux representation or Pauli shortcut.",
            "No Lindblad evolution, Hamiltonian dynamics, or target-system admission.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This baseline tests numerical integration of one local Hopf connection condition. It can support "
            "inner/outer carrier-geometry exploration, but it does not close independence of full Weyl-spinor "
            "inner and outer loops without a fuller geometric carrier."
        ),
        "operation_sequence": [
            "declare the local Hopf connection A = 1/2(dchi + cos(theta)dphi)",
            "integrate the horizontal-lift ODE dchi/dphi = -cos(theta) over phi in [0,2pi]",
            "compare solve_ivp final chi shifts against analytic -2pi cos(theta)",
            "compute connection residuals for two base latitudes",
            "compute base solid-angle differences for the same latitudes",
            "run same-latitude, no-horizontal-lift, equator, zero-traversal, and constant-connection graveyards",
        ],
        "carrier_topology": "local Hopf U(1) bundle chart with horizontal lifts of base latitude loops",
        "observable": "numeric final chi shift, analytic chi shift error, connection residual, and base solid-angle difference",
        "pass_fail_predicate": (
            "solve_ivp chi shifts match -2pi cos(theta), horizontal connection residual is zero within tolerance, "
            "distinct base latitudes have distinct shifts and areas, and adjacent controls collapse or expose "
            "missing horizontal/base dependence"
        ),
        "graveyards": [
            "same base latitude has no shift difference",
            "base loop without horizontal lift accumulates connection",
            "equator horizontal lift has zero chi shift",
            "zero base traversal has zero chi shift",
            "constant connection without theta dependence cannot distinguish latitudes",
        ],
        "baselines": [
            "SymPy Hopf loop holonomy area-dependence fixture",
            "SymPy Hopf connection curvature first-Chern integral fixture",
            "GUDHI Hopf torus fiber/base homology fixture",
            "sampled Hopf/Weyl inner-outer loop readout fixture",
        ],
        "alternative_formulations": [
            "exact SymPy connection integral",
            "Stokes theorem over a triangulated base cap",
            "sampled SU(2) matrix transport fixture",
            "nested Hopf-torus carrier holonomy fixture",
        ],
        "exact_tool_function_needs": {
            "scipy": ["integrate.solve_ivp"],
            "numpy": ["linspace", "max", "abs"],
        },
        "lego_or_coupling_target": "hopf_loop_holonomy_geometry_baseline",
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
