#!/usr/bin/env python3
"""
PURE LEGO: Positivity Constraint
================================
Direct local admission lego.

Check positive-semidefinite validity on a small bounded set of valid and invalid
candidate density operators.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill

divergence_log = [
    "Classical comparator/control surface only; this metadata clears C4 for baseline accounting and does not promote a nonclassical, formal-scout, bridge, axis-level, or canonical proof claim."
]


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for the positive-semidefinite admission constraint on "
    "bounded density-operator candidates."
)

LEGO_IDS = [
    "positivity_constraint",
    "density_matrix_representability",
]

PRIMARY_LEGO_IDS = [
    "positivity_constraint",
]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing eigenvalue and PSD checks on bounded 2x2 density candidates"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- pure numpy eigenvalue lego"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"


def positivity_check(rho):
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    return {
        "eigenvalues": [float(x) for x in evals],
        "psd": bool(np.all(evals >= -EPS)),
    }


def main():
    valid = {
        "max_mixed": np.eye(2, dtype=complex) / 2,
        "pure_zero": np.array([[1, 0], [0, 0]], dtype=complex),
        "bloch_x_plus": np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex),
    }
    invalid = {
        "negative_eigenvalue": np.array([[1.2, 0], [0, -0.2]], dtype=complex),
        "indefinite_offdiag": np.array([[0.5, 0.8], [0.8, 0.5]], dtype=complex),
    }

    positive = {}
    for name, rho in valid.items():
        chk = positivity_check(rho)
        positive[name] = {**chk, "pass": chk["psd"]}

    negative = {}
    for name, rho in invalid.items():
        chk = positivity_check(rho)
        negative[name] = {**chk, "pass": not chk["psd"]}

    boundary = {
        "rank_deficient_pure_state_is_still_psd": {
            "pass": positivity_check(valid["pure_zero"])["psd"],
        }
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "positivity_constraint",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "canonical_local_positivity_constraint_lego_only",
        "next_lego_target": "none",
        "promotion_condition": "requires separate reconciled queue row before coupling, bridge, axis, engine, or QIT use",
        "blocked_until": "exact parent receipts, queue row, result JSON, and ledger loopback are reconciled",
        "demotion_condition": "demote if valid PSD candidates are rejected, invalid candidates are admitted, or this row is used for a higher-stage claim",
        "out_of_scope": [
            "no coupling, bridge, axis, engine, GStack, or nonclassical admission claim",
        ],
        "all_pass": all_pass,
        "criteria_checked": list(positive) + list(negative) + list(boundary),
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "positive": f"{sum(1 for v in positive.values() if v['pass'])}/{len(positive)}",
            "negative": f"{sum(1 for v in negative.values() if v['pass'])}/{len(negative)}",
            "boundary": f"{sum(1 for v in boundary.values() if v['pass'])}/{len(boundary)}",
            "all_pass": all_pass,
            "scope_note": "Direct local PSD admission lego on bounded 2x2 candidates.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "positivity_constraint_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
