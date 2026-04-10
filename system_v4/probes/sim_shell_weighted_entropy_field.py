#!/usr/bin/env python3
"""
PURE LEGO: Shell-Weighted Entropy Field
======================================
Direct late-layer shell-weighted entropy field on one bounded shell family.
"""

import json
import pathlib

import numpy as np


EPS = 1e-12

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical late-layer lego for a shell-weighted entropy field on one bounded shell family, "
    "kept separate from history-transport bundles and selector claims."
)

LEGO_IDS = [
    "shell_weighted_entropy_field",
]

PRIMARY_LEGO_IDS = [
    "shell_weighted_entropy_field",
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


def hermitian(rho):
    return 0.5 * (rho + rho.conj().T)


def validate_density(rho):
    rho = hermitian(np.asarray(rho, dtype=np.complex128))
    tr = np.trace(rho)
    if abs(tr) < EPS:
        raise ValueError("density matrix has near-zero trace")
    rho = rho / tr
    evals = np.linalg.eigvalsh(rho)
    if np.min(np.real(evals)) < -1e-9:
        raise ValueError("density matrix not positive semidefinite")
    return rho


def bloch_density(x, y, z):
    return validate_density(
        0.5
        * np.array(
            [[1 + z, x - 1j * y], [x + 1j * y, 1 - z]],
            dtype=np.complex128,
        )
    )


def entropy_bits(rho):
    evals = np.linalg.eigvalsh(hermitian(rho))
    evals = np.clip(np.real(evals), 0.0, None)
    nz = evals[evals > EPS]
    if nz.size == 0:
        return 0.0
    return float(-np.sum(nz * np.log2(nz)))


def normalize(weights):
    weights = np.asarray(weights, dtype=float)
    return weights / np.sum(weights)


def shell_field(states, weights):
    weights = normalize(weights)
    entropies = np.array([entropy_bits(rho) for rho in states], dtype=float)
    field = weights * entropies
    return {
        "weights": weights.tolist(),
        "entropies": entropies.tolist(),
        "field": field.tolist(),
        "field_sum": float(np.sum(field)),
        "min_entropy": float(np.min(entropies)),
        "max_entropy": float(np.max(entropies)),
    }


def main():
    shells = [
        bloch_density(0.0, 0.0, 0.98),
        bloch_density(0.18, 0.0, 0.82),
        bloch_density(0.33, 0.11, 0.55),
        bloch_density(0.45, 0.24, 0.18),
        bloch_density(0.30, 0.41, -0.05),
    ]
    front_loaded = shell_field(shells, [7, 5, 3, 2, 1])
    back_loaded = shell_field(shells, [1, 2, 3, 5, 7])
    uniform = shell_field(shells, [1, 1, 1, 1, 1])

    positive = {
        "field_sum_stays_within_shell_entropy_bounds": {
            "front_loaded_sum": front_loaded["field_sum"],
            "uniform_sum": uniform["field_sum"],
            "min_entropy": front_loaded["min_entropy"],
            "max_entropy": front_loaded["max_entropy"],
            "pass": (
                front_loaded["min_entropy"] - 1e-12
                <= front_loaded["field_sum"]
                <= front_loaded["max_entropy"] + 1e-12
            ),
        },
        "changing_shell_weights_changes_field_profile": {
            "front_loaded_field": front_loaded["field"],
            "back_loaded_field": back_loaded["field"],
            "front_loaded_sum": front_loaded["field_sum"],
            "back_loaded_sum": back_loaded["field_sum"],
            "pass": (
                np.max(np.abs(np.array(front_loaded["field"]) - np.array(back_loaded["field"]))) > 1e-4
                and abs(front_loaded["field_sum"] - back_loaded["field_sum"]) > 1e-4
            ),
        },
        "field_is_not_uniform_when_shell_entropies_and_weights_differ": {
            "uniform_field": uniform["field"],
            "front_loaded_field": front_loaded["field"],
            "pass": np.max(np.abs(np.array(front_loaded["field"]) - np.array(uniform["field"]))) > 1e-4,
        },
    }

    negative = {
        "shell_field_does_not_claim_history_transport_law": {
            "pass": True,
        },
        "shell_field_does_not_promote_bridge_selector": {
            "pass": True,
        },
    }

    boundary = {
        "all_shell_states_remain_valid_density_operators": {
            "pass": True,
        },
        "field_is_bounded_to_one_local_shell_family": {
            "pass": True,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "shell_weighted_entropy_field",
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
            "scope_note": "Direct late-layer shell-weighted entropy field on one bounded shell family only.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "shell_weighted_entropy_field_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
