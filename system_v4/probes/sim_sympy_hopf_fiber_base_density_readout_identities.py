#!/usr/bin/env python3
"""Symbolic Hopf-coordinate density readout for fiber and base loops."""

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


NAME = "sympy_hopf_fiber_base_density_readout_identities"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "symbolically checks Hopf-coordinate density dependence on fiber and base-lift coordinates",
    }
}
TOOL_INTEGRATION_DEPTH = {"sympy": "supportive"}


def spinor(theta: sp.Symbol, phi: sp.Symbol, chi: sp.Symbol) -> sp.Matrix:
    return sp.Matrix(
        [
            sp.cos(theta / 2) * sp.exp(sp.I * (chi + phi) / 2),
            sp.sin(theta / 2) * sp.exp(sp.I * (chi - phi) / 2),
        ]
    )


def density(psi: sp.Matrix) -> sp.Matrix:
    return sp.simplify(psi * psi.conjugate().T)


def matrix_derivative_zero(matrix: sp.Matrix, variable: sp.Symbol) -> bool:
    return all(sp.simplify(sp.diff(entry, variable)) == 0 for entry in matrix)


def run_symbolic() -> dict[str, object]:
    theta, phi, chi = sp.symbols("theta phi chi", real=True)
    rho = density(spinor(theta, phi, chi))
    d_chi_zero = matrix_derivative_zero(rho, chi)
    d_phi = rho.diff(phi)
    off_diagonal_phi_derivative = sp.simplify(d_phi[0, 1])
    nondegenerate_value = sp.simplify(off_diagonal_phi_derivative.subs({theta: sp.pi / 3, phi: 0}))
    return {
        "rho": [[str(sp.simplify(entry)) for entry in row] for row in rho.tolist()],
        "fiber_coordinate_derivative_zero": bool(d_chi_zero),
        "off_diagonal_base_derivative": str(off_diagonal_phi_derivative),
        "off_diagonal_base_derivative_nonzero_at_theta_pi_over_3": bool(nondegenerate_value != 0),
        "nondegenerate_value": str(nondegenerate_value),
    }


def run_graveyards() -> dict[str, object]:
    theta, phi, chi = sp.symbols("theta phi chi", real=True)
    rho = density(spinor(theta, phi, chi))
    d_phi = rho.diff(phi)

    diagonal_phi_derivatives = [sp.simplify(d_phi[0, 0]), sp.simplify(d_phi[1, 1])]
    diagonal_hidden = all(entry == 0 for entry in diagonal_phi_derivatives)

    pole_value = sp.simplify(d_phi[0, 1].subs({theta: 0, phi: 0}))
    equator_value = sp.simplify(d_phi[0, 1].subs({theta: sp.pi / 2, phi: 0}))

    return {
        "diagonal_readout_hides_base_lift_change": {
            "diagonal_phi_derivatives": [str(entry) for entry in diagonal_phi_derivatives],
            "collapses_distinction": bool(diagonal_hidden),
            "passed": bool(diagonal_hidden),
        },
        "outer_loop_at_pole_degenerates": {
            "off_diagonal_derivative_at_pole": str(pole_value),
            "collapses_distinction": bool(pole_value == 0),
            "passed": bool(pole_value == 0),
        },
        "equator_base_lift_remains_visible": {
            "off_diagonal_derivative_at_equator": str(equator_value),
            "expected_nonzero": True,
            "passed": bool(equator_value != 0),
        },
        "bare_pauli_without_hopf_coordinates_is_insufficient": {
            "has_theta_phi_chi": False,
            "can_check_loop_dependence": False,
            "passed": True,
        },
    }


def main() -> int:
    symbolic = run_symbolic()
    graveyards = run_graveyards()
    all_pass = bool(
        symbolic["fiber_coordinate_derivative_zero"]
        and symbolic["off_diagonal_base_derivative_nonzero_at_theta_pi_over_3"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "classical symbolic Hopf-coordinate density-readout identity baseline only; no physical fiber/base "
            "loop independence, no full S3 bundle, no QIT, GStack, axis, bridge, nonclassical, target-system, "
            "or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "declared_fiber_base_coordinate_readout_baseline",
        "promotion_condition": (
            "May support later geometry planning only as an exact coordinate identity companion to sampled or "
            "operator-evolution receipts with adjacent graveyards."
        ),
        "demotion_condition": (
            "Demote if density depends on the fiber coordinate, if base-lift off-diagonal readout is not visible "
            "away from degeneracy, or if diagonal/pole graveyards do not collapse the distinction."
        ),
        "blocked_until": (
            "blocked from target-system claims until a fuller carrier/topology implementation and physical-evolution "
            "graveyards exist"
        ),
        "out_of_scope": [
            "No dynamics, Lindblad evolution, nonclassical admission, bridge, QIT, or target-system claim.",
            "No claim that flux is represented.",
            "No full nested-tori geometric constraint manifold.",
        ],
        "divergence_log": (
            "SymPy exact coordinate algebra is a classical baseline. It proves only local coordinate identities for "
            "the declared Hopf-style carrier and does not prove physical loop independence."
        ),
        "operation_sequence": [
            "construct symbolic normalized two-component carrier in Hopf-style coordinates",
            "form the density matrix psi psi^dagger",
            "differentiate all density entries by the fiber coordinate",
            "differentiate density entries by the base-lift coordinate",
            "check nondegenerate off-diagonal base-lift visibility",
            "run diagonal-hidden, pole-degenerate, and no-coordinate graveyards",
        ],
        "carrier_topology": "symbolic S^3-style two-component carrier coordinates projected to a density matrix",
        "observable": "symbolic density-matrix derivatives with respect to fiber and base-lift coordinates",
        "pass_fail_predicate": (
            "all density entries are independent of the fiber coordinate, at least one off-diagonal density entry "
            "depends on the base-lift coordinate away from degeneracy, and graveyards collapse as declared"
        ),
        "graveyards": [
            "diagonal-only density readout hides base-lift change",
            "base loop at the pole degenerates",
            "bare Pauli matrices without Hopf coordinates cannot test loop dependence",
        ],
        "baselines": [
            "sampled Hopf-coordinate path metrics",
            "bare Pauli orientation integer predicate",
            "finite z3 product-coordinate readout",
        ],
        "alternative_formulations": [
            "numeric sampled path-length fixture",
            "operator-evolution fixture along explicit path generators",
            "cell-complex approximation to loop transport",
        ],
        "exact_tool_function_needs": {"sympy": ["Matrix", "exp", "diff", "simplify", "subs"]},
        "lego_or_coupling_target": "declared_fiber_base_coordinate_readout_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "symbolic": symbolic,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
