#!/usr/bin/env python3
"""SymPy exact S3 carrier and S2 projection identities for Hopf/Weyl fiber-base loops."""

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


NAME = "sympy_hopf_weyl_fiber_base_s3_s2_distance_identities"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "derives exact carrier and projection speed identities for declared Hopf/Weyl fiber-base coordinates",
    },
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing"}


def squared_norm(vec: sp.Matrix) -> sp.Expr:
    return sp.trigsimp(sum(component**2 for component in vec))


def main() -> int:
    theta, phi, chi, s = sp.symbols("theta phi chi s", real=True)
    s_assumptions = {s**2: 1}

    signed_phi = s * phi
    carrier = sp.Matrix(
        [
            sp.cos(theta / 2) * sp.cos((chi + signed_phi) / 2),
            sp.cos(theta / 2) * sp.sin((chi + signed_phi) / 2),
            sp.sin(theta / 2) * sp.cos((chi - signed_phi) / 2),
            sp.sin(theta / 2) * sp.sin((chi - signed_phi) / 2),
        ]
    )
    projection = sp.Matrix(
        [
            sp.sin(theta) * sp.cos(signed_phi),
            sp.sin(theta) * sp.sin(signed_phi),
            sp.cos(theta),
        ]
    )

    carrier_norm = sp.trigsimp(squared_norm(carrier))
    projection_norm = sp.trigsimp(squared_norm(projection))
    fiber_s3_speed_sq = sp.trigsimp(squared_norm(carrier.diff(chi)))
    base_s3_speed_sq = sp.trigsimp(squared_norm(carrier.diff(phi))).xreplace(s_assumptions)
    fiber_s2_speed_sq = sp.trigsimp(squared_norm(projection.diff(chi)))
    base_s2_speed_sq = sp.trigsimp(squared_norm(projection.diff(phi))).xreplace(s_assumptions)
    base_s2_speed_sq = sp.trigsimp(base_s2_speed_sq)

    positive = {
        "carrier_norm": str(carrier_norm),
        "projection_norm": str(projection_norm),
        "fiber_s3_speed_squared": str(fiber_s3_speed_sq),
        "base_s3_speed_squared": str(base_s3_speed_sq),
        "fiber_s2_speed_squared": str(fiber_s2_speed_sq),
        "base_s2_speed_squared": str(base_s2_speed_sq),
        "fiber_s3_length_over_0_to_2pi": "pi",
        "base_s3_length_over_0_to_2pi": "pi",
        "base_s2_length_over_0_to_2pi": "2*pi*Abs(sin(theta))",
    }

    graveyards = {
        "projection_to_s2_hides_fiber_carrier_motion": {
            "fiber_s3_speed_squared": str(fiber_s3_speed_sq),
            "fiber_s2_speed_squared": str(fiber_s2_speed_sq),
            "passed": bool(sp.simplify(fiber_s3_speed_sq - sp.Rational(1, 4)) == 0 and fiber_s2_speed_sq == 0),
        },
        "base_projection_collapses_at_pole": {
            "base_s2_speed_squared_at_theta_zero": str(sp.simplify(base_s2_speed_sq.subs(theta, 0))),
            "passed": bool(sp.simplify(base_s2_speed_sq.subs(theta, 0)) == 0),
        },
        "base_projection_is_visible_away_from_pole": {
            "base_s2_speed_squared_at_theta_pi_over_3": str(sp.simplify(base_s2_speed_sq.subs(theta, sp.pi / 3))),
            "passed": bool(sp.simplify(base_s2_speed_sq.subs(theta, sp.pi / 3) - sp.Rational(3, 4)) == 0),
        },
        "sheet_orientation_does_not_change_metric_speeds": {
            "base_s2_speed_squared_depends_on_s_squared_only": str(base_s2_speed_sq),
            "passed": bool(not base_s2_speed_sq.has(s)),
        },
        "s2_only_formulation_cannot_recover_fiber_carrier_length": {
            "s2_fiber_speed_squared": str(fiber_s2_speed_sq),
            "carrier_needed_for_fiber_length": True,
            "passed": bool(fiber_s2_speed_sq == 0 and fiber_s3_speed_sq == sp.Rational(1, 4)),
        },
    }

    all_pass = bool(
        carrier_norm == 1
        and projection_norm == 1
        and sp.simplify(fiber_s3_speed_sq - sp.Rational(1, 4)) == 0
        and sp.simplify(base_s3_speed_sq - sp.Rational(1, 4)) == 0
        and fiber_s2_speed_sq == 0
        and sp.simplify(base_s2_speed_sq - sp.sin(theta) ** 2) == 0
        and all(row["passed"] for row in graveyards.values())
    )

    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "SymPy exact identity baseline for declared Hopf/Weyl fiber-base S3 carrier and S2 projection coordinates only; "
            "no sampled dynamics, no physical fiber/base independence proof, no full nested Hopf-torus manifold, no flux, "
            "no QIT, GStack, axis, bridge, nonclassical, target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later carrier-geometry planning after compatible object-level, numerical metric, topology, "
            "and physical operator-evolution receipts reproduce the same fiber/base identities with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if carrier/projection norms are not exact one, if fiber S2 speed is nonzero, if base S2 speed fails "
            "to equal sin(theta)^2, or if pole/S2-only graveyards do not collapse."
        ),
        "blocked_until": "blocked from target-system claims until fuller carrier/topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, or information-cycle mechanics.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This exact symbolic chart explains the sampled S3/S2 metric baseline but remains a coordinate-identity baseline, "
            "not a full geometry or physical evolution result."
        ),
        "operation_sequence": [
            "define a real S3 embedding of the two-component Hopf/Weyl carrier",
            "define the S2 Bloch projection with declared sheet orientation sign",
            "compute exact carrier and projection norms",
            "differentiate the S3 carrier with respect to chi and phi",
            "differentiate the S2 projection with respect to chi and phi",
            "simplify squared speeds and run pole, sheet, and projection-hidden graveyards",
        ],
        "carrier_topology": "symbolic two-component Hopf-coordinate carrier embedded in S3 with S2 projection; no full nested-torus manifold",
        "observable": "exact squared speeds for S3 carrier and S2 projection under fiber coordinate chi and base coordinate phi",
        "pass_fail_predicate": (
            "carrier and projection norms equal one, fiber and base S3 speeds equal 1/4, fiber S2 speed equals zero, "
            "base S2 speed equals sin(theta)^2, and adjacent graveyards collapse as predicted"
        ),
        "graveyards": [
            "projection to S2 hides fiber carrier motion",
            "base projection collapses at pole",
            "base projection is visible away from pole",
            "sheet orientation does not change metric speeds",
            "S2-only formulation cannot recover fiber carrier length",
        ],
        "baselines": [
            "Geomstats Hopf/Weyl S3 carrier and S2 projection distance baseline",
            "PyTorch Hopf/Weyl fiber-base gradient readout baseline",
            "QuTiP/Qiskit Hopf/Weyl fiber-base carrier transport baselines",
        ],
        "alternative_formulations": [
            "Geomstats numerical intrinsic path length over the same coordinates",
            "QuTiP carrier-state trace-distance and density-projection controls",
            "Clifford spinor rotor formulation for carrier sign transport",
            "physical operator-evolution fixture over the same carrier samples",
        ],
        "exact_tool_function_needs": {
            "sympy": ["symbols", "Matrix", "diff", "trigsimp", "simplify", "subs"],
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
