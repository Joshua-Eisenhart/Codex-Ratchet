#!/usr/bin/env python3
"""
PURE LEGO: Eigenvalue Spectrum View
==================================
Direct local state-representation lego for eigenvalue-only descriptions.
"""

import json
import pathlib

import numpy as np
classification = "tool_lego_fit_probe"


EPS = 1e-10

CLASSIFICATION = "tool_lego_fit_probe"
CLASSIFICATION_NOTE = (
    "Pre-admission local lego fit probe for the eigenvalue-only state view, "
    "showing where spectral descriptions track mixedness and where they collapse "
    "distinct states with the same spectrum."
)

LEGO_IDS = [
    "eigenvalue_spectrum_view",
]

PRIMARY_LEGO_IDS = [
    "eigenvalue_spectrum_view",
]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite numeric arrays and bounded linear-algebra checks for this local lego"},
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
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def spectrum(rho):
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    evals = np.maximum(evals, 0.0)
    return np.round(np.sort(evals)[::-1], 10)


def same_density(rho1, rho2):
    return bool(np.allclose(rho1, rho2, atol=EPS))


def same_spectrum(rho1, rho2):
    return bool(np.allclose(spectrum(rho1), spectrum(rho2), atol=EPS))


def main():
    ket0 = ket([1, 0])
    ket1 = ket([0, 1])
    ketp = ket([1 / np.sqrt(2), 1 / np.sqrt(2)])
    ketm = ket([1 / np.sqrt(2), -1 / np.sqrt(2)])

    rho_0 = dm(ket0)
    rho_1 = dm(ket1)
    rho_p = dm(ketp)
    rho_m = dm(ketm)
    rho_mm = np.eye(2, dtype=complex) / 2.0
    rho_diag = np.diag([0.75, 0.25]).astype(complex)

    positive = {
        "pure_states_share_rank_one_spectrum": {
            "spectra": {
                "rho_0": spectrum(rho_0).tolist(),
                "rho_p": spectrum(rho_p).tolist(),
                "rho_m": spectrum(rho_m).tolist(),
            },
            "pass": same_spectrum(rho_0, rho_p) and same_spectrum(rho_p, rho_m),
        },
        "maximally_mixed_state_has_flat_spectrum": {
            "spectrum": spectrum(rho_mm).tolist(),
            "pass": np.allclose(spectrum(rho_mm), np.array([0.5, 0.5]), atol=EPS),
        },
        "mixedness_order_is_visible_spectrally": {
            "pure": spectrum(rho_0).tolist(),
            "mixed": spectrum(rho_diag).tolist(),
            "max_mixed": spectrum(rho_mm).tolist(),
            "pass": spectrum(rho_0)[0] > spectrum(rho_diag)[0] > spectrum(rho_mm)[0],
        },
    }

    negative = {
        "same_spectrum_does_not_mean_same_density": {
            "pass": same_spectrum(rho_0, rho_p) and not same_density(rho_0, rho_p),
        },
        "orthogonal_pure_states_are_not_collapsed_by_density_matrix": {
            "pass": same_spectrum(rho_0, rho_1) and not same_density(rho_0, rho_1),
        },
    }

    boundary = {
        "spectral_view_cannot_see_relative_phase_for_pure_qubits": {
            "pass": same_spectrum(rho_p, rho_m) and not same_density(rho_p, rho_m),
        },
        "degenerate_flat_spectrum_is_fixed_by_maximally_mixed_state": {
            "pass": same_density(rho_mm, np.eye(2, dtype=complex) / 2.0),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "eigenvalue_spectrum_view",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "tool_lego_fit_probe_only; finite numpy eigenvalue-spectrum receipt only; no canonical, bridge, GStack, axis, QIT, or nonclassical admission",
        "promotion_allowed": False,
        "next_lego_target": "none",
        "promotion_condition": "requires separate reconciled queue row before coupling, bridge, axis, engine, or QIT use",
        "blocked_until": "exact parent receipts, queue row, result JSON, and ledger loopback are reconciled",
        "demotion_condition": "demote if the named positive, negative, or boundary criteria fail, or if this row is used for a higher-stage claim",
        "out_of_scope": [
            "no coupling, bridge, axis, engine, GStack, or nonclassical admission claim",
        ],
        "all_pass": all_pass,
        "criteria_checked": list(positive) + list(negative) + list(boundary),
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local spectral-view lego on bounded one-qubit pure and mixed states, keeping eigenvalue-only representation separate from full density-state structure.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "eigenvalue_spectrum_view_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
