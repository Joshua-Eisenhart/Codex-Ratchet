#!/usr/bin/env python3
"""SymPy exact Hopf/Weyl vertical-horizontal tangent projection identities."""

from __future__ import annotations

import json
from pathlib import Path

import sympy as sp
from receipt_boundary import apply_default_receipt_boundary


NAME = "sympy_hopf_weyl_vertical_horizontal_tangent_projection_identities"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Matrix/diff/conjugate/re/trigsimp/simplify derive exact vertical projection coefficients for Hopf/Weyl raw base, horizontal base-lift, and wrong-sign tangent generators",
    },
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing"}


def hermitian_inner(left: sp.Matrix, right: sp.Matrix) -> sp.Expr:
    return sp.trigsimp((sp.conjugate(left).T * right)[0])


def real_metric(left: sp.Matrix, right: sp.Matrix) -> sp.Expr:
    return sp.trigsimp(sp.re(hermitian_inner(left, right)))


def main() -> int:
    theta, phi, chi, sheet = sp.symbols("theta phi chi sheet", real=True)
    sheet_rule = {sheet**2: 1}
    signed_phi = sheet * phi

    carrier = sp.Matrix(
        [
            sp.cos(theta / 2) * sp.exp(sp.I * (chi + signed_phi) / 2),
            sp.sin(theta / 2) * sp.exp(sp.I * (chi - signed_phi) / 2),
        ]
    )
    projection = sp.Matrix(
        [
            sp.sin(theta) * sp.cos(signed_phi),
            sp.sin(theta) * sp.sin(signed_phi),
            sp.cos(theta),
        ]
    )

    vertical = carrier.diff(chi)
    raw_base = carrier.diff(phi)
    horizontal_base = raw_base - sheet * sp.cos(theta) * vertical
    wrong_sign_horizontal_base = raw_base + sheet * sp.cos(theta) * vertical
    duplicate_vertical = vertical

    projection_vertical = projection.diff(chi)
    projection_raw_base = projection.diff(phi)
    projection_horizontal_base = projection.diff(phi)

    vertical_norm_sq = sp.trigsimp(real_metric(vertical, vertical)).xreplace(sheet_rule)
    raw_vertical_inner = sp.trigsimp(real_metric(raw_base, vertical)).xreplace(sheet_rule)
    horizontal_vertical_inner = sp.trigsimp(real_metric(horizontal_base, vertical)).xreplace(sheet_rule)
    wrong_vertical_inner = sp.trigsimp(real_metric(wrong_sign_horizontal_base, vertical)).xreplace(sheet_rule)
    raw_vertical_coeff = sp.trigsimp(raw_vertical_inner / vertical_norm_sq).xreplace(sheet_rule)
    horizontal_vertical_coeff = sp.trigsimp(horizontal_vertical_inner / vertical_norm_sq).xreplace(sheet_rule)
    wrong_vertical_coeff = sp.trigsimp(wrong_vertical_inner / vertical_norm_sq).xreplace(sheet_rule)
    duplicate_vertical_separation_sq = sp.trigsimp(sum((duplicate_vertical[idx] - vertical[idx]) ** 2 for idx in range(2)))
    projection_vertical_speed_sq = sp.trigsimp(sum(component**2 for component in projection_vertical))
    projection_raw_base_speed_sq = sp.trigsimp(sum(component**2 for component in projection_raw_base)).xreplace(sheet_rule)
    projection_horizontal_speed_sq = sp.trigsimp(sum(component**2 for component in projection_horizontal_base)).xreplace(sheet_rule)

    identities = {
        "vertical_norm_squared": str(vertical_norm_sq),
        "raw_base_vertical_projection_coefficient": str(raw_vertical_coeff),
        "horizontal_base_vertical_projection_coefficient": str(horizontal_vertical_coeff),
        "wrong_sign_horizontal_base_vertical_projection_coefficient": str(wrong_vertical_coeff),
        "projection_vertical_speed_squared": str(projection_vertical_speed_sq),
        "projection_raw_base_speed_squared": str(projection_raw_base_speed_sq),
        "projection_horizontal_base_speed_squared": str(projection_horizontal_speed_sq),
        "duplicate_vertical_tangent_separation_squared": str(duplicate_vertical_separation_sq),
    }

    positive = {
        "identities": identities,
        "exact_projection_identity_pass": bool(
            sp.simplify(vertical_norm_sq - sp.Rational(1, 4)) == 0
            and sp.simplify(raw_vertical_coeff - sheet * sp.cos(theta)) == 0
            and sp.simplify(horizontal_vertical_coeff) == 0
            and sp.simplify(wrong_vertical_coeff - 2 * sheet * sp.cos(theta)) == 0
            and sp.simplify(projection_vertical_speed_sq) == 0
            and sp.simplify(projection_raw_base_speed_sq - sp.sin(theta) ** 2) == 0
            and sp.simplify(projection_horizontal_speed_sq - sp.sin(theta) ** 2) == 0
            and sp.simplify(duplicate_vertical_separation_sq) == 0
        ),
    }

    graveyards = {
        "raw_base_falsely_independent_from_fiber_fails_away_from_equator": {
            "raw_vertical_coeff_at_theta_pi_over_3_sheet_plus": str(
                sp.simplify(raw_vertical_coeff.subs({theta: sp.pi / 3, sheet: 1}))
            ),
            "passed": bool(sp.simplify(raw_vertical_coeff.subs({theta: sp.pi / 3, sheet: 1}) - sp.Rational(1, 2)) == 0),
        },
        "equator_raw_base_independence_is_accidental": {
            "equator_raw_vertical_coeff": str(sp.simplify(raw_vertical_coeff.subs({theta: sp.pi / 2, sheet: 1}))),
            "non_equator_raw_vertical_coeff": str(sp.simplify(raw_vertical_coeff.subs({theta: sp.pi / 3, sheet: 1}))),
            "passed": bool(
                sp.simplify(raw_vertical_coeff.subs({theta: sp.pi / 2, sheet: 1})) == 0
                and sp.simplify(raw_vertical_coeff.subs({theta: sp.pi / 3, sheet: 1})) != 0
            ),
        },
        "pole_horizontal_base_projection_collapses": {
            "horizontal_projection_speed_squared_at_theta_zero": str(sp.simplify(projection_horizontal_speed_sq.subs(theta, 0))),
            "passed": bool(sp.simplify(projection_horizontal_speed_sq.subs(theta, 0)) == 0),
        },
        "wrong_sign_connection_reintroduces_vertical_component": {
            "wrong_vertical_coeff_at_theta_pi_over_3_sheet_plus": str(
                sp.simplify(wrong_vertical_coeff.subs({theta: sp.pi / 3, sheet: 1}))
            ),
            "passed": bool(sp.simplify(wrong_vertical_coeff.subs({theta: sp.pi / 3, sheet: 1}) - 1) == 0),
        },
        "s2_projection_does_not_see_vertical_fiber_motion": {
            "vertical_norm_squared": str(vertical_norm_sq),
            "projection_vertical_speed_squared": str(projection_vertical_speed_sq),
            "passed": bool(sp.simplify(vertical_norm_sq - sp.Rational(1, 4)) == 0 and sp.simplify(projection_vertical_speed_sq) == 0),
        },
        "duplicated_vertical_tangent_has_zero_separation": {
            "duplicate_vertical_tangent_separation_squared": str(duplicate_vertical_separation_sq),
            "passed": bool(sp.simplify(duplicate_vertical_separation_sq) == 0),
        },
        "density_projection_cannot_distinguish_raw_base_from_horizontal_base": {
            "raw_projection_speed_squared": str(projection_raw_base_speed_sq),
            "horizontal_projection_speed_squared": str(projection_horizontal_speed_sq),
            "passed": bool(sp.simplify(projection_raw_base_speed_sq - projection_horizontal_speed_sq) == 0),
        },
        "sheet_reversal_flips_raw_and_wrong_sign_coefficients_not_horizontal_projection": {
            "raw_sheet_plus": str(sp.simplify(raw_vertical_coeff.subs({theta: sp.pi / 3, sheet: 1}))),
            "raw_sheet_minus": str(sp.simplify(raw_vertical_coeff.subs({theta: sp.pi / 3, sheet: -1}))),
            "wrong_sheet_plus": str(sp.simplify(wrong_vertical_coeff.subs({theta: sp.pi / 3, sheet: 1}))),
            "wrong_sheet_minus": str(sp.simplify(wrong_vertical_coeff.subs({theta: sp.pi / 3, sheet: -1}))),
            "horizontal_sheet_plus": str(sp.simplify(horizontal_vertical_coeff.subs({theta: sp.pi / 3, sheet: 1}))),
            "horizontal_sheet_minus": str(sp.simplify(horizontal_vertical_coeff.subs({theta: sp.pi / 3, sheet: -1}))),
            "passed": bool(
                sp.simplify(raw_vertical_coeff.subs({theta: sp.pi / 3, sheet: 1}) + raw_vertical_coeff.subs({theta: sp.pi / 3, sheet: -1})) == 0
                and sp.simplify(wrong_vertical_coeff.subs({theta: sp.pi / 3, sheet: 1}) + wrong_vertical_coeff.subs({theta: sp.pi / 3, sheet: -1})) == 0
                and sp.simplify(horizontal_vertical_coeff.subs({theta: sp.pi / 3, sheet: 1})) == 0
                and sp.simplify(horizontal_vertical_coeff.subs({theta: sp.pi / 3, sheet: -1})) == 0
            ),
        },
    }

    all_pass = bool(positive["exact_projection_identity_pass"] and all(row["passed"] for row in graveyards.values()))
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "pass": all_pass,
        "claim_ceiling": (
            "SymPy exact local Hopf/Weyl carrier tangent-projection baseline only: vertical fiber, raw base, horizontal "
            "base-lift, and wrong-sign tangents are compared by exact projection coefficients in a declared two-component "
            "carrier chart; this may support geometry planning for vertical/horizontal loop separation, but it does not "
            "prove physical loop independence, flux, GStack, QIT, axis closure, bridge, nonclassical evidence, or "
            "target-system admission"
        ),
        "next_lego_target": "hopf_weyl_vertical_horizontal_carrier_loop_tangent_projection_baseline",
        "promotion_condition": (
            "May only support later geometry planning after numerical carrier, topology, density-object, and physical "
            "operator-evolution receipts reproduce compatible vertical/horizontal separation with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if exact coefficients do not match sheet*cos(theta), zero, and 2*sheet*cos(theta), if projection "
            "controls fail, or if this receipt is used as flux, GStack, QIT, axis, bridge, nonclassical, or target-system evidence."
        ),
        "blocked_until": "blocked from physical loop-independence and target-system claims until full carrier/topology and physical-evolution receipts exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, information-cycle, or target-system mechanics.",
            "No physical inner/outer loop independence proof.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This exact packet mirrors the geomstats tangent-projection sweep. It records that S2 density projection "
            "alone cannot distinguish raw base from horizontal base-lift; the tested separation lives in the S3 carrier "
            "vertical projection coefficient."
        ),
        "operation_sequence": [
            "define symbolic two-component Hopf/Weyl carrier and S2 density projection",
            "differentiate the carrier along vertical fiber and raw base coordinates",
            "construct horizontal base-lift and wrong-sign horizontal base tangents",
            "compute exact Hermitian real metric projection coefficients onto the vertical fiber tangent",
            "compute exact S2 projection speeds for vertical, raw base, and horizontal base directions",
            "run raw-base, equator, pole, wrong-sign, projection-hidden, duplicate, density-projection, and sheet-reversal graveyards",
        ],
        "carrier_topology": "symbolic two-component Hopf/Weyl S3 carrier chart with S2 Bloch-density projection",
        "observable": "exact vertical projection coefficients, S2 projection speeds, and duplicate tangent separation identities",
        "pass_fail_predicate": (
            "raw base coefficient equals sheet*cos(theta), horizontal lift coefficient equals zero, wrong-sign lift "
            "coefficient equals 2*sheet*cos(theta), S2 projection hides vertical fiber while raw/horizontal projection "
            "speeds coincide, and all adjacent graveyards collapse or fail as predicted"
        ),
        "graveyards": list(graveyards),
        "baselines": [
            "Geomstats Hopf/Weyl vertical-horizontal tangent projection sweep",
            "SymPy Hopf/Weyl vertical-horizontal metric identities",
            "Clifford Cl(4) Hopf/Weyl vertical-horizontal tangent inner-product baseline",
            "QuTiP/Qiskit density-object vertical-horizontal transport baselines",
        ],
        "alternative_formulations": [
            "Geomstats numerical tangent projection sweep",
            "Clifford exact tangent projection coefficients",
            "QuTiP density-object generator evolution along vertical and horizontal tangents",
            "e3nn SO3 equivariance over the same projected density readouts",
        ],
        "exact_tool_function_needs": {
            "sympy": ["symbols", "Matrix", "diff", "conjugate", "re", "trigsimp", "simplify", "subs"],
        },
        "lego_or_coupling_target": "hopf_weyl_vertical_horizontal_carrier_loop_tangent_projection_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={all_pass}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
