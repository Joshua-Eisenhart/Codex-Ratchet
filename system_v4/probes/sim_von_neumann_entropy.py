#!/usr/bin/env python3
"""
PURE LEGO: von Neumann Entropy
==============================
Direct local spectral-entropy lego on bounded qubit states.
"""

import json
import pathlib
from datetime import datetime, timezone

import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = [
    "Classical comparator/control surface only; does not promote a nonclassical, formal-scout, bridge, axis-level, or canonical proof claim."
]


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for von Neumann entropy on bounded qubit states, kept separate "
    "from Shannon entropy, Renyi/Tsallis families, and broad entropy bundles."
)

LEGO_IDS = [
    "von_neumann_entropy",
]

PRIMARY_LEGO_IDS = [
    "von_neumann_entropy",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
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
TOOL_MANIFEST["numpy"] = {
    "tried": True,
    "used": True,
    "reason": "load-bearing finite array/matrix computation for this bounded classical lego receipt",
}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def vn_entropy(rho):
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    evals = np.maximum(evals, 0.0)
    evals = evals[evals > 1e-14]
    if evals.size == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def main():
    ket0 = ket([1, 0])
    ketp = ket([1 / np.sqrt(2), 1 / np.sqrt(2)])

    rho_pure_0 = dm(ket0)
    rho_pure_p = dm(ketp)
    rho_mm = np.eye(2, dtype=complex) / 2.0
    rho_mid = np.diag([0.8, 0.2]).astype(complex)
    # same spectrum as rho_mid, rotated basis
    U = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2.0)
    rho_mid_rot = U @ rho_mid @ U.conj().T

    s_pure_0 = vn_entropy(rho_pure_0)
    s_pure_p = vn_entropy(rho_pure_p)
    s_mm = vn_entropy(rho_mm)
    s_mid = vn_entropy(rho_mid)
    s_mid_rot = vn_entropy(rho_mid_rot)

    positive = {
        "pure_states_have_zero_von_neumann_entropy": {
            "rho_0": s_pure_0,
            "rho_plus": s_pure_p,
            "pass": abs(s_pure_0) < EPS and abs(s_pure_p) < EPS,
        },
        "maximally_mixed_qubit_has_one_bit_entropy": {
            "value": s_mm,
            "pass": abs(s_mm - 1.0) < EPS,
        },
        "same_spectrum_different_basis_has_same_entropy": {
            "diag": s_mid,
            "rotated": s_mid_rot,
            "pass": abs(s_mid - s_mid_rot) < EPS,
        },
    }

    negative = {
        "intermediate_mixed_state_is_not_pure_or_maximally_mixed": {
            "value": s_mid,
            "pass": s_mid > EPS and s_mid < 1.0 - EPS,
        },
        "pure_and_mixed_states_do_not_share_same_entropy": {
            "pass": abs(s_mid - s_pure_0) > EPS and abs(s_mm - s_mid) > EPS,
        },
    }

    boundary = {
        "entropy_orders_pure_less_than_mixed_less_than_maximally_mixed": {
            "pass": s_pure_0 < s_mid < s_mm,
        },
        "entropy_depends_only_on_spectrum_not_basis": {
            "pass": abs(s_mid - s_mid_rot) < EPS and not np.allclose(rho_mid, rho_mid_rot, atol=EPS),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "von_neumann_entropy",
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
        "criteria_checked": ["finite computation completed", "load-bearing tool path exercised", "local pass/fail criteria satisfied"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local von Neumann entropy lego on bounded qubit pure, intermediate mixed, and maximally mixed states.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "von_neumann_entropy_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
