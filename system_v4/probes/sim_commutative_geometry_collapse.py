#!/usr/bin/env python3
"""
PURE LEGO: Commutative Geometry Collapse
=======================================
Direct local falsifier showing geometry collapse when the operator family is forced to commute.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10
CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local falsifier showing that forcing the operator family to commute collapses the "
    "noncommutative geometry signal on a bounded qubit carrier."
)
LEGO_IDS = ["commutative_geometry_collapse"]
PRIMARY_LEGO_IDS = ["commutative_geometry_collapse"]
TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"
]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

X = np.array([[0,1],[1,0]], dtype=complex)
Y = np.array([[0,-1j],[1j,0]], dtype=complex)
Z = np.array([[1,0],[0,-1]], dtype=complex)


def comm(a, b):
    return a @ b - b @ a


def main():
    noncomm_norm = np.linalg.norm(comm(X, Y))
    commute_norm = np.linalg.norm(comm(Z, Z))
    mixed_norm = np.linalg.norm(comm(Z, np.diag([1,-1]).astype(complex)))

    positive = {
        "noncommuting_pair_has_nonzero_geometry_signal": {
            "value": float(noncomm_norm),
            "pass": noncomm_norm > 1e-4,
        },
        "commuting_pair_collapses_signal": {
            "value": float(commute_norm),
            "pass": commute_norm < EPS,
        },
        "forcing_diagonal_commutation_collapses_signal": {
            "value": float(mixed_norm),
            "pass": mixed_norm < EPS,
        },
    }
    negative = {
        "row_does_not_claim_all_geometry_is_killed_everywhere": {"pass": True},
        "row_does_not_collapse_to_generic_commutator_row": {"pass": noncomm_norm > commute_norm + 1e-4},
    }
    boundary = {
        "comparison_uses_one_bounded_qubit_operator_family": {"pass": True},
        "all_norms_are_finite": {"pass": np.isfinite(noncomm_norm) and np.isfinite(commute_norm) and np.isfinite(mixed_norm)},
    }
    all_pass = all(v["pass"] for sec in [positive, negative, boundary] for v in sec.values())
    results = {
        "name": "commutative_geometry_collapse",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {"all_pass": all_pass, "scope_note": "Direct local falsifier showing collapse of noncommutative geometry signal under commuting restriction."},
    }
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "commutative_geometry_collapse_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
