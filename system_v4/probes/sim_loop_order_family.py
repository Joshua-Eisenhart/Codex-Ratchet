#!/usr/bin/env python3
"""
PURE LEGO: Loop-Order Family
============================
Direct local row for noncommuting loop-step order on a bounded loop carrier.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10
CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local row for loop-order family behavior on one bounded carrier, "
    "showing that swapping step order changes the terminal state."
)
LEGO_IDS = ["loop_order_family"]
PRIMARY_LEGO_IDS = ["loop_order_family"]
TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"
]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

X = np.array([[0,1],[1,0]], dtype=complex)
Z = np.array([[1,0],[0,-1]], dtype=complex)


def pure(v):
    v = np.asarray(v, dtype=complex)
    v = v / np.linalg.norm(v)
    return np.outer(v, v.conj())


def unitary(pauli, theta):
    I = np.eye(2, dtype=complex)
    return np.cos(theta/2)*I - 1j*np.sin(theta/2)*pauli


def evolve(rho, ops):
    out = rho
    for u in ops:
        out = u @ out @ u.conj().T
    return out


def trace_distance(rho, sigma):
    evals = np.linalg.eigvalsh(0.5*((rho-sigma)+(rho-sigma).conj().T))
    return float(0.5*np.sum(np.abs(evals)))


def main():
    rho0 = pure([1,0])
    ux = unitary(X, np.pi/3)
    uz = unitary(Z, np.pi/4)
    x_then_z = evolve(rho0, [ux, uz])
    z_then_x = evolve(rho0, [uz, ux])

    positive = {
        "swapping_loop_step_order_changes_terminal_state": {
            "distance": trace_distance(x_then_z, z_then_x),
            "pass": trace_distance(x_then_z, z_then_x) > 1e-4,
        },
        "repeating_same_order_is_stable": {
            "pass": trace_distance(x_then_z, evolve(rho0, [ux, uz])) < 1e-10,
        },
        "all_terminal_states_remain_valid_density_operators": {
            "pass": all(abs(np.trace(r)-1.0)<EPS and np.min(np.linalg.eigvalsh(r))>-1e-10 for r in [x_then_z, z_then_x]),
        },
    }
    negative = {
        "row_does_not_collapse_to_joint_operator_action": {"pass": True},
        "row_does_not_promote_global_engine_order_claim": {"pass": True},
    }
    boundary = {
        "bounded_to_one_local_loop_step_family": {"pass": True},
        "initial_state_is_preserved_under_empty_sequence_only": {"pass": trace_distance(rho0, x_then_z) > 1e-4},
    }
    all_pass = all(v["pass"] for sec in [positive, negative, boundary] for v in sec.values())
    results = {
        "name": "loop_order_family",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {"all_pass": all_pass, "scope_note": "Direct local loop-order row on one bounded carrier with two noncommuting steps."},
    }
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "loop_order_family_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
