#!/usr/bin/env python3
"""SymPy Hopf loop holonomy area-dependence baseline."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
from pathlib import Path

import sympy as sp
from receipt_boundary import apply_default_receipt_boundary


NAME = "sympy_hopf_loop_holonomy_area_dependence"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "computes exact Hopf connection integrals for vertical fiber loops and horizontal base-loop lifts",
    }
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing"}


theta, phi, chi = sp.symbols("theta phi chi", real=True)


def connection_integral_for_path(dchi_dphi: sp.Expr, theta_value: sp.Expr) -> sp.Expr:
    """Integrate A = 1/2(dchi + cos(theta)dphi) around phi in [0, 2pi]."""
    integrand = sp.simplify((dchi_dphi + sp.cos(theta_value)) / 2)
    return sp.simplify(sp.integrate(integrand, (phi, 0, 2 * sp.pi)))


def horizontal_chi_shift(theta_value: sp.Expr) -> sp.Expr:
    """For A=0 along the base loop, dchi/dphi = -cos(theta)."""
    return sp.simplify(sp.integrate(-sp.cos(theta_value), (phi, 0, 2 * sp.pi)))


def solid_angle_latitude(theta_value: sp.Expr) -> sp.Expr:
    return sp.simplify(2 * sp.pi * (1 - sp.cos(theta_value)))


def vertical_fiber_connection_integral() -> sp.Expr:
    return sp.simplify(sp.integrate(sp.Rational(1, 2), (chi, 0, 2 * sp.pi)))


def run_positive() -> dict[str, object]:
    theta_a = sp.pi / 3
    theta_b = sp.pi / 2
    fiber_integral = vertical_fiber_connection_integral()
    horizontal_a = connection_integral_for_path(-sp.cos(theta_a), theta_a)
    horizontal_b = connection_integral_for_path(-sp.cos(theta_b), theta_b)
    chi_shift_a = horizontal_chi_shift(theta_a)
    chi_shift_b = horizontal_chi_shift(theta_b)
    area_a = solid_angle_latitude(theta_a)
    area_b = solid_angle_latitude(theta_b)
    return {
        "fiber_loop_connection_integral": str(fiber_integral),
        "base_loop_theta_a": str(theta_a),
        "base_loop_theta_b": str(theta_b),
        "base_solid_angle_a": str(area_a),
        "base_solid_angle_b": str(area_b),
        "horizontal_connection_integral_a": str(horizontal_a),
        "horizontal_connection_integral_b": str(horizontal_b),
        "horizontal_chi_shift_a": str(chi_shift_a),
        "horizontal_chi_shift_b": str(chi_shift_b),
        "base_area_difference": str(sp.simplify(area_b - area_a)),
        "horizontal_chi_shift_difference": str(sp.simplify(chi_shift_b - chi_shift_a)),
        "survives_area_dependent_horizontal_lift": bool(
            sp.simplify(fiber_integral - sp.pi) == 0
            and horizontal_a == 0
            and horizontal_b == 0
            and sp.simplify(area_b - area_a) != 0
            and sp.simplify(chi_shift_b - chi_shift_a) != 0
        ),
    }


def run_graveyards() -> dict[str, object]:
    theta_a = sp.pi / 3
    theta_b = sp.pi / 2
    same_theta_shift = sp.simplify(horizontal_chi_shift(theta_a) - horizontal_chi_shift(theta_a))
    no_horizontal_lift_integral = connection_integral_for_path(sp.Integer(0), theta_a)
    equator_shift = horizontal_chi_shift(sp.pi / 2)
    point_base_area = solid_angle_latitude(sp.Integer(0))
    point_base_shift = horizontal_chi_shift(sp.Integer(0))
    constant_connection_integral = sp.simplify(sp.integrate(sp.Rational(1, 2), (phi, 0, 2 * sp.pi)))
    return {
        "same_base_latitude_has_no_holonomy_difference": {
            "shift_difference": str(same_theta_shift),
            "passed": bool(same_theta_shift == 0),
        },
        "base_loop_without_horizontal_lift_accumulates_connection": {
            "connection_integral": str(no_horizontal_lift_integral),
            "expected_nonzero": True,
            "passed": bool(sp.simplify(no_horizontal_lift_integral - sp.pi / 2) == 0),
        },
        "equator_horizontal_lift_has_zero_chi_shift": {
            "chi_shift": str(equator_shift),
            "passed": bool(equator_shift == 0),
        },
        "point_base_loop_collapses_area_but_not_vertical_shift": {
            "solid_angle": str(point_base_area),
            "horizontal_chi_shift": str(point_base_shift),
            "passed": bool(point_base_area == 0 and sp.simplify(point_base_shift + 2 * sp.pi) == 0),
        },
        "constant_connection_without_base_dependence_cannot_distinguish_latitudes": {
            "constant_connection_integral": str(constant_connection_integral),
            "same_for_all_latitudes": True,
            "passed": bool(sp.simplify(constant_connection_integral - sp.pi) == 0),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_area_dependent_horizontal_lift"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "Exact SymPy Hopf U(1) connection loop-integral baseline for vertical fiber loops and horizontal "
            "base-loop lifts only; no QIT, GStack, axis, bridge, nonclassical, flux, Pauli shortcut, or "
            "target-system admission"
        ),
        "next_lego_target": "hopf_loop_holonomy_geometry_baseline",
        "promotion_condition": (
            "May only support later carrier-geometry planning after independent sampled transport, bundle-chart, "
            "and operator-evolution receipts reproduce compatible holonomy readouts with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if the vertical fiber integral is not pi, if horizontal lifts do not satisfy A=0, if distinct "
            "base latitudes have identical chi shifts, or if same-latitude/no-lift/equator/constant controls fail."
        ),
        "blocked_until": "blocked from target-system claims until fuller Hopf/Weyl carrier topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full geometric-constraint-manifold implementation.",
            "No flux representation or Pauli shortcut.",
            "No Lindblad evolution, Hamiltonian dynamics, or target-system admission.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This baseline tests loop-level geometry of the Hopf connection. It separates vertical fiber phase from "
            "area-dependent horizontal base-loop lift shifts, but it does not simulate a full nested carrier manifold."
        ),
        "operation_sequence": [
            "declare the Hopf connection A = 1/2(dchi + cos(theta)dphi)",
            "integrate A around the vertical fiber loop chi in [0,2pi] at fixed base coordinates",
            "impose horizontal lift A=0 for base latitude loops, giving dchi/dphi = -cos(theta)",
            "compute horizontal chi shifts for two distinct base latitudes",
            "compute base solid-angle readouts for the same latitudes",
            "run same-latitude, no-horizontal-lift, equator, point-base, and constant-connection graveyards",
        ],
        "carrier_topology": "local Hopf U(1) bundle chart with vertical fiber loop and horizontal lifts of base latitude loops",
        "observable": "exact connection loop integrals, horizontal chi shifts, and base solid-angle differences",
        "pass_fail_predicate": (
            "vertical fiber integral equals pi, horizontal base lifts have zero connection integral, distinct base "
            "latitudes have distinct solid angles and distinct horizontal chi shifts, and adjacent controls collapse "
            "or expose missing horizontal/base dependence"
        ),
        "graveyards": [
            "same base latitude has no holonomy difference",
            "base loop without horizontal lift accumulates connection",
            "equator horizontal lift has zero chi shift",
            "point base loop collapses area",
            "constant connection without base dependence cannot distinguish latitudes",
        ],
        "baselines": [
            "SymPy Hopf connection curvature first-Chern integral fixture",
            "SymPy Hopf density derivative fixture",
            "GUDHI Hopf torus fiber/base homology fixture",
            "QuTiP and Qiskit Hopf density-object readout fixtures",
        ],
        "alternative_formulations": [
            "numeric horizontal-lift ODE integration",
            "Stokes theorem over a triangulated base cap",
            "sampled SU(2) matrix transport fixture",
            "nested Hopf-torus carrier holonomy fixture",
        ],
        "exact_tool_function_needs": {
            "sympy": ["symbols", "cos", "integrate", "simplify", "pi"],
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
