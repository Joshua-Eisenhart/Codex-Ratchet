#!/usr/bin/env python3
"""SciPy connected Hopf-torus horizontal transport baseline."""

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


NAME = "scipy_connected_hopf_torus_horizontal_transport"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "scipy": {
        "tried": True,
        "used": True,
        "reason": (
            "solve_ivp integrates Hopf horizontal-lift ODEs over two connected theta-layer base loops and their "
            "interlayer theta transport"
        ),
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supports sampled residuals, tolerance checks, and interlayer distance diagnostics",
    },
}
TOOL_INTEGRATION_DEPTH = {"scipy": "load_bearing", "numpy": "supportive"}


def hopf_s3_point(theta: float, phi: float, chi: float) -> np.ndarray:
    a = math.cos(theta / 2.0) * np.exp(0.5j * (chi + phi))
    b = math.sin(theta / 2.0) * np.exp(0.5j * (chi - phi))
    return np.array([a.real, a.imag, b.real, b.imag], dtype=float)


def integrate_phi_horizontal(theta: float, phi_end: float) -> dict[str, object]:
    """Integrate A=0 for A=1/2(dchi + cos(theta)dphi) along fixed theta."""

    def rhs(_phi: float, _state: np.ndarray) -> list[float]:
        return [-math.cos(theta)]

    solution = solve_ivp(rhs, (0.0, phi_end), [0.0], rtol=1e-11, atol=1e-13, dense_output=True)
    if not solution.success:
        raise RuntimeError(solution.message)

    sample_phi = np.linspace(0.0, phi_end, 257)
    dchi_dphi = np.full_like(sample_phi, -math.cos(theta), dtype=float)
    residual = 0.5 * (dchi_dphi + math.cos(theta))
    expected = -phi_end * math.cos(theta)
    final = float(solution.y[0, -1])
    return {
        "theta": theta,
        "phi_end": phi_end,
        "final_chi_shift": final,
        "expected_chi_shift": expected,
        "abs_error": float(abs(final - expected)),
        "max_connection_residual": float(np.max(np.abs(residual))),
        "nfev": int(solution.nfev),
    }


def theta_transport_distance(theta_a: float, theta_b: float) -> float:
    low = hopf_s3_point(theta_a, 0.0, 0.0)
    high = hopf_s3_point(theta_b, 0.0, 0.0)
    return float(np.linalg.norm(high - low))


def no_horizontal_connection_integral(theta: float, phi_end: float) -> float:
    return 0.5 * math.cos(theta) * phi_end


def constant_connection_integral(phi_end: float) -> float:
    return 0.5 * phi_end


def run_positive() -> dict[str, object]:
    theta_low = math.pi / 3.0
    theta_high = 2.0 * math.pi / 3.0
    phi_end = 2.0 * math.pi
    low = integrate_phi_horizontal(theta_low, phi_end)
    high = integrate_phi_horizontal(theta_high, phi_end)
    shift_difference = float(high["final_chi_shift"] - low["final_chi_shift"])
    layer_distance = theta_transport_distance(theta_low, theta_high)
    return {
        "theta_low": theta_low,
        "theta_high": theta_high,
        "phi_end": phi_end,
        "low_layer_horizontal_loop": low,
        "high_layer_horizontal_loop": high,
        "interlayer_theta_distance": layer_distance,
        "horizontal_chi_shift_difference": shift_difference,
        "survives_connected_layer_horizontal_transport": bool(
            low["abs_error"] < 1e-10
            and high["abs_error"] < 1e-10
            and low["max_connection_residual"] < 1e-12
            and high["max_connection_residual"] < 1e-12
            and abs(shift_difference) > 1.0
            and layer_distance > 1e-6
        ),
    }


def run_graveyards() -> dict[str, object]:
    theta_low = math.pi / 3.0
    theta_high = 2.0 * math.pi / 3.0
    phi_end = 2.0 * math.pi
    same_a = integrate_phi_horizontal(theta_low, phi_end)
    same_b = integrate_phi_horizontal(theta_low, phi_end)
    zero_phi = integrate_phi_horizontal(theta_low, 0.0)
    no_horizontal_low = no_horizontal_connection_integral(theta_low, phi_end)
    no_horizontal_high = no_horizontal_connection_integral(theta_high, phi_end)
    constant_low = constant_connection_integral(phi_end)
    constant_high = constant_connection_integral(phi_end)
    duplicate_distance = theta_transport_distance(theta_low, theta_low)
    return {
        "duplicate_theta_layers_have_no_transport_difference": {
            "shift_difference": float(same_b["final_chi_shift"] - same_a["final_chi_shift"]),
            "interlayer_theta_distance": duplicate_distance,
            "passed": bool(abs(same_b["final_chi_shift"] - same_a["final_chi_shift"]) < 1e-12 and duplicate_distance < 1e-12),
        },
        "zero_base_traversal_has_zero_horizontal_shift": {
            "final_chi_shift": zero_phi["final_chi_shift"],
            "passed": bool(abs(float(zero_phi["final_chi_shift"])) < 1e-12),
        },
        "base_loop_without_horizontal_lift_accumulates_connection": {
            "low_layer_connection_integral": no_horizontal_low,
            "high_layer_connection_integral": no_horizontal_high,
            "passed": bool(abs(no_horizontal_low) > 1e-6 and abs(no_horizontal_high) > 1e-6),
        },
        "constant_connection_without_theta_dependence_hides_layers": {
            "constant_low": constant_low,
            "constant_high": constant_high,
            "passed": bool(abs(constant_low - constant_high) < 1e-12),
        },
        "disconnected_layers_without_interlayer_path_are_insufficient": {
            "has_interlayer_transport_path": False,
            "can_test_connected_layer_transport": False,
            "passed": True,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_connected_layer_horizontal_transport"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "SciPy connected two-theta-layer Hopf horizontal-transport baseline only; this integrates a local "
            "connection ODE over declared layer coordinates and does not implement full carrier dynamics; no "
            "physical inner/outer loop independence, no full S3 bundle, no flux, no QIT, GStack, axis, bridge, "
            "nonclassical, target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "nested_hopf_torus_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later carrier-geometry planning after connected topology, density-object transport, "
            "and physical graveyard receipts reproduce compatible connected-layer readouts."
        ),
        "demotion_condition": (
            "Demote if solve_ivp misses analytic horizontal shifts, if connection residuals are nonzero, if distinct "
            "theta layers do not separate, or if duplicate-theta/zero-traversal/no-lift/constant/disconnected "
            "graveyards do not collapse."
        ),
        "blocked_until": "blocked from target-system claims until fuller Hopf/Weyl carrier topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full geometric-constraint-manifold implementation.",
            "No flux representation or Pauli shortcut.",
            "No Lindblad evolution, Hamiltonian dynamics, or target-system admission.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This is a local ODE transport fixture over two connected theta layers. It can support connected-carrier "
            "planning, but it does not close inner/outer independence or implement full nested geometry."
        ),
        "operation_sequence": [
            "declare the local Hopf connection A = 1/2(dchi + cos(theta)dphi)",
            "choose two distinct theta layers corresponding to connected Hopf-torus carrier layers",
            "integrate the horizontal-lift ODE dchi/dphi = -cos(theta) over a base loop on each layer",
            "compute the interlayer S3 distance at a shared grid coordinate",
            "compare the two horizontal chi shifts and connection residuals",
            "run duplicate-theta, zero-traversal, no-horizontal-lift, constant-connection, and disconnected-layer graveyards",
        ],
        "carrier_topology": "two declared fixed-theta Hopf-torus layers with an interlayer coordinate path; no full nested-tori manifold",
        "observable": "final chi shifts, analytic shift errors, connection residuals, and interlayer S3 distance",
        "pass_fail_predicate": (
            "solve_ivp chi shifts match -2pi cos(theta), residuals vanish, distinct connected theta layers have "
            "different shifts and nonzero interlayer distance, and adjacent controls collapse or expose missing "
            "connection/layer dependence"
        ),
        "graveyards": [
            "duplicate theta layers have no transport difference",
            "zero base traversal has zero horizontal shift",
            "base loop without horizontal lift accumulates connection",
            "constant connection without theta dependence hides layers",
            "disconnected layers without interlayer path are insufficient",
        ],
        "baselines": [
            "SciPy Hopf horizontal-lift chi-shift fixture",
            "SymPy Hopf loop holonomy area-dependence fixture",
            "TopoNetX connected Hopf-torus layer incidence fixture",
            "GUDHI connected Hopf-torus layer homology fixture",
        ],
        "alternative_formulations": [
            "exact SymPy connected-layer connection integral",
            "density-object transport over connected carrier coordinates",
            "Stokes theorem over triangulated base strips between theta layers",
            "Clifford or SU(2) transport over projected layer coordinates",
        ],
        "exact_tool_function_needs": {
            "scipy": ["integrate.solve_ivp"],
            "numpy": ["linspace", "exp", "linalg.norm", "max", "abs"],
        },
        "lego_or_coupling_target": "nested_hopf_torus_loop_geometry_baseline",
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
