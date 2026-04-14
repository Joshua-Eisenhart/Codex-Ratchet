#!/usr/bin/env python3
"""
PURE LEGO: Channel-Space Geometry
=================================
Direct local geometry lego on a bounded qubit channel family.
"""

import json
import pathlib
from datetime import datetime, timezone

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for channel-space geometry on a bounded qubit channel family, "
    "kept separate from CPTP legality, measurement instruments, and channel-capacity rows."
)

LEGO_IDS = [
    "channel_space_geometry",
]

PRIMARY_LEGO_IDS = [
    "channel_space_geometry",
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
X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def apply_channel(rho, kraus_ops):
    out = np.zeros_like(rho, dtype=complex)
    for k in kraus_ops:
        out = out + k @ rho @ k.conj().T
    return out


def choi_matrix(kraus_ops):
    omega = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2.0)
    omega_proj = np.outer(omega, omega.conj())
    total = np.zeros((4, 4), dtype=complex)
    for k in kraus_ops:
        ki = np.kron(k, I2)
        total = total + ki @ omega_proj @ ki.conj().T
    return total


def frob_distance(a, b):
    return float(np.linalg.norm(a - b))


def identity_channel():
    return [I2.copy()]


def dephasing_channel(p=0.4):
    return [np.sqrt(1.0 - p) * I2, np.sqrt(p) * Z]


def bit_flip_channel(p=0.35):
    return [np.sqrt(1.0 - p) * I2, np.sqrt(p) * X]


def amplitude_damping_channel(gamma=0.4):
    return [
        np.array([[1.0, 0.0], [0.0, np.sqrt(1.0 - gamma)]], dtype=complex),
        np.array([[0.0, np.sqrt(gamma)], [0.0, 0.0]], dtype=complex),
    ]


def output_signature(kraus_ops, states):
    sig = []
    for rho in states:
        out = apply_channel(rho, kraus_ops)
        sig.append(out.reshape(-1))
    return np.concatenate(sig)


def main():
    rho_0 = dm([1, 0])
    rho_1 = dm([0, 1])
    rho_p = dm([1 / np.sqrt(2), 1 / np.sqrt(2)])
    rho_mix = np.eye(2, dtype=complex) / 2.0
    states = [rho_0, rho_1, rho_p, rho_mix]

    channels = {
        "identity": identity_channel(),
        "dephasing": dephasing_channel(),
        "bit_flip": bit_flip_channel(),
        "amplitude_damping": amplitude_damping_channel(),
    }

    choi = {name: choi_matrix(kraus) for name, kraus in channels.items()}
    signatures = {name: output_signature(kraus, states) for name, kraus in channels.items()}

    d_id_deph = frob_distance(choi["identity"], choi["dephasing"])
    d_id_flip = frob_distance(choi["identity"], choi["bit_flip"])
    d_deph_flip = frob_distance(choi["dephasing"], choi["bit_flip"])
    d_flip_amp = frob_distance(choi["bit_flip"], choi["amplitude_damping"])

    sig_id_deph = frob_distance(signatures["identity"], signatures["dephasing"])
    sig_id_flip = frob_distance(signatures["identity"], signatures["bit_flip"])
    sig_flip_amp = frob_distance(signatures["bit_flip"], signatures["amplitude_damping"])

    out_id_0 = apply_channel(rho_0, channels["identity"])
    out_amp_1 = apply_channel(rho_1, channels["amplitude_damping"])

    positive = {
        "distinct_channels_have_nonzero_choi_separation": {
            "id_vs_dephasing": d_id_deph,
            "id_vs_bit_flip": d_id_flip,
            "dephasing_vs_bit_flip": d_deph_flip,
            "pass": min(d_id_deph, d_id_flip, d_deph_flip) > EPS,
        },
        "output_family_signature_separates_channel_actions": {
            "id_vs_dephasing": sig_id_deph,
            "id_vs_bit_flip": sig_id_flip,
            "bit_flip_vs_amplitude_damping": sig_flip_amp,
            "pass": min(sig_id_deph, sig_id_flip, sig_flip_amp) > EPS,
        },
        "identity_preserves_zero_state_but_amplitude_damping_moves_excited_state": {
            "id_on_zero_error": frob_distance(out_id_0, rho_0),
            "amp_on_one_distance_to_one": frob_distance(out_amp_1, rho_1),
            "pass": frob_distance(out_id_0, rho_0) < EPS and frob_distance(out_amp_1, rho_1) > EPS,
        },
    }

    negative = {
        "dephasing_and_bit_flip_are_not_same_geometry_row": {
            "choi_distance": d_deph_flip,
            "signature_distance": frob_distance(signatures["dephasing"], signatures["bit_flip"]),
            "pass": d_deph_flip > EPS and frob_distance(signatures["dephasing"], signatures["bit_flip"]) > EPS,
        },
        "identity_and_amplitude_damping_do_not_share_same_output_signature": {
            "pass": frob_distance(signatures["identity"], signatures["amplitude_damping"]) > EPS,
        },
    }

    boundary = {
        "choi_and_output_geometries_agree_on_identity_as_distinct_from_nontrivial_channels": {
            "pass": d_id_deph > EPS and d_id_flip > EPS and sig_id_deph > EPS and sig_id_flip > EPS,
        },
        "channel_distances_are_symmetric_under_pair_order": {
            "pass": abs(frob_distance(choi["identity"], choi["dephasing"]) - frob_distance(choi["dephasing"], choi["identity"])) < EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "channel_space_geometry",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local channel-space geometry lego on identity, dephasing, bit-flip, and amplitude-damping channels over a fixed qubit state family.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "channel_space_geometry_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
