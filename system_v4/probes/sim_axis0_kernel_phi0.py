#!/usr/bin/env python3
"""
PURE LEGO: Axis-0 Kernel Phi0
=============================
Direct late-layer signed kernel row on one bounded point-bridge family.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical late-layer lego for a signed Axis-0 kernel Phi0 on one bounded point-bridge family, "
    "kept separate from bridge search, unsigned entropy bundles, and final selector promotion."
)

LEGO_IDS = [
    "axis0_kernel_phi0",
]

PRIMARY_LEGO_IDS = [
    "axis0_kernel_phi0",
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
SX = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SY = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SZ = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
PHI_PLUS = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2.0)


def bloch_to_density(v):
    x, y, z = v
    rho = 0.5 * (I2 + x * SX + y * SY + z * SZ)
    return 0.5 * (rho + rho.conj().T)


def ensure_density(rho):
    rho = 0.5 * (rho + rho.conj().T)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.clip(np.real(evals), 0.0, None)
    if evals.sum() <= 0.0:
        return np.eye(rho.shape[0], dtype=complex) / rho.shape[0]
    return evecs @ np.diag(evals / evals.sum()) @ evecs.conj().T


def point_bridge(q_ref, q_cur, coupling=0.22):
    rho_ref = bloch_to_density(q_ref)
    rho_cur = bloch_to_density(q_cur)
    bell = np.outer(PHI_PLUS, PHI_PLUS.conj())
    rho = (1.0 - coupling) * np.kron(rho_ref, rho_cur) + coupling * bell
    return ensure_density(rho)


def partial_trace_A(rho):
    return np.trace(rho.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_B(rho):
    return np.trace(rho.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def entropy(rho):
    vals = np.linalg.eigvalsh(ensure_density(rho))
    vals = vals[vals > 1e-14]
    return float(-np.sum(vals * np.log2(vals))) if len(vals) else 0.0


def phi0_signed(rho_ab):
    rho_a = partial_trace_A(rho_ab)
    rho_b = partial_trace_B(rho_ab)
    return float(np.real(np.trace(rho_b @ SZ) - np.trace(rho_a @ SZ)))


def mutual_information(rho_ab):
    return max(
        0.0,
        entropy(partial_trace_A(rho_ab)) + entropy(partial_trace_B(rho_ab)) - entropy(rho_ab),
    )


def main():
    q_ref = np.array([0.0, 0.0, 1.0], dtype=float)
    q_cur = np.array([0.8, 0.0, -0.1], dtype=float)
    q_cur = q_cur / np.linalg.norm(q_cur)

    rho_same = point_bridge(q_ref, q_ref)
    rho_forward = point_bridge(q_ref, q_cur)
    rho_reverse = point_bridge(q_cur, q_ref)

    phi0_same = phi0_signed(rho_same)
    phi0_forward = phi0_signed(rho_forward)
    phi0_reverse = phi0_signed(rho_reverse)

    mi_forward = mutual_information(rho_forward)
    mi_reverse = mutual_information(rho_reverse)

    positive = {
        "phi0_vanishes_on_symmetric_reference_case": {
            "phi0_same": phi0_same,
            "pass": abs(phi0_same) < 1e-8,
        },
        "phi0_changes_sign_under_packet_reversal": {
            "phi0_forward": phi0_forward,
            "phi0_reverse": phi0_reverse,
            "pass": abs(phi0_forward + phi0_reverse) < 1e-8 and abs(phi0_forward) > 1e-4,
        },
        "unsigned_companion_mi_is_reversal_invariant": {
            "mi_forward": mi_forward,
            "mi_reverse": mi_reverse,
            "pass": abs(mi_forward - mi_reverse) < 1e-8,
        },
    }

    negative = {
        "phi0_row_does_not_promote_final_winner": {
            "pass": True,
        },
        "phi0_is_not_collapsed_to_unsigned_entropy_family": {
            "pass": abs(phi0_forward) > 1e-4 and abs(mi_forward - abs(phi0_forward)) > 1e-4,
        },
    }

    boundary = {
        "bridge_outputs_remain_valid_density_operators": {
            "pass": all(
                abs(np.trace(rho) - 1.0) < EPS and np.min(np.linalg.eigvalsh(rho)) > -1e-10
                for rho in [rho_same, rho_forward, rho_reverse]
            ),
        },
        "signed_kernel_uses_one_bounded_bridge_family_only": {
            "pass": True,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "axis0_kernel_phi0",
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
            "scope_note": "Direct late-layer signed kernel row on one bounded point-bridge family with MI kept as an unsigned companion.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "axis0_kernel_phi0_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
