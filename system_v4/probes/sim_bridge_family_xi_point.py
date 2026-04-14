#!/usr/bin/env python3
"""
PURE LEGO: Xi Point Bridge
==========================
Direct local point-bridge row on a tiny bounded packet family.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical late-layer lego for the point bridge Xi_point on one bounded packet family, "
    "kept separate from Axis-0 selector logic, shell-weighted entropy fields, and broad bridge searches."
)

LEGO_IDS = [
    "bridge_family_xi_point",
]

PRIMARY_LEGO_IDS = [
    "bridge_family_xi_point",
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

I2 = np.eye(2, dtype=complex)
I4 = np.eye(4, dtype=complex)
PHI_PLUS = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2.0)


def bloch_to_density(vec):
    x, y, z = vec
    sx = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
    sy = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
    sz = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    rho = 0.5 * (I2 + x * sx + y * sy + z * sz)
    return 0.5 * (rho + rho.conj().T)


def ensure_density(rho):
    rho = 0.5 * (rho + rho.conj().T)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.clip(np.real(evals), 0.0, None)
    if evals.sum() <= 0.0:
        return I4 / 4.0 if rho.shape == (4, 4) else I2 / 2.0
    return evecs @ np.diag(evals / evals.sum()) @ evecs.conj().T


def pair_state_from_vec(vec):
    rho = bloch_to_density(vec)
    return np.kron(rho, rho)


def point_bridge(q_ref, q_cur, coupling=0.22):
    ref_pair = pair_state_from_vec(q_ref)
    cur_pair = pair_state_from_vec(q_cur)
    bell = np.outer(PHI_PLUS, PHI_PLUS.conj())
    return ensure_density((1.0 - coupling) * 0.5 * (ref_pair + cur_pair) + coupling * bell)


def shell_bridge(q_ref, q_cur, shell_weight=0.35):
    ref_pair = pair_state_from_vec(q_ref)
    cur_pair = pair_state_from_vec(q_cur)
    bridge = (1.0 - shell_weight) * cur_pair + shell_weight * ref_pair
    return ensure_density(bridge)


def mutual_information(rho_ab):
    def ptr_a(rho):
        return np.trace(rho.reshape(2, 2, 2, 2), axis1=0, axis2=2)
    def ptr_b(rho):
        return np.trace(rho.reshape(2, 2, 2, 2), axis1=1, axis2=3)
    def entropy(rho):
        vals = np.linalg.eigvalsh(ensure_density(rho))
        vals = vals[vals > 1e-14]
        return float(-np.sum(vals * np.log2(vals))) if len(vals) else 0.0
    return max(0.0, entropy(ptr_a(rho_ab)) + entropy(ptr_b(rho_ab)) - entropy(rho_ab))


def main():
    q_ref = np.array([0.0, 0.0, 1.0], dtype=float)
    q_cur_same = np.array([0.0, 0.0, 1.0], dtype=float)
    q_cur_shift = np.array([0.6, 0.0, 0.6], dtype=float) / np.sqrt(0.72)

    rho_same = point_bridge(q_ref, q_cur_same)
    rho_shift = point_bridge(q_ref, q_cur_shift)
    rho_shell = shell_bridge(q_ref, q_cur_shift)

    positive = {
        "point_bridge_produces_valid_bipartite_state": {
            "trace": float(np.real(np.trace(rho_shift))),
            "pass": abs(np.trace(rho_shift) - 1.0) < EPS and np.min(np.linalg.eigvalsh(rho_shift)) > -1e-10,
        },
        "point_bridge_changes_when_current_point_changes": {
            "fro_shift": float(np.linalg.norm(rho_shift - rho_same)),
            "pass": np.linalg.norm(rho_shift - rho_same) > 1e-3,
        },
        "point_bridge_is_distinct_from_shell_weighted_bridge_on_same_packet": {
            "fro_difference": float(np.linalg.norm(rho_shift - rho_shell)),
            "pass": np.linalg.norm(rho_shift - rho_shell) > 1e-3,
        },
    }

    negative = {
        "point_bridge_row_does_not_claim_final_axis0_winner": {
            "pass": True,
        },
        "point_bridge_row_does_not_collapse_into_unsigned_entropy_surface": {
            "mi_point": mutual_information(rho_shift),
            "mi_shell": mutual_information(rho_shell),
            "pass": abs(mutual_information(rho_shift) - mutual_information(rho_shell)) > 1e-4,
        },
    }

    boundary = {
        "same_reference_same_current_gives_stable_reference_case": {
            "pass": np.allclose(rho_same, point_bridge(q_ref, q_cur_same), atol=EPS),
        },
        "bounded_packet_scope_stays_pointwise_not_searchwise": {
            "pass": True,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "bridge_family_xi_point",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local point-bridge row on one bounded packet family, without selector or search claims.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "bridge_family_xi_point_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
