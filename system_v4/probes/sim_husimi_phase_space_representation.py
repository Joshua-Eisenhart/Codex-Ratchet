#!/usr/bin/env python3
"""
PURE LEGO: Husimi Phase-Space Representation
============================================
Direct local qubit Husimi-Q representation lego on a fixed Bloch-sphere grid.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10
INTEGRAL_TOL = 0.06

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for Husimi phase-space representation on bounded qubit states, "
    "kept separate from sphere geometry, characteristic representations, and broader "
    "phase-space geometry surfaces."
)

LEGO_IDS = [
    "husimi_phase_space_representation",
]

PRIMARY_LEGO_IDS = [
    "husimi_phase_space_representation",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this local lego"},
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


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def qubit_coherent_state(theta, phi):
    return np.array(
        [
            [np.cos(theta / 2.0)],
            [np.exp(1j * phi) * np.sin(theta / 2.0)],
        ],
        dtype=complex,
    )


def husimi_q(rho, theta, phi):
    alpha = qubit_coherent_state(theta, phi)
    return float(np.real_if_close((alpha.conj().T @ rho @ alpha)[0, 0]) / (2.0 * np.pi))


def approx_sphere_integral(rho, n_theta=40, n_phi=40):
    d_theta = np.pi / n_theta
    d_phi = 2.0 * np.pi / n_phi
    total = 0.0
    for i in range(n_theta):
        theta = (i + 0.5) * d_theta
        sin_theta = np.sin(theta)
        for j in range(n_phi):
            phi = (j + 0.5) * d_phi
            total += husimi_q(rho, theta, phi) * sin_theta * d_theta * d_phi
    return float(total)


def grid_peak(rho, theta_values, phi_values):
    best = None
    for theta in theta_values:
        for phi in phi_values:
            q = husimi_q(rho, theta, phi)
            candidate = (q, theta, phi)
            if best is None or candidate[0] > best[0]:
                best = candidate
    return best


def grid_stats(rho, theta_values, phi_values):
    vals = [
        husimi_q(rho, theta, phi)
        for theta in theta_values
        for phi in phi_values
    ]
    return {
        "min": float(min(vals)),
        "max": float(max(vals)),
        "spread": float(max(vals) - min(vals)),
    }


def main():
    ket0 = ket([1, 0])
    ket1 = ket([0, 1])
    ketp = ket([1 / np.sqrt(2), 1 / np.sqrt(2)])

    rho_0 = dm(ket0)
    rho_1 = dm(ket1)
    rho_p = dm(ketp)
    rho_mm = np.eye(2, dtype=complex) / 2.0
    rho_mix = np.diag([0.7, 0.3]).astype(complex)

    theta_grid = np.linspace(0.0, np.pi, 13)
    phi_grid = np.linspace(0.0, 2.0 * np.pi, 25)

    peak_0 = grid_peak(rho_0, theta_grid, phi_grid)
    peak_1 = grid_peak(rho_1, theta_grid, phi_grid)
    peak_p = grid_peak(rho_p, theta_grid, phi_grid)

    stats_0 = grid_stats(rho_0, theta_grid, phi_grid)
    stats_p = grid_stats(rho_p, theta_grid, phi_grid)
    stats_mm = grid_stats(rho_mm, theta_grid, phi_grid)
    stats_mix = grid_stats(rho_mix, theta_grid, phi_grid)

    positive = {
        "pointwise_nonnegativity_on_grid": {
            "rho_0_min": stats_0["min"],
            "rho_p_min": stats_p["min"],
            "rho_mm_min": stats_mm["min"],
            "rho_mix_min": stats_mix["min"],
            "pass": min(stats_0["min"], stats_p["min"], stats_mm["min"], stats_mix["min"]) >= -EPS,
        },
        "normalization_is_approximately_one": {
            "rho_0": approx_sphere_integral(rho_0),
            "rho_p": approx_sphere_integral(rho_p),
            "rho_mm": approx_sphere_integral(rho_mm),
            "pass": all(
                abs(val - 1.0) < INTEGRAL_TOL
                for val in [
                    approx_sphere_integral(rho_0),
                    approx_sphere_integral(rho_p),
                    approx_sphere_integral(rho_mm),
                ]
            ),
        },
        "basis_peak_localization_and_shift": {
            "peak_0": {"q": peak_0[0], "theta": peak_0[1], "phi": peak_0[2]},
            "peak_1": {"q": peak_1[0], "theta": peak_1[1], "phi": peak_1[2]},
            "peak_p": {"q": peak_p[0], "theta": peak_p[1], "phi": peak_p[2]},
            "pass": peak_0[1] < np.pi / 4 and peak_1[1] > 3 * np.pi / 4 and abs(peak_p[1] - np.pi / 2) < np.pi / 4,
        },
    }

    negative = {
        "maximally_mixed_state_is_not_sharply_peaked": {
            "spread_mm": stats_mm["spread"],
            "spread_0": stats_0["spread"],
            "pass": stats_mm["spread"] < stats_0["spread"] - EPS,
        },
        "plus_state_does_not_share_z_pole_peak_with_zero_state": {
            "theta_zero": peak_0[1],
            "theta_plus": peak_p[1],
            "pass": abs(peak_0[1] - peak_p[1]) > np.pi / 6,
        },
    }

    boundary = {
        "interior_mixed_state_interpolates_between_pure_and_flat": {
            "spread_0": stats_0["spread"],
            "spread_mix": stats_mix["spread"],
            "spread_mm": stats_mm["spread"],
            "pass": stats_0["spread"] > stats_mix["spread"] > stats_mm["spread"],
        },
        "south_pole_state_peaks_opposite_north_pole_state": {
            "theta_zero": peak_0[1],
            "theta_one": peak_1[1],
            "pass": peak_1[1] - peak_0[1] > np.pi / 2,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "husimi_phase_space_representation",
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
            "scope_note": "Direct local qubit Husimi-Q representation lego on five bounded states and a fixed Bloch-sphere grid.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "husimi_phase_space_representation_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
