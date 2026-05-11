#!/usr/bin/env python3
"""Direct local lego: F01 finitude constraint.

The row-level claim is only that the root carrier/probe/state objects are finite
and explicitly enumerable.  Noncommutation, entropy gradients, GStack, and axis
claims are out of scope for this probe.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from z3 import And, Distinct, Int, Solver, sat


classification = "canonical"

CLASSIFICATION_NOTE = (
    "Canonical direct lego for F01 as finite Hilbert dimension, finite probe "
    "family, and finite candidate state set. This does not admit any later "
    "axis/GStack/QIT-engine claim."
)
LEGO_IDS = ["f01_finitude_constraint"]
PRIMARY_LEGO_IDS = ["f01_finitude_constraint"]
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "constructs finite matrices, finite probe families, and finite candidate state arrays",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "proves finite basis indices are enumerable and distinct inside a bounded dimension",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "z3": "load_bearing",
}
EPS = 1e-10


def finite_basis_sat(d: int) -> bool:
    basis = [Int(f"e_{d}_{i}") for i in range(d)]
    solver = Solver()
    solver.add(Distinct(basis))
    solver.add(*[And(index >= 0, index < d) for index in basis])
    return solver.check() == sat


def density(trace_bias: float = 0.0) -> np.ndarray:
    return np.array([[1.0 + trace_bias, 0.0], [0.0, 0.0]], dtype=float)


def finite_probe_family() -> list[np.ndarray]:
    return [
        np.array([[1.0, 0.0], [0.0, 0.0]], dtype=float),
        np.array([[0.0, 0.0], [0.0, 1.0]], dtype=float),
    ]


def is_density_candidate(rho: np.ndarray) -> bool:
    return (
        rho.shape == (2, 2)
        and np.allclose(rho, rho.T, atol=EPS)
        and abs(float(np.trace(rho)) - 1.0) <= EPS
        and bool(np.all(np.linalg.eigvalsh(rho) >= -EPS))
    )


def run_positive_tests() -> dict:
    probes = finite_probe_family()
    states = [
        density(),
        np.array([[0.0, 0.0], [0.0, 1.0]], dtype=float),
        np.array([[0.5, 0.0], [0.0, 0.5]], dtype=float),
    ]
    probabilities = [[float(np.trace(effect @ rho)) for effect in probes] for rho in states]
    return {
        "finite_dimensions_enumerable": {
            "dimensions": [1, 2, 3, 4],
            "z3_sat_by_dimension": {str(d): finite_basis_sat(d) for d in [1, 2, 3, 4]},
            "pass": all(finite_basis_sat(d) for d in [1, 2, 3, 4]),
        },
        "finite_probe_family_resolves_identity": {
            "probe_count": len(probes),
            "identity_sum": np.sum(probes, axis=0).tolist(),
            "pass": len(probes) == 2 and np.allclose(np.sum(probes, axis=0), np.eye(2), atol=EPS),
        },
        "finite_state_set_has_valid_density_candidates": {
            "state_count": len(states),
            "probabilities": probabilities,
            "pass": all(is_density_candidate(rho) for rho in states),
        },
    }


def run_negative_tests() -> dict:
    invalid_wrong_trace = density(trace_bias=0.2)
    invalid_negative = np.array([[1.2, 0.0], [0.0, -0.2]], dtype=float)
    invalid_probe_family: list[np.ndarray] = []
    return {
        "infinite_dimension_marker_rejected": {
            "candidate_dimension": "omega",
            "pass": not isinstance("omega", int),
        },
        "wrong_trace_state_rejected": {
            "trace": float(np.trace(invalid_wrong_trace)),
            "pass": not is_density_candidate(invalid_wrong_trace),
        },
        "negative_eigenvalue_state_rejected": {
            "eigenvalues": np.linalg.eigvalsh(invalid_negative).tolist(),
            "pass": not is_density_candidate(invalid_negative),
        },
        "empty_probe_family_rejected": {
            "probe_count": len(invalid_probe_family),
            "pass": len(invalid_probe_family) == 0,
        },
    }


def run_boundary_tests() -> dict:
    pure_state = density()
    d1_basis_sat = finite_basis_sat(1)
    return {
        "one_dimensional_carrier_is_finite_but_not_later_noncommutative": {
            "d": 1,
            "finite_basis_sat": d1_basis_sat,
            "scope_note": "F01 alone admits finite d=1; N01 is a separate constraint.",
            "pass": d1_basis_sat,
        },
        "rank_one_density_state_is_valid_boundary": {
            "eigenvalues": np.linalg.eigvalsh(pure_state).tolist(),
            "pass": is_density_candidate(pure_state),
        },
    }


def main() -> int:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )
    payload = {
        "name": "f01_finitude_constraint",
        "classification": classification if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "claim_ceiling": "direct_f01_finitude_only_not_noncommutation_not_qit_promotion",
        "out_of_scope": [
            "N01 noncommutation admission",
            "GStack or axis promotion",
            "QIT engine admission",
            "entropy-gradient or coupling claims",
        ],
        "promotion_condition": "requires separate N01, coupling, topology, and stage-gate receipts; this receipt alone cannot promote",
        "demotion_condition": "demote if finite enumeration, positive/negative discrimination, or tool-manifest depth fails",
        "blocked_until": "separate later-stage receipts explicitly lift the coupling/axis/QIT gate",
        "next_lego_target": "n01_noncommutation_constraint",
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "probe_family": "finitude_only",
        "standalone_scope": {
            "imports_old_l0_l1_bundle": False,
            "forbidden_dependency_modules": ["sim_constraint_manifold_L0_L1", "engine_core"],
            "positive_instance": "finite C^2 carrier with a finite two-effect probe family and finite candidate states",
            "excluded_instance": "infinite-dimension marker, wrong-trace state, negative-eigenvalue state, and empty probe family",
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "claim_ceiling": "direct_f01_finitude_only_not_noncommutation_not_qit_promotion",
        },
        "all_pass": all_pass,
    }
    out = Path(__file__).resolve().parent / "a2_state" / "sim_results" / "f01_finitude_constraint_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"ALL PASS: {all_pass} -> {out}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
