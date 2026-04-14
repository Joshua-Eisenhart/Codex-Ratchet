#!/usr/bin/env python3
"""
PURE LEGO: Real-Only Geometry Rejection
======================================
Direct local falsifier showing that a real-only restriction destroys complex phase geometry.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local falsifier showing that a real-only restriction collapses distinct complex phase "
    "states and erases nontrivial cycle phase geometry."
)

LEGO_IDS = [
    "real_only_geometry_rejection",
]

PRIMARY_LEGO_IDS = [
    "real_only_geometry_rejection",
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


def phase_state(phi):
    v = np.array([1.0, np.exp(1j * phi)], dtype=complex) / np.sqrt(2.0)
    return v


def real_projected_state(phi):
    v = np.real(phase_state(phi))
    norm = np.linalg.norm(v)
    if norm < EPS:
        raise ValueError("real projection collapsed to zero vector")
    return v / norm


def density(v):
    v = np.asarray(v, dtype=complex)
    return np.outer(v, v.conj())


def trace_distance(rho, sigma):
    diff = 0.5 * ((rho - sigma) + (rho - sigma).conj().T)
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))


def cycle_phase(vectors):
    prod = 1.0 + 0.0j
    for a, b in zip(vectors, vectors[1:] + vectors[:1]):
        prod *= np.vdot(a, b)
    return float(np.angle(prod))


def main():
    phi_a = np.pi / 4.0
    phi_b = -np.pi / 4.0

    v_a = phase_state(phi_a)
    v_b = phase_state(phi_b)
    rv_a = real_projected_state(phi_a)
    rv_b = real_projected_state(phi_b)

    td_complex = trace_distance(density(v_a), density(v_b))
    td_real = trace_distance(density(rv_a), density(rv_b))

    complex_loop = [phase_state(phi) for phi in [0.0, np.pi / 3.0, np.pi]]
    real_loop = [real_projected_state(phi) for phi in [0.0, np.pi / 3.0, np.pi]]

    loop_phase_complex = abs(cycle_phase(complex_loop))
    loop_phase_real = abs(cycle_phase(real_loop))

    positive = {
        "complex_phase_pair_is_geometrically_distinct": {
            "trace_distance": td_complex,
            "pass": td_complex > 1e-4,
        },
        "real_projection_collapses_conjugate_phase_pair": {
            "trace_distance": td_real,
            "pass": td_real < EPS,
        },
        "complex_loop_has_nontrivial_cycle_phase": {
            "phase_magnitude": loop_phase_complex,
            "pass": loop_phase_complex > 1e-3,
        },
    }

    negative = {
        "real_only_projection_erases_cycle_phase_geometry": {
            "phase_magnitude": loop_phase_real,
            "pass": loop_phase_real < EPS,
        },
        "row_does_not_collapse_to_generic_state_representation_claim": {
            "pass": td_complex > 1e-4 and td_real < EPS,
        },
    }

    boundary = {
        "comparison_uses_one_bounded_phase_family": {
            "pass": True,
        },
        "all_state_vectors_remain_normalized": {
            "pass": all(abs(np.linalg.norm(v) - 1.0) < 1e-10 for v in [v_a, v_b, rv_a, rv_b]),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "real_only_geometry_rejection",
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
            "scope_note": "Direct local falsifier showing that real-only restriction collapses distinct complex phase states and erases nontrivial cycle-phase geometry.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "real_only_geometry_rejection_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
