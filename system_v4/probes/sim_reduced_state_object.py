#!/usr/bin/env python3
"""
PURE LEGO: Reduced State Object
===============================
Direct local bipartite lego.

Construct small joint states and verify their reduced density states explicitly.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill

divergence_log = [
    "Classical comparator/control surface only; does not promote a nonclassical, formal-scout, bridge, axis-level, or canonical proof claim."
]


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for reduced density states obtained by partial tracing small "
    "bounded bipartite joint states."
)

LEGO_IDS = [
    "reduced_state_object",
    "partial_trace_operator",
    "joint_density_matrix",
]

PRIMARY_LEGO_IDS = [
    "reduced_state_object",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- pure numpy reduction lego"},
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

TOOL_MANIFEST["numpy"] = {
    "tried": True,
    "used": True,
    "reason": "load-bearing finite array/matrix computation for this bounded classical lego receipt",
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    k = ket(v)
    return k @ k.conj().T


def partial_trace_B(rho_ab, da=2, db=2):
    rho = rho_ab.reshape(da, db, da, db)
    return np.trace(rho, axis1=1, axis2=3)


def partial_trace_A(rho_ab, da=2, db=2):
    rho = rho_ab.reshape(da, db, da, db)
    return np.trace(rho, axis1=0, axis2=2)


def is_valid_dm(rho):
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    return bool(abs(np.trace(rho) - 1.0) < EPS and np.all(evals >= -EPS))


def main():
    k0 = [1, 0]
    k1 = [0, 1]
    prod = np.kron(ket(k0), ket(k1)).flatten()
    bell = (np.kron(ket(k0), ket(k0)) + np.kron(ket(k1), ket(k1))).flatten() / np.sqrt(2)

    rho_prod = np.outer(prod, prod.conj())
    rho_bell = np.outer(bell, bell.conj())

    prod_A = partial_trace_B(rho_prod)
    prod_B = partial_trace_A(rho_prod)
    bell_A = partial_trace_B(rho_bell)
    bell_B = partial_trace_A(rho_bell)

    positive = {
        "product_state_reductions": {
            "rho_A": prod_A.tolist(),
            "rho_B": prod_B.tolist(),
            "rho_A_valid": is_valid_dm(prod_A),
            "rho_B_valid": is_valid_dm(prod_B),
            "pass": is_valid_dm(prod_A) and is_valid_dm(prod_B) and np.allclose(prod_A, dm(k0)) and np.allclose(prod_B, dm(k1)),
        },
        "bell_state_reductions": {
            "rho_A": bell_A.tolist(),
            "rho_B": bell_B.tolist(),
            "rho_A_valid": is_valid_dm(bell_A),
            "rho_B_valid": is_valid_dm(bell_B),
            "pass": is_valid_dm(bell_A) and is_valid_dm(bell_B) and np.allclose(bell_A, np.eye(2) / 2) and np.allclose(bell_B, np.eye(2) / 2),
        },
    }

    negative = {
        "wrong_expected_product_marginal": {
            "pass": not np.allclose(prod_A, np.eye(2) / 2),
        },
        "bell_not_pure_after_reduction": {
            "pass": not np.allclose(bell_A @ bell_A, bell_A),
        },
    }

    boundary = {
        "trace_preserved_under_reduction": {
            "pass": abs(np.trace(prod_A) - 1.0) < EPS and abs(np.trace(bell_A) - 1.0) < EPS,
        }
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "reduced_state_object",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "finite classical baseline/tool-depth receipt only; no bridge, GStack, axis, QIT, or nonclassical admission",
        "next_lego_target": "Use as a bounded source receipt for later tool-lego or coupling work only after exact downstream checks.",
        "promotion_condition": "Requires separate bridge/nonclassical/topology/operator coupling receipts and explicit stage-gate approval.",
        "blocked_until": "tool-lego fit; coupling/coexistence evidence; stage-gate admission",
        "demotion_condition": "Demote if rerun fails, tool use is not load-bearing, or result claims exceed this finite receipt.",
        "out_of_scope": ["QIT engine admission", "GStack admission", "axis promotion", "nonclassical proof"],
        "all_pass": all_pass,
        "criteria_checked": ["finite computation completed", "load-bearing numpy path exercised", "local pass/fail criteria satisfied"],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local reduced-state lego on small bipartite joint states.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "reduced_state_object_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
