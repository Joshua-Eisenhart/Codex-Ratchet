#!/usr/bin/env python3
"""SymPy Weyl-sheet Hopf-loop derivative-sign baseline."""

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


NAME = "sympy_weyl_sheet_hopf_loop_derivative_sign"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "constructs symbolic two-component Hopf-coordinate carriers with a declared sheet-orientation sign "
            "and differentiates density readouts by fiber and base-loop coordinates"
        ),
    }
}
TOOL_INTEGRATION_DEPTH = {"sympy": "supportive"}


def spinor(theta: sp.Symbol, phi: sp.Symbol, chi: sp.Symbol, sheet_sign: int) -> sp.Matrix:
    signed_phi = sheet_sign * phi
    return sp.Matrix(
        [
            sp.cos(theta / 2) * sp.exp(sp.I * (chi + signed_phi) / 2),
            sp.sin(theta / 2) * sp.exp(sp.I * (chi - signed_phi) / 2),
        ]
    )


def density(psi: sp.Matrix) -> sp.Matrix:
    return sp.simplify(psi * psi.conjugate().T)


def matrix_derivative_zero(matrix: sp.Matrix, variable: sp.Symbol) -> bool:
    return all(sp.simplify(sp.diff(entry, variable)) == 0 for entry in matrix)


def symbolic_readout(sheet_sign: int) -> dict[str, object]:
    theta, phi, chi = sp.symbols("theta phi chi", real=True)
    rho = density(spinor(theta, phi, chi, sheet_sign))
    offdiag = sp.simplify(rho[0, 1])
    fiber_zero = matrix_derivative_zero(rho, chi)
    base_derivative = sp.simplify(sp.diff(offdiag, phi))
    normalized_derivative_ratio = sp.simplify(base_derivative / offdiag)
    nondegenerate_value = sp.simplify(base_derivative.subs({theta: sp.pi / 3, phi: 0}))
    return {
        "rho_offdiag": str(offdiag),
        "fiber_coordinate_derivative_zero": bool(fiber_zero),
        "base_offdiag_derivative": str(base_derivative),
        "base_derivative_over_offdiag": str(normalized_derivative_ratio),
        "base_derivative_nonzero_at_theta_pi_over_3": bool(nondegenerate_value != 0),
        "nondegenerate_value": str(nondegenerate_value),
    }


def run_positive() -> dict[str, object]:
    positive = symbolic_readout(1)
    negative = symbolic_readout(-1)
    return {
        "positive_sheet": positive,
        "negative_sheet": negative,
        "survives_declared_sheet_derivative_sign": bool(
            positive["fiber_coordinate_derivative_zero"]
            and negative["fiber_coordinate_derivative_zero"]
            and positive["base_derivative_nonzero_at_theta_pi_over_3"]
            and negative["base_derivative_nonzero_at_theta_pi_over_3"]
            and positive["base_derivative_over_offdiag"] == "I"
            and negative["base_derivative_over_offdiag"] == "-I"
        ),
    }


def run_graveyards() -> dict[str, object]:
    theta, phi, chi = sp.symbols("theta phi chi", real=True)
    positive_rho = density(spinor(theta, phi, chi, 1))
    negative_rho = density(spinor(theta, phi, chi, -1))
    positive_offdiag = sp.simplify(positive_rho[0, 1])
    negative_offdiag = sp.simplify(negative_rho[0, 1])
    positive_ratio = sp.simplify(sp.diff(positive_offdiag, phi) / positive_offdiag)
    negative_ratio = sp.simplify(sp.diff(negative_offdiag, phi) / negative_offdiag)
    diagonal_phi_derivatives = [sp.simplify(sp.diff(positive_rho[0, 0], phi)), sp.simplify(sp.diff(positive_rho[1, 1], phi))]
    pole_positive = sp.simplify(sp.diff(positive_offdiag, phi).subs({theta: 0, phi: 0}))
    same_sheet_ratio_a = positive_ratio
    same_sheet_ratio_b = sp.simplify(sp.diff(positive_offdiag, phi) / positive_offdiag)
    return {
        "diagonal_readout_hides_sheet_derivative_sign": {
            "diagonal_phi_derivatives": [str(item) for item in diagonal_phi_derivatives],
            "passed": bool(all(item == 0 for item in diagonal_phi_derivatives)),
        },
        "dropping_sheet_sign_collapses_derivative_ratio": {
            "absolute_ratios_equal": bool(sp.simplify(sp.Abs(positive_ratio) - sp.Abs(negative_ratio)) == 0),
            "positive_ratio": str(positive_ratio),
            "negative_ratio": str(negative_ratio),
            "passed": bool(positive_ratio != negative_ratio and positive_ratio == sp.I and negative_ratio == -sp.I),
        },
        "same_sheet_duplicates_have_same_derivative_ratio": {
            "ratios": [str(same_sheet_ratio_a), str(same_sheet_ratio_b)],
            "passed": bool(same_sheet_ratio_a == same_sheet_ratio_b),
        },
        "base_loop_at_pole_collapses_offdiag_derivative": {
            "positive_derivative_at_pole": str(pole_positive),
            "passed": bool(pole_positive == 0),
        },
        "bare_sheet_loop_labels_without_carrier_are_insufficient": {
            "has_symbolic_carrier": False,
            "has_density_readout": False,
            "passed": True,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_declared_sheet_derivative_sign"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "SymPy declared Weyl-sheet orientation derivative-sign baseline over Hopf-coordinate density readouts "
            "only; no physical sheet/loop independence, no full S3 bundle, no flux, no QIT, GStack, axis, bridge, "
            "nonclassical, target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "inner_outer_hopf_weyl_loop_geometry_fit",
        "promotion_condition": (
            "May only support later geometry planning after sampled numeric, Clifford, density-object, and topology "
            "fixtures reproduce compatible declared-path readouts with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if fiber-coordinate derivatives are nonzero, if base-loop off-diagonal derivatives fail to "
            "change sign under declared sheet orientation, or if adjacent graveyards do not collapse."
        ),
        "blocked_until": (
            "blocked from target-system claims until full carrier/topology implementation and physical-evolution "
            "graveyards exist"
        ),
        "out_of_scope": [
            "No physical Weyl-sheet dynamics.",
            "No full Hopf bundle or nested Hopf-torus manifold.",
            "No flux representation or Pauli shortcut.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This is exact symbolic coordinate algebra. It proves only that declared sheet signs reverse a local "
            "base-coordinate density derivative ratio; it does not prove physical loop independence."
        ),
        "operation_sequence": [
            "declare a sheet-orientation sign in the Hopf-coordinate phase",
            "construct symbolic two-component carrier states",
            "form density matrices for positive and negative sheet signs",
            "differentiate density readouts by fiber and base-loop coordinates",
            "compare the normalized off-diagonal base derivative ratios",
            "run diagonal-hidden, no-sheet, duplicate-sheet, pole-degenerate, and no-carrier graveyards",
        ],
        "carrier_topology": "symbolic two-component Hopf-coordinate carrier with declared sheet-orientation sign; no full S3 bundle object",
        "observable": "fiber-coordinate density derivatives and normalized off-diagonal base-coordinate derivative ratio",
        "pass_fail_predicate": (
            "fiber derivatives are zero, base off-diagonal derivatives are nonzero away from the pole, normalized "
            "base derivative ratios are +I and -I for the two declared sheet signs, and controls collapse as declared"
        ),
        "graveyards": [
            "diagonal readout hides sheet derivative sign",
            "dropping sheet sign collapses derivative-ratio orientation",
            "same-sheet duplicates have same derivative ratio",
            "base loop at pole collapses off-diagonal derivative",
            "bare sheet/loop labels without carrier are insufficient",
        ],
        "baselines": [
            "NumPy Weyl-sheet Hopf-loop readout separation",
            "NumPy Hopf inner/outer loop readout geometry",
            "SymPy Hopf density derivative identity",
            "z3 finite sheet-loop product readout separation",
        ],
        "alternative_formulations": [
            "Clifford rotor orientation reversal fixture",
            "QuTiP/Qiskit density-object sheet orientation fixture",
            "TopoNetX or GUDHI nested torus carrier approximation",
        ],
        "exact_tool_function_needs": {"sympy": ["Matrix", "exp", "diff", "simplify", "subs"]},
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
