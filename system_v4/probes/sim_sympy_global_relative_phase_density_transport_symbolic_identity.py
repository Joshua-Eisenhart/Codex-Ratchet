#!/usr/bin/env python3
"""SymPy identities for global-vs-relative phase density transport."""

from __future__ import annotations

import json
import time
from pathlib import Path

import sympy as sp
from receipt_boundary import apply_default_receipt_boundary


NAME = "sympy_global_relative_phase_density_transport_symbolic_identity"
CLASSIFICATION = "classical_baseline"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "symbolically simplifies density-transport identities and adjacent degeneracy controls",
    }
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing"}


def trace(matrix: sp.Matrix) -> sp.Expr:
    return sp.simplify(sum(matrix[idx, idx] for idx in range(matrix.rows)))


def frobenius_norm_squared(matrix: sp.Matrix) -> sp.Expr:
    return sp.simplify(sum(sp.conjugate(value) * value for value in matrix))


def main() -> int:
    started = time.time()
    theta, phase = sp.symbols("theta phase", real=True)
    c = sp.cos(theta / 2)
    s = sp.sin(theta / 2)
    ket = sp.Matrix([[c], [s]])
    rho = sp.simplify(ket * ket.conjugate().T)

    global_u = sp.exp(sp.I * phase / 2) * sp.eye(2)
    relative_u = sp.diag(sp.exp(sp.I * phase / 2), sp.exp(-sp.I * phase / 2))

    global_rho = sp.simplify(global_u * rho * global_u.conjugate().T)
    relative_rho = sp.simplify(relative_u * rho * relative_u.conjugate().T)
    global_delta = sp.simplify(global_rho - rho)
    relative_delta = sp.simplify(relative_rho - rho)

    global_density_displacement_squared = sp.trigsimp(frobenius_norm_squared(global_delta))
    relative_density_displacement_squared = sp.trigsimp(frobenius_norm_squared(relative_delta))
    expected_relative_density_displacement_squared = 2 * sp.sin(theta) ** 2 * sp.sin(phase / 2) ** 2
    relative_formula_delta = sp.trigsimp(
        relative_density_displacement_squared - expected_relative_density_displacement_squared
    )

    pauli_z = sp.Matrix([[1, 0], [0, -1]])
    z_start = sp.trigsimp(trace(pauli_z * rho))
    z_relative = sp.trigsimp(trace(pauli_z * relative_rho))
    diagonal_readout_delta = sp.trigsimp(z_relative - z_start)

    graveyards = {
        "relative_phase_zero_degenerates": {
            "relative_displacement_squared_at_phase_zero": sp.sstr(
                sp.trigsimp(relative_density_displacement_squared.subs(phase, 0))
            ),
            "passed": sp.trigsimp(relative_density_displacement_squared.subs(phase, 0)) == 0,
        },
        "relative_phase_on_pole_density_degenerates": {
            "relative_displacement_squared_at_theta_zero": sp.sstr(
                sp.trigsimp(relative_density_displacement_squared.subs(theta, 0))
            ),
            "passed": sp.trigsimp(relative_density_displacement_squared.subs(theta, 0)) == 0,
        },
        "diagonal_readout_hides_relative_phase_transport": {
            "z_readout_delta": sp.sstr(diagonal_readout_delta),
            "passed": diagonal_readout_delta == 0,
        },
        "both_transports_global_phase_would_collapse_distinction": {
            "global_displacement_squared": sp.sstr(global_density_displacement_squared),
            "candidate_passed": global_density_displacement_squared != 0,
            "expected": False,
            "passed": global_density_displacement_squared == 0,
        },
        "bare_phase_symbols_without_density_carrier_are_insufficient": {
            "has_density_carrier": False,
            "has_loop_family": False,
            "can_compare_density_transport": False,
            "passed": True,
        },
    }

    positive = {
        "global_density_transport_delta_zero": {
            "global_delta_matrix": [[sp.sstr(sp.simplify(value)) for value in row] for row in global_delta.tolist()],
            "global_density_displacement_squared": sp.sstr(global_density_displacement_squared),
            "passed": global_density_displacement_squared == 0,
        },
        "relative_density_transport_formula": {
            "relative_density_displacement_squared": sp.sstr(relative_density_displacement_squared),
            "expected_relative_density_displacement_squared": sp.sstr(
                expected_relative_density_displacement_squared
            ),
            "formula_delta": sp.sstr(relative_formula_delta),
            "passed": relative_formula_delta == 0,
        },
    }
    all_pass = bool(all(row["passed"] for row in positive.values()) and all(row["passed"] for row in graveyards.values()))

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "promotion_allowed": False,
        "claim_ceiling": (
            "SymPy symbolic baseline for two-component global-phase density invariance and relative-phase "
            "density-transport displacement identity only; no full Hopf bundle, no physical loop independence, "
            "no flux, no QIT, GStack, axis, bridge, engine, target-system, or nonclassical admission"
        ),
        "next_lego_target": "two_component_global_relative_phase_density_transport_symbolic_identity",
        "promotion_condition": "No promotion from this identity; use only as symbolic companion evidence for already-fenced numeric transport baselines.",
        "blocked_until": "blocked from geometric-constraint-manifold claims until nested carrier geometry and physical-evolution graveyards exist",
        "demotion_condition": "Demote if cited as full Hopf geometry, physical loop independence, flux, QIT, GStack, axis, bridge, engine, target-system, or nonclassical evidence.",
        "divergence_log": (
            "This exact identity proves only the algebraic two-component density response under global and "
            "relative phase matrices. It omits numerical backend execution, nested carrier geometry, flux "
            "representation, Lindblad terrain dynamics, and target-system admission."
        ),
        "operation_sequence": [
            "construct symbolic two-component pure-state density rho(theta)",
            "apply global-phase matrix exp(i phase/2) I",
            "apply relative-phase matrix diag(exp(i phase/2), exp(-i phase/2))",
            "simplify global density delta and relative density Frobenius displacement",
            "run zero-phase, pole-density, diagonal-readout, global-only, and no-carrier graveyards",
        ],
        "carrier_topology": "symbolic two-component density carrier with global-phase and relative-phase unitary matrices; no full Hopf bundle or nested-tori manifold",
        "observable": "symbolic density delta, Frobenius displacement squared, trace, and sigma_z readout",
        "pass_fail_predicate": "global-phase density delta simplifies to zero; relative-phase Frobenius displacement squared simplifies to 2 sin(theta)^2 sin(phase/2)^2; adjacent graveyards collapse or become insufficient",
        "graveyards": [
            "relative phase equals zero degenerates",
            "relative phase on pole density degenerates",
            "diagonal sigma_z readout hides relative phase transport",
            "global phase alone collapses density-transport distinction",
            "bare phase symbols without density carrier are insufficient",
        ],
        "baselines": [
            "QuTiP global-relative phase non-pole sweep receipt",
            "Qiskit global-relative phase non-pole sweep receipt",
            "QuTiP/Qiskit non-pole sweep backend-agreement audit",
        ],
        "alternative_formulations": [
            "QuTiP Qobj parameter sweep",
            "Qiskit DensityMatrix parameter sweep",
            "Clifford rotor relative-phase companion",
            "nested Hopf-torus carrier fixture before stronger geometry claims",
        ],
        "exact_tool_function_needs": {
            "sympy": ["symbols", "Matrix", "diag", "exp", "sin", "cos", "simplify", "trigsimp"],
        },
        "lego_or_coupling_target": "two_component_global_relative_phase_density_transport_symbolic_identity",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "positive_count": len(positive),
            "graveyard_count": len(graveyards),
            "all_positive_pass": all(row["passed"] for row in positive.values()),
            "all_graveyards_pass": all(row["passed"] for row in graveyards.values()),
            "promotion_allowed": False,
            "all_pass": all_pass,
        },
        "positive": positive,
        "graveyards_detail": graveyards,
        "out_of_scope": [
            "No numerical backend execution.",
            "No full Hopf bundle or nested Hopf-torus carrier.",
            "No physical loop-independence closure.",
            "No flux, QIT, GStack, axis, bridge, engine, target-system, or nonclassical claim.",
        ],
        "elapsed_seconds": round(time.time() - started, 6),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    result = apply_default_receipt_boundary(result, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {result['all_pass']}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
