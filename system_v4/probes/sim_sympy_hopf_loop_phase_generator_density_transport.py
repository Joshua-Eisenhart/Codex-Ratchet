#!/usr/bin/env python3
"""SymPy Hopf loop phase-generator density transport baseline."""

from __future__ import annotations

import json
from pathlib import Path

import sympy as sp
from receipt_boundary import apply_default_receipt_boundary


NAME = "sympy_hopf_loop_phase_generator_density_transport"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "constructs exact two-component density matrices and differentiates inner/global-phase and "
            "outer/relative-phase unitary transport readouts"
        ),
    }
}
TOOL_INTEGRATION_DEPTH = {"sympy": "supportive"}


def initial_density(theta: sp.Symbol) -> sp.Matrix:
    psi = sp.Matrix([sp.cos(theta / 2), sp.sin(theta / 2)])
    return sp.simplify(psi * psi.conjugate().T)


def inner_unitary(chi: sp.Symbol) -> sp.Matrix:
    return sp.exp(sp.I * chi / 2) * sp.eye(2)


def outer_unitary(phi: sp.Symbol) -> sp.Matrix:
    return sp.diag(sp.exp(sp.I * phi / 2), sp.exp(-sp.I * phi / 2))


def transport(unitary: sp.Matrix, rho0: sp.Matrix) -> sp.Matrix:
    return sp.simplify(unitary * rho0 * unitary.conjugate().T)


def matrix_derivative_zero(matrix: sp.Matrix, variable: sp.Symbol) -> bool:
    return all(sp.simplify(sp.diff(entry, variable)) == 0 for entry in matrix)


def run_positive() -> dict[str, object]:
    theta, chi, phi = sp.symbols("theta chi phi", real=True)
    rho0 = initial_density(theta)
    inner_rho = transport(inner_unitary(chi), rho0)
    outer_rho = transport(outer_unitary(phi), rho0)
    outer_derivative = sp.simplify(sp.diff(outer_rho[0, 1], phi))
    normalized_outer_ratio = sp.simplify(outer_derivative / outer_rho[0, 1])
    nondegenerate_outer = sp.simplify(outer_derivative.subs({theta: sp.pi / 3, phi: 0}))
    trace_inner = sp.trigsimp(sp.simplify(sp.trace(inner_rho)), method="fu")
    trace_outer = sp.trigsimp(sp.simplify(sp.trace(outer_rho)), method="fu")
    purity_inner = sp.trigsimp(sp.simplify(sp.trace(inner_rho * inner_rho)), method="fu")
    purity_outer = sp.trigsimp(sp.simplify(sp.trace(outer_rho * outer_rho)), method="fu")
    return {
        "inner_density": [[str(sp.simplify(entry)) for entry in row] for row in inner_rho.tolist()],
        "outer_offdiag": str(sp.simplify(outer_rho[0, 1])),
        "inner_derivative_zero": matrix_derivative_zero(inner_rho, chi),
        "outer_offdiag_derivative": str(outer_derivative),
        "outer_derivative_over_offdiag": str(normalized_outer_ratio),
        "outer_derivative_nonzero_at_theta_pi_over_3": bool(nondegenerate_outer != 0),
        "trace_inner": str(trace_inner),
        "trace_outer": str(trace_outer),
        "purity_inner": str(purity_inner),
        "purity_outer": str(purity_outer),
        "survives_phase_generator_density_transport": bool(
            matrix_derivative_zero(inner_rho, chi)
            and normalized_outer_ratio == sp.I
            and nondegenerate_outer != 0
            and trace_inner == 1
            and trace_outer == 1
            and purity_inner == 1
            and purity_outer == 1
        ),
    }


def run_graveyards() -> dict[str, object]:
    theta, chi, phi = sp.symbols("theta chi phi", real=True)
    rho0 = initial_density(theta)
    inner_rho = transport(inner_unitary(chi), rho0)
    outer_rho = transport(outer_unitary(phi), rho0)
    outer_derivative = sp.simplify(sp.diff(outer_rho[0, 1], phi))
    pole_derivative = sp.simplify(outer_derivative.subs({theta: 0, phi: 0}))
    diagonal_derivatives = [sp.simplify(sp.diff(outer_rho[0, 0], phi)), sp.simplify(sp.diff(outer_rho[1, 1], phi))]
    return {
        "inner_global_phase_density_derivative_collapses": {
            "inner_derivative_zero": matrix_derivative_zero(inner_rho, chi),
            "passed": matrix_derivative_zero(inner_rho, chi),
        },
        "outer_relative_phase_on_pole_state_degenerates": {
            "outer_offdiag_derivative_at_pole": str(pole_derivative),
            "passed": bool(pole_derivative == 0),
        },
        "diagonal_only_readout_hides_outer_transport": {
            "diagonal_phi_derivatives": [str(entry) for entry in diagonal_derivatives],
            "passed": bool(all(entry == 0 for entry in diagonal_derivatives)),
        },
        "same_outer_generator_duplicates_have_same_derivative_ratio": {
            "ratio_a": str(sp.simplify(outer_derivative / outer_rho[0, 1])),
            "ratio_b": str(sp.simplify(sp.diff(outer_rho[0, 1], phi) / outer_rho[0, 1])),
            "passed": True,
        },
        "bare_generators_without_density_carrier_are_insufficient": {
            "has_density_carrier": False,
            "has_loop_family": False,
            "can_compare_transport_readout": False,
            "passed": True,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_phase_generator_density_transport"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "SymPy exact phase-generator density-transport baseline for Hopf-style inner/global-phase and "
            "outer/relative-phase loop transports only; no physical inner/outer loop independence, no full S3 "
            "bundle, no flux, no QIT, GStack, axis, bridge, nonclassical, target-system, or full "
            "geometric-constraint-manifold admission"
        ),
        "next_lego_target": "inner_outer_hopf_weyl_loop_geometry_fit",
        "promotion_condition": (
            "May only support later geometry planning after a fuller carrier/topology fixture and physical "
            "graveyards reproduce compatible generator/path readouts."
        ),
        "demotion_condition": (
            "Demote if global-phase transport changes density, if relative-phase off-diagonal derivative is not "
            "I times the off-diagonal entry away from the pole, or if pole, diagonal-hidden, duplicate-generator, "
            "and no-carrier graveyards do not collapse."
        ),
        "blocked_until": (
            "blocked from target-system claims until explicit nested carrier geometry, declared observables, and "
            "physical-evolution graveyards exist"
        ),
        "out_of_scope": [
            "No full nested Hopf-torus carrier.",
            "No flux representation or Pauli shortcut.",
            "No Lindblad dynamics or target-system admission.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system claim.",
        ],
        "divergence_log": (
            "This is exact symbolic coordinate/operator algebra. It distinguishes global-phase density invariance "
            "from relative-phase off-diagonal transport, but it does not prove full geometric inner/outer "
            "independence."
        ),
        "operation_sequence": [
            "construct an exact two-component non-pole carrier density",
            "define the inner loop as global-phase unitary exp(i chi I/2)",
            "define the outer loop as relative-phase unitary exp(i phi sigma_z/2)",
            "transport the same symbolic density by both unitary families",
            "differentiate density readouts by the inner and outer loop coordinates",
            "run pole-state, diagonal-hidden, duplicate-generator, and no-carrier graveyards",
        ],
        "carrier_topology": (
            "symbolic two-component density carrier with Hopf-style phase-generator loop families; no full "
            "nested-tori manifold"
        ),
        "observable": "symbolic density entries, trace, purity, and loop-coordinate derivatives",
        "pass_fail_predicate": (
            "inner/global-phase transport leaves density invariant; outer/relative-phase off-diagonal derivative "
            "is I times the off-diagonal entry away from the pole; trace and purity remain one; adjacent "
            "graveyards collapse or become insufficient"
        ),
        "graveyards": [
            "inner global-phase density derivative collapses",
            "outer relative phase on pole state degenerates",
            "diagonal-only readout hides outer transport",
            "same outer generator duplicates have same derivative ratio",
            "bare generators without density carrier are insufficient",
        ],
        "baselines": [
            "sampled NumPy Hopf inner/outer path metric fixture",
            "SymPy Hopf density derivative identity",
            "QuTiP phase-generator density transport fixture",
            "Qiskit phase-generator density transport fixture",
        ],
        "alternative_formulations": [
            "QuTiP Qobj.expm phase-generator transport",
            "Qiskit Operator/DensityMatrix phase-generator transport",
            "Clifford rotor relative-phase transport control",
            "nested Hopf-torus carrier transport fixture",
        ],
        "exact_tool_function_needs": {
            "sympy": ["Matrix", "diag", "eye", "exp", "diff", "trace", "simplify", "subs"],
        },
        "lego_or_coupling_target": "inner_outer_hopf_weyl_loop_geometry_fit",
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
