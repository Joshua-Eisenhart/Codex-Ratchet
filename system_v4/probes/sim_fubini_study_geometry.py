#!/usr/bin/env python3
"""
PURE LEGO: Fubini-Study Geometry
================================
Direct local pure-state projective metric lego on bounded qubit rays.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10
FS_TOL = 1e-7

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for Fubini-Study geometry on bounded pure-state rays, "
    "kept separate from Bures and trace-distance rows."
)

LEGO_IDS = [
    "fubini_study_geometry",
]

PRIMARY_LEGO_IDS = [
    "fubini_study_geometry",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for the smallest direct pure-state metric row"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def normalize(v):
    v = np.array(v, dtype=complex).reshape(-1)
    return v / np.linalg.norm(v)


def fubini_study_distance(psi, phi):
    overlap = abs(np.vdot(psi, phi))
    overlap = min(1.0, max(0.0, float(overlap)))
    return float(np.arccos(overlap))


def main():
    psi0 = normalize([1, 0])
    psi1 = normalize([0, 1])
    psi_plus = normalize([1, 1])
    psi_minus = normalize([1, -1])
    theta = 0.7
    psi_mid = normalize([np.cos(theta / 2), np.sin(theta / 2)])
    psi_phase = np.exp(1j * 0.731) * psi_mid

    d_same = fubini_study_distance(psi0, psi0)
    d_phase = fubini_study_distance(psi_mid, psi_phase)
    d_orth = fubini_study_distance(psi0, psi1)
    d_plus = fubini_study_distance(psi0, psi_plus)
    d_mid = fubini_study_distance(psi0, psi_mid)

    positive = {
        "same_ray_has_zero_distance": {
            "value": d_same,
            "pass": abs(d_same) < EPS,
        },
        "global_phase_invariance_holds": {
            "value": d_phase,
            "pass": abs(d_phase) < FS_TOL,
        },
        "symmetry_holds": {
            "lhs": d_plus,
            "rhs": fubini_study_distance(psi_plus, psi0),
            "pass": abs(d_plus - fubini_study_distance(psi_plus, psi0)) < EPS,
        },
    }

    negative = {
        "orthogonal_states_are_not_zero_distance": {
            "value": d_orth,
            "pass": abs(d_orth - (np.pi / 2.0)) < EPS,
        },
        "superposition_case_is_intermediate": {
            "plus": d_plus,
            "orth": d_orth,
            "pass": d_plus > EPS and d_plus < d_orth - EPS,
        },
    }

    boundary = {
        "ray_not_vector_rule_depends_only_on_overlap_magnitude": {
            "mid": d_mid,
            "phase_mid": fubini_study_distance(psi0, psi_phase),
            "pass": abs(d_mid - fubini_study_distance(psi0, psi_phase)) < EPS,
        },
        "triangle_inequality_spot_check": {
            "lhs": fubini_study_distance(psi0, psi_mid),
            "rhs": fubini_study_distance(psi0, psi_plus) + fubini_study_distance(psi_plus, psi_mid),
            "pass": fubini_study_distance(psi0, psi_mid) <= fubini_study_distance(psi0, psi_plus) + fubini_study_distance(psi_plus, psi_mid) + EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "fubini_study_geometry",
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
            "scope_note": "Direct local Fubini-Study metric lego on bounded pure-state rays.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "fubini_study_geometry_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
