#!/usr/bin/env python3
"""SymPy exact Hopf/Weyl fiber versus horizontal-base loop independence baseline."""

from __future__ import annotations

import json
from pathlib import Path

import sympy as sp
from receipt_boundary import apply_default_receipt_boundary


NAME = "sympy_hopf_weyl_fiber_horizontal_base_loop_independence"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "derives exact Hopf connection metric identities separating vertical fiber and horizontal base-lift loop generators",
    },
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing"}


def hermitian_inner(vec_a: sp.Matrix, vec_b: sp.Matrix) -> sp.Expr:
    return sp.trigsimp((sp.conjugate(vec_a).T * vec_b)[0])


def real_metric(vec_a: sp.Matrix, vec_b: sp.Matrix) -> sp.Expr:
    return sp.trigsimp(sp.re(hermitian_inner(vec_a, vec_b)))


def squared_norm(vec: sp.Matrix) -> sp.Expr:
    return real_metric(vec, vec)


def main() -> int:
    theta, phi, chi, sheet = sp.symbols("theta phi chi sheet", real=True)
    sheet_assumptions = {sheet**2: 1}
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

    fiber = carrier.diff(chi)
    raw_base = carrier.diff(phi)
    horizontal_base = raw_base - sheet * sp.cos(theta) * fiber
    projection_fiber = projection.diff(chi)
    projection_base = projection.diff(phi)

    carrier_norm = sp.trigsimp(hermitian_inner(carrier, carrier))
    projection_norm = sp.trigsimp(sum(component**2 for component in projection))
    fiber_speed_sq = sp.trigsimp(squared_norm(fiber))
    raw_base_speed_sq = sp.trigsimp(squared_norm(raw_base)).xreplace(sheet_assumptions)
    raw_base_fiber_inner = sp.trigsimp(real_metric(raw_base, fiber)).xreplace(sheet_assumptions)
    horizontal_fiber_inner = sp.trigsimp(real_metric(horizontal_base, fiber)).xreplace(sheet_assumptions)
    horizontal_speed_sq = sp.trigsimp(squared_norm(horizontal_base)).xreplace(sheet_assumptions)
    projection_fiber_speed_sq = sp.trigsimp(sum(component**2 for component in projection_fiber))
    projection_base_speed_sq = sp.trigsimp(sum(component**2 for component in projection_base)).xreplace(sheet_assumptions)

    horizontal_speed_sq = sp.trigsimp(horizontal_speed_sq)
    projection_base_speed_sq = sp.trigsimp(projection_base_speed_sq)

    positive = {
        "carrier_norm": str(carrier_norm),
        "projection_norm": str(projection_norm),
        "fiber_speed_squared": str(fiber_speed_sq),
        "raw_base_speed_squared": str(raw_base_speed_sq),
        "raw_base_fiber_metric_inner": str(raw_base_fiber_inner),
        "horizontal_base_fiber_metric_inner": str(horizontal_fiber_inner),
        "horizontal_base_speed_squared": str(horizontal_speed_sq),
        "projection_fiber_speed_squared": str(projection_fiber_speed_sq),
        "projection_base_speed_squared": str(projection_base_speed_sq),
        "horizontal_base_speed_to_projection_speed_ratio": "1/4 away from projection-collapse points",
    }

    graveyards = {
        "raw_base_coordinate_is_not_generically_independent_from_fiber": {
            "raw_base_fiber_metric_inner_at_theta_pi_over_3_sheet_plus": str(
                sp.simplify(raw_base_fiber_inner.subs({theta: sp.pi / 3, sheet: 1}))
            ),
            "passed": bool(
                sp.simplify(raw_base_fiber_inner.subs({theta: sp.pi / 3, sheet: 1}) - sp.Rational(1, 8)) == 0
            ),
        },
        "horizontal_lift_makes_base_generator_metric_independent_from_fiber": {
            "horizontal_base_fiber_metric_inner": str(horizontal_fiber_inner),
            "passed": bool(sp.simplify(horizontal_fiber_inner) == 0),
        },
        "base_lift_collapses_at_projection_pole": {
            "horizontal_base_speed_squared_at_theta_zero": str(sp.simplify(horizontal_speed_sq.subs(theta, 0))),
            "projection_base_speed_squared_at_theta_zero": str(sp.simplify(projection_base_speed_sq.subs(theta, 0))),
            "passed": bool(sp.simplify(horizontal_speed_sq.subs(theta, 0)) == 0 and sp.simplify(projection_base_speed_sq.subs(theta, 0)) == 0),
        },
        "fiber_motion_is_hidden_by_s2_projection": {
            "fiber_speed_squared_on_carrier": str(fiber_speed_sq),
            "fiber_speed_squared_after_projection": str(projection_fiber_speed_sq),
            "passed": bool(sp.simplify(fiber_speed_sq - sp.Rational(1, 4)) == 0 and projection_fiber_speed_sq == 0),
        },
        "equator_raw_base_independence_is_accidental_not_global": {
            "raw_base_fiber_metric_inner_at_theta_pi_over_2": str(
                sp.simplify(raw_base_fiber_inner.subs(theta, sp.pi / 2))
            ),
            "raw_base_fiber_metric_inner_at_theta_pi_over_3": str(
                sp.simplify(raw_base_fiber_inner.subs({theta: sp.pi / 3, sheet: 1}))
            ),
            "passed": bool(
                sp.simplify(raw_base_fiber_inner.subs(theta, sp.pi / 2)) == 0
                and sp.simplify(raw_base_fiber_inner.subs({theta: sp.pi / 3, sheet: 1})) != 0
            ),
        },
        "sheet_sign_changes_raw_connection_sign_but_not_horizontal_independence": {
            "raw_inner_sheet_plus": str(sp.simplify(raw_base_fiber_inner.subs({theta: sp.pi / 3, sheet: 1}))),
            "raw_inner_sheet_minus": str(sp.simplify(raw_base_fiber_inner.subs({theta: sp.pi / 3, sheet: -1}))),
            "horizontal_inner_sheet_plus": str(sp.simplify(horizontal_fiber_inner.subs({theta: sp.pi / 3, sheet: 1}))),
            "horizontal_inner_sheet_minus": str(sp.simplify(horizontal_fiber_inner.subs({theta: sp.pi / 3, sheet: -1}))),
            "passed": bool(
                sp.simplify(raw_base_fiber_inner.subs({theta: sp.pi / 3, sheet: 1}) + raw_base_fiber_inner.subs({theta: sp.pi / 3, sheet: -1})) == 0
                and sp.simplify(horizontal_fiber_inner.subs({theta: sp.pi / 3, sheet: 1})) == 0
                and sp.simplify(horizontal_fiber_inner.subs({theta: sp.pi / 3, sheet: -1})) == 0
            ),
        },
    }

    all_pass = bool(
        sp.simplify(carrier_norm - 1) == 0
        and sp.simplify(projection_norm - 1) == 0
        and sp.simplify(fiber_speed_sq - sp.Rational(1, 4)) == 0
        and sp.simplify(raw_base_speed_sq - sp.Rational(1, 4)) == 0
        and sp.simplify(raw_base_fiber_inner - sheet * sp.cos(theta) / 4) == 0
        and sp.simplify(horizontal_fiber_inner) == 0
        and sp.simplify(horizontal_speed_sq - sp.sin(theta) ** 2 / 4) == 0
        and projection_fiber_speed_sq == 0
        and sp.simplify(projection_base_speed_sq - sp.sin(theta) ** 2) == 0
        and all(row["passed"] for row in graveyards.values())
    )

    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "SymPy exact Hopf/Weyl carrier metric baseline for vertical fiber and horizontal base-lift loop generators only; "
            "it proves coordinate identities in a declared two-component carrier chart, not physical loop independence in a "
            "full nested Hopf-torus geometric-constraint manifold; no flux representation, no QIT, no GStack, no axis, "
            "no bridge, no nonclassical admission, and no target-system admission"
        ),
        "next_lego_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later geometry planning after numerical carrier-distance, topology, Clifford/spinor, and "
            "physical operator-evolution receipts reproduce the same vertical/horizontal separation with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if the raw base coordinate is treated as independent without the Hopf connection correction, if "
            "horizontal base is not metric-orthogonal to fiber, or if projection/pole/sheet-sign graveyards do not collapse."
        ),
        "blocked_until": "blocked from target-system claims until full carrier/topology and physical-evolution receipts exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, or information-cycle mechanics.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This exact identity packet sharpens the earlier fiber/base baselines: raw base motion is not globally "
            "independent from the fiber; only the horizontal base lift is metric-independent. It remains a coordinate "
            "geometry baseline, not a full physical carrier simulation."
        ),
        "operation_sequence": [
            "define the two-component Hopf/Weyl carrier with sheet sign on phi",
            "define the S2 projection of the carrier",
            "differentiate the carrier along the fiber coordinate chi",
            "differentiate the carrier along the raw base coordinate phi",
            "construct the horizontal base-lift generator by subtracting the Hopf connection vertical component",
            "compute exact metric inner products and squared speeds for fiber, raw base, and horizontal base",
            "compare carrier-level speeds with S2 projection readouts and adjacent graveyards",
        ],
        "carrier_topology": "symbolic two-component Hopf-coordinate carrier with vertical fiber and horizontal base-lift generators; no full nested-torus manifold",
        "observable": "exact Hermitian metric inner products and squared speeds for fiber, raw-base, horizontal-base, and S2-projected loops",
        "pass_fail_predicate": (
            "fiber speed equals 1/4, raw base has nonzero fiber inner product sheet*cos(theta)/4, horizontal base has "
            "zero fiber inner product and speed sin(theta)^2/4, S2 projection hides fiber and sees base speed sin(theta)^2, "
            "and all adjacent controls collapse as predicted"
        ),
        "graveyards": [
            "raw base coordinate is not generically independent from fiber",
            "horizontal lift makes base generator metric-independent from fiber",
            "base lift collapses at projection pole",
            "fiber motion is hidden by S2 projection",
            "equator raw-base independence is accidental not global",
            "sheet sign changes raw connection sign but not horizontal independence",
        ],
        "baselines": [
            "SymPy Hopf/Weyl fiber-base S3/S2 distance identities",
            "Geomstats Hopf/Weyl S3 carrier and S2 projection distance baseline",
            "PyTorch Hopf/Weyl fiber-base gradient readout baseline",
        ],
        "alternative_formulations": [
            "Geomstats numerical S3/S2 path length using the horizontal base lift",
            "QuTiP density-object transport along vertical and horizontal generators",
            "Clifford rotor/spinor representation of the same vertical/horizontal metric separation",
            "operator-evolution fixture over vertical and horizontal carrier paths",
        ],
        "exact_tool_function_needs": {
            "sympy": ["symbols", "Matrix", "diff", "conjugate", "re", "trigsimp", "simplify", "subs"],
        },
        "lego_or_coupling_target": "hopf_weyl_carrier_loop_geometry_baseline",
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
