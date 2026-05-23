#!/usr/bin/env python3
"""SymPy Hopf connection curvature and first-Chern integral baseline."""

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


NAME = "sympy_hopf_connection_curvature_c1_integral"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "computes exact differential-form coefficients, curvature, and first-Chern integral for the Hopf U(1) connection",
    }
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing"}


theta, phi, chi = sp.symbols("theta phi chi", real=True)


def curvature_coeff(a_theta: sp.Expr, a_phi: sp.Expr) -> sp.Expr:
    """Return F_theta_phi for A = A_theta dtheta + A_phi dphi + A_chi dchi."""
    return sp.simplify(sp.diff(a_phi, theta) - sp.diff(a_theta, phi))


def integrate_s2(two_form_coeff: sp.Expr) -> sp.Expr:
    return sp.simplify(sp.integrate(sp.integrate(two_form_coeff, (theta, 0, sp.pi)), (phi, 0, 2 * sp.pi)))


def run_positive() -> dict[str, object]:
    # Hopf connection in a standard gauge:
    # A = 1/2 (dchi + cos(theta) dphi), so F = dA = -1/2 sin(theta) dtheta ^ dphi.
    a_theta = sp.Integer(0)
    a_phi = sp.cos(theta) / 2
    a_chi = sp.Rational(1, 2)
    f_theta_phi = curvature_coeff(a_theta, a_phi)
    integral = integrate_s2(f_theta_phi)
    c1 = sp.simplify(integral / (2 * sp.pi))
    return {
        "connection_coefficients": {
            "A_theta": str(a_theta),
            "A_phi": str(a_phi),
            "A_chi": str(a_chi),
        },
        "curvature_F_theta_phi": str(f_theta_phi),
        "curvature_integral_over_s2": str(integral),
        "first_chern_signed": str(c1),
        "first_chern_magnitude": str(sp.Abs(c1)),
        "survives_exact_hopf_connection_curvature": bool(
            sp.simplify(f_theta_phi + sp.sin(theta) / 2) == 0
            and sp.simplify(c1 + 1) == 0
            and sp.simplify(sp.Abs(c1) - 1) == 0
        ),
    }


def run_graveyards() -> dict[str, object]:
    flat_fiber_only = curvature_coeff(sp.Integer(0), sp.Integer(0))
    flat_fiber_integral = integrate_s2(flat_fiber_only)

    pure_gauge_lambda = chi / 2 + phi / 3
    pure_a_theta = sp.diff(pure_gauge_lambda, theta)
    pure_a_phi = sp.diff(pure_gauge_lambda, phi)
    pure_f = curvature_coeff(pure_a_theta, pure_a_phi)

    reversed_orientation_f = sp.sin(theta) / 2
    reversed_integral = integrate_s2(reversed_orientation_f)
    reversed_c1 = sp.simplify(reversed_integral / (2 * sp.pi))

    constant_phi_connection_f = curvature_coeff(sp.Integer(0), sp.Rational(1, 2))
    constant_phi_integral = integrate_s2(constant_phi_connection_f)

    return {
        "fiber_only_connection_has_zero_base_curvature": {
            "F_theta_phi": str(flat_fiber_only),
            "integral": str(flat_fiber_integral),
            "passed": bool(flat_fiber_only == 0 and flat_fiber_integral == 0),
        },
        "pure_gauge_exact_form_has_zero_curvature": {
            "A_theta": str(pure_a_theta),
            "A_phi": str(pure_a_phi),
            "F_theta_phi": str(pure_f),
            "passed": bool(sp.simplify(pure_f) == 0),
        },
        "reversed_orientation_flips_c1_sign_only": {
            "F_theta_phi": str(reversed_orientation_f),
            "integral": str(reversed_integral),
            "first_chern_signed": str(reversed_c1),
            "passed": bool(sp.simplify(reversed_c1 - 1) == 0),
        },
        "constant_base_phi_connection_has_zero_curvature": {
            "F_theta_phi": str(constant_phi_connection_f),
            "integral": str(constant_phi_integral),
            "passed": bool(constant_phi_connection_f == 0 and constant_phi_integral == 0),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_exact_hopf_connection_curvature"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "Exact SymPy differential-form coefficient baseline for the Hopf U(1) connection curvature and "
            "first-Chern integral only; no QIT, GStack, axis, bridge, nonclassical, Pauli-flux shortcut, or "
            "target-system admission"
        ),
        "next_lego_target": "hopf_connection_curvature_geometry_baseline",
        "promotion_condition": (
            "May only support later geometric carrier planning after independent bundle, holonomy, loop-transport, "
            "and operator-evolution receipts reproduce compatible curvature readouts with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if exact curvature is not -sin(theta)/2, if the first-Chern magnitude is not 1, or if flat, "
            "pure-gauge, reversed-orientation, and constant-base controls do not behave as expected."
        ),
        "blocked_until": "blocked from target-system claims until fuller Hopf/Weyl carrier topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full geometric-constraint-manifold implementation.",
            "No Pauli flux representation or flux-to-Pauli shortcut.",
            "No Lindblad evolution, Hamiltonian dynamics, or target-system admission.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This baseline treats the relevant quantity as curvature of a Hopf U(1) connection. It does not claim "
            "that project-specific flux is admitted, nor that flux is represented by Pauli matrices."
        ),
        "operation_sequence": [
            "declare the Hopf connection coefficients A = 1/2(dchi + cos(theta)dphi)",
            "compute F_theta_phi = partial_theta A_phi - partial_phi A_theta exactly",
            "integrate F over theta in [0,pi] and phi in [0,2pi]",
            "compute signed and magnitude first-Chern readouts",
            "run flat fiber-only, pure-gauge, reversed-orientation, and constant-base controls",
        ],
        "carrier_topology": "local coefficient chart for the Hopf U(1) bundle S1 -> S3 -> S2",
        "observable": "exact curvature coefficient F_theta_phi, integral over S2, signed first-Chern value, and first-Chern magnitude",
        "pass_fail_predicate": (
            "F_theta_phi equals -sin(theta)/2, signed first-Chern value is -1 under the declared orientation, "
            "magnitude is 1, and adjacent flat/pure-gauge/orientation controls collapse or flip as expected"
        ),
        "graveyards": [
            "fiber-only connection has zero base curvature",
            "pure-gauge exact form has zero curvature",
            "reversed orientation flips first-Chern sign only",
            "constant base-phi connection has zero curvature",
        ],
        "baselines": [
            "SymPy Hopf density derivative fixture",
            "GUDHI Hopf torus fiber/base homology fixture",
            "Clifford projected outer-loop rotor fixture",
        ],
        "alternative_formulations": [
            "numeric holonomy around small S2 rectangles",
            "Stokes theorem on a triangulated base patch",
            "bundle horizontal-lift transport fixture",
            "nested Hopf-torus carrier curvature fixture",
        ],
        "exact_tool_function_needs": {
            "sympy": ["symbols", "diff", "integrate", "simplify", "Abs"],
        },
        "lego_or_coupling_target": "hopf_connection_curvature_geometry_baseline",
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
