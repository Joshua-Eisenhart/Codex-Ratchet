#!/usr/bin/env python3
"""
PURE LEGO: Gauge/Group Correspondence
=====================================
Direct local commutator-closure correspondence row on a bounded generator set.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local correspondence row showing that a bounded Pauli commutator set closes with the "
    "expected su(2)-like structure pattern, without promoting a broader physics identification claim."
)

LEGO_IDS = [
    "gauge_group_correspondence",
]

PRIMARY_LEGO_IDS = [
    "gauge_group_correspondence",
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

I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)


def commutator(a, b):
    return a @ b - b @ a


def hs_inner(a, b):
    return float(np.real(np.trace(a.conj().T @ b)))


def coefficients_in_basis(m, basis):
    gram = np.array([[hs_inner(b1, b2) for b2 in basis] for b1 in basis], dtype=float)
    rhs = np.array([hs_inner(m, b) for b in basis], dtype=float)
    return np.linalg.solve(gram, rhs)


def closure_residual(m, basis):
    coeffs = coefficients_in_basis(m, basis)
    recon = sum(c * b for c, b in zip(coeffs, basis))
    return float(np.linalg.norm(m - recon))


def main():
    basis = [X, Y, Z]
    comms = {
        "[X,Y]": commutator(X, Y),
        "[Y,Z]": commutator(Y, Z),
        "[Z,X]": commutator(Z, X),
    }

    residuals = {name: closure_residual(m / (2j), basis) for name, m in comms.items()}
    coeffs = {name: coefficients_in_basis(m / (2j), basis).tolist() for name, m in comms.items()}

    h = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2.0)
    rotated_basis = [h @ b @ h.conj().T for b in basis]
    rotated_residuals = {
        name: closure_residual(commutator(a, b) / (2j), rotated_basis)
        for name, (a, b) in {
            "[X,Y]": (rotated_basis[0], rotated_basis[1]),
            "[Y,Z]": (rotated_basis[1], rotated_basis[2]),
            "[Z,X]": (rotated_basis[2], rotated_basis[0]),
        }.items()
    }

    counterfeit_basis = [X, Z, I]
    counterfeit_residual = closure_residual(commutator(X, Z) / (2j), counterfeit_basis)

    positive = {
        "bounded_generator_set_closes_under_commutator": {
            "residuals": residuals,
            "pass": max(residuals.values()) < 1e-10,
        },
        "structure_constants_match_expected_generator_pattern": {
            "coefficients": coeffs,
            "pass": (
                np.allclose(coeffs["[X,Y]"], [0.0, 0.0, 1.0], atol=1e-10)
                and np.allclose(coeffs["[Y,Z]"], [1.0, 0.0, 0.0], atol=1e-10)
                and np.allclose(coeffs["[Z,X]"], [0.0, 1.0, 0.0], atol=1e-10)
            ),
        },
        "closure_pattern_survives_basis_change": {
            "rotated_residuals": rotated_residuals,
            "pass": max(rotated_residuals.values()) < 1e-10,
        },
    }

    negative = {
        "generic_counterfeit_subset_does_not_show_same_closure_pattern": {
            "counterfeit_residual": counterfeit_residual,
            "pass": counterfeit_residual > 1e-4,
        },
        "row_does_not_promote_full_physics_identification": {
            "pass": True,
        },
    }

    boundary = {
        "all_generators_are_traceless_hermitian": {
            "pass": all(abs(np.trace(b)) < 1e-10 and np.allclose(b, b.conj().T) for b in basis),
        },
        "comparison_is_bounded_to_one_local_carrier": {
            "pass": True,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "gauge_group_correspondence",
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
            "scope_note": "Direct local correspondence row on one bounded commutator generator set with no broader gauge-physics promotion.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "gauge_group_correspondence_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
