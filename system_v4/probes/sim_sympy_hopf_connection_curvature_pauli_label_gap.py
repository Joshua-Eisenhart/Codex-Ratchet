#!/usr/bin/env python3
"""SymPy Hopf connection curvature versus bare Pauli-label gap baseline."""

from __future__ import annotations

import json
from pathlib import Path

import sympy as sp
from receipt_boundary import apply_default_receipt_boundary


NAME = "sympy_hopf_connection_curvature_pauli_label_gap"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "computes exact Hopf connection curvature and compares it with zero-coordinate Pauli-label controls"
        ),
    }
}
TOOL_INTEGRATION_DEPTH = {"sympy": "supportive"}

theta, phi = sp.symbols("theta phi", real=True)


def curvature_coeff(a_theta: sp.Expr, a_phi: sp.Expr) -> sp.Expr:
    return sp.simplify(sp.diff(a_phi, theta) - sp.diff(a_theta, phi))


def integrate_s2(two_form_coeff: sp.Expr) -> sp.Expr:
    return sp.simplify(sp.integrate(sp.integrate(two_form_coeff, (theta, 0, sp.pi)), (phi, 0, 2 * sp.pi)))


def pauli_matrices() -> dict[str, sp.Matrix]:
    return {
        "sigma_x": sp.Matrix([[0, 1], [1, 0]]),
        "sigma_y": sp.Matrix([[0, -sp.I], [sp.I, 0]]),
        "sigma_z": sp.Matrix([[1, 0], [0, -1]]),
    }


def matrix_entries_have_no_base_derivative(matrix: sp.Matrix) -> bool:
    return all(sp.simplify(sp.diff(entry, theta)) == 0 and sp.simplify(sp.diff(entry, phi)) == 0 for entry in matrix)


def run_positive() -> dict[str, object]:
    hopf_a_theta = sp.Integer(0)
    hopf_a_phi = sp.cos(theta) / 2
    hopf_f = curvature_coeff(hopf_a_theta, hopf_a_phi)
    hopf_integral = integrate_s2(hopf_f)
    hopf_c1 = sp.simplify(hopf_integral / (2 * sp.pi))
    return {
        "A_theta": str(hopf_a_theta),
        "A_phi": str(hopf_a_phi),
        "curvature_F_theta_phi": str(hopf_f),
        "curvature_integral_over_s2": str(hopf_integral),
        "first_chern_signed": str(hopf_c1),
        "survives_hopf_connection_readout": bool(
            sp.simplify(hopf_f + sp.sin(theta) / 2) == 0 and sp.simplify(hopf_c1 + 1) == 0
        ),
    }


def run_graveyards() -> dict[str, object]:
    paulis = pauli_matrices()
    pauli_derivative_rows = {
        name: matrix_entries_have_no_base_derivative(matrix)
        for name, matrix in paulis.items()
    }

    label_only_a_theta = sp.Integer(0)
    label_only_a_phi = sp.Integer(0)
    label_only_f = curvature_coeff(label_only_a_theta, label_only_a_phi)
    label_only_integral = integrate_s2(label_only_f)

    diagonal_label_a_phi = sp.Integer(1)
    diagonal_label_f = curvature_coeff(sp.Integer(0), diagonal_label_a_phi)

    offdiag_label_a_phi = sp.Integer(1)
    offdiag_label_f = curvature_coeff(sp.Integer(0), offdiag_label_a_phi)

    signed_hopf_f = -sp.sin(theta) / 2
    reversed_signed_hopf_f = sp.sin(theta) / 2
    signed_c1 = sp.simplify(integrate_s2(signed_hopf_f) / (2 * sp.pi))
    reversed_c1 = sp.simplify(integrate_s2(reversed_signed_hopf_f) / (2 * sp.pi))

    return {
        "pauli_matrices_have_no_base_coordinate_derivatives": {
            "entries_derivative_free": pauli_derivative_rows,
            "passed": bool(all(pauli_derivative_rows.values())),
        },
        "pauli_label_only_connection_has_zero_curvature": {
            "A_theta": str(label_only_a_theta),
            "A_phi": str(label_only_a_phi),
            "F_theta_phi": str(label_only_f),
            "integral": str(label_only_integral),
            "passed": bool(label_only_f == 0 and label_only_integral == 0),
        },
        "diagonal_offdiagonal_partition_cannot_supply_sin_theta_area_form": {
            "diagonal_label_F_theta_phi": str(diagonal_label_f),
            "offdiag_label_F_theta_phi": str(offdiag_label_f),
            "expected_hopf_F_theta_phi": str(signed_hopf_f),
            "passed": bool(diagonal_label_f == 0 and offdiag_label_f == 0 and sp.simplify(signed_hopf_f) != 0),
        },
        "orientation_sign_requires_connection_orientation_not_pauli_label": {
            "signed_first_chern": str(signed_c1),
            "reversed_first_chern": str(reversed_c1),
            "pauli_label_orientation": None,
            "passed": bool(sp.simplify(signed_c1 + 1) == 0 and sp.simplify(reversed_c1 - 1) == 0),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_hopf_connection_readout"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "SymPy Hopf connection curvature versus bare Pauli-label negative-control baseline only; shows that "
            "constant Pauli matrices and diagonal/off-diagonal labels do not carry the base-coordinate curvature "
            "form by themselves; no flux admission, no Pauli-to-flux shortcut, no physical dynamics, no QIT, "
            "GStack, axis, bridge, nonclassical, or target-system claim"
        ),
        "next_lego_target": "bare_pauli_no_carrier_negative_control",
        "promotion_condition": (
            "May only support later geometry planning as a negative control after carrier/topology receipts define "
            "the connection or curvature object explicitly."
        ),
        "demotion_condition": (
            "Demote if Pauli label-only controls produce nonzero base curvature, if the Hopf connection curvature "
            "does not integrate to signed first-Chern value -1, or if orientation controls fail to flip sign."
        ),
        "blocked_until": (
            "blocked from target-system or flux claims until a full carrier/topology implementation defines the "
            "connection, orientation, and physical readout family"
        ),
        "out_of_scope": [
            "No flux representation or Pauli-to-flux map.",
            "No physical Weyl-sheet dynamics.",
            "No nested Hopf-torus geometric-constraint-manifold implementation.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "The positive object is Hopf connection curvature. The Pauli controls are deliberately too weak: they "
            "are constant matrix labels and therefore do not encode the base-coordinate area form without an "
            "external carrier/connection construction."
        ),
        "operation_sequence": [
            "declare the Hopf connection coefficient A_phi = cos(theta)/2",
            "differentiate the connection coefficient to obtain F_theta_phi",
            "integrate the curvature coefficient over the base sphere coordinates",
            "construct constant Pauli matrices as label-only controls",
            "check that Pauli labels and diagonal/off-diagonal partitions have zero base-coordinate curvature",
            "check that orientation sign lives in the connection orientation control, not in a Pauli label alone",
        ],
        "carrier_topology": (
            "local Hopf U(1) bundle connection chart contrasted with carrier-free Pauli matrix labels"
        ),
        "observable": (
            "curvature coefficient F_theta_phi, first-Chern integral, Pauli matrix base-coordinate derivatives, "
            "and label-only curvature controls"
        ),
        "pass_fail_predicate": (
            "Hopf connection curvature is -sin(theta)/2 with signed first-Chern value -1; Pauli matrix labels and "
            "diagonal/off-diagonal partitions have zero base-coordinate curvature; reversing connection orientation "
            "flips first-Chern sign"
        ),
        "graveyards": [
            "Pauli matrices have no base-coordinate derivatives",
            "Pauli label-only connection has zero curvature",
            "diagonal/off-diagonal partition cannot supply sin(theta) area form",
            "orientation sign requires connection orientation rather than Pauli label alone",
        ],
        "baselines": [
            "SymPy Hopf connection curvature and first-Chern integral",
            "SymPy bare Pauli orientation partition baseline",
            "SymPy Hopf density derivative readout baseline",
        ],
        "alternative_formulations": [
            "Clifford rotor orientation negative control without Hopf connection",
            "QuTiP/Qiskit density-object readout with and without path coordinates",
            "GUDHI or TopoNetX nested torus carrier approximation with curvature-like cochain",
        ],
        "exact_tool_function_needs": {
            "sympy": ["Matrix", "symbols", "diff", "integrate", "simplify"],
        },
        "lego_or_coupling_target": "bare_pauli_no_carrier_negative_control",
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
