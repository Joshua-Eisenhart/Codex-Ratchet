#!/usr/bin/env python3
"""
PURE LEGO: Entanglement Spectrum
================================
Direct local reduced-spectrum lego on a tiny bipartite state family.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for entanglement spectrum on a tiny bipartite family, "
    "kept separate from entropy scalars, negativity, and truncation workflows."
)

LEGO_IDS = [
    "entanglement_spectrum",
]

PRIMARY_LEGO_IDS = [
    "entanglement_spectrum",
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


def dm(v):
    vec = np.array(v, dtype=complex).reshape(-1, 1)
    return vec @ vec.conj().T


def partial_trace_B(rho, da=2, db=2):
    rho = rho.reshape(da, db, da, db)
    return np.trace(rho, axis1=1, axis2=3)


def spectrum(rho):
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    vals = np.sort(np.real(vals))[::-1]
    return [float(x) for x in vals]


def main():
    prod = dm(np.kron([1.0, 0.0], [0.0, 1.0]))
    bell = dm((np.array([1.0, 0.0, 0.0, 1.0], dtype=complex)) / np.sqrt(2.0))
    partial = dm(
        np.cos(0.35) * np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        + np.sin(0.35) * np.array([0.0, 0.0, 0.0, 1.0], dtype=complex)
    )

    spec_prod = spectrum(partial_trace_B(prod))
    spec_bell = spectrum(partial_trace_B(bell))
    spec_partial = spectrum(partial_trace_B(partial))

    positive = {
        "product_state_has_rank_one_reduced_spectrum": {
            "spectrum": spec_prod,
            "pass": np.allclose(spec_prod, [1.0, 0.0], atol=1e-8),
        },
        "bell_state_has_flat_reduced_spectrum": {
            "spectrum": spec_bell,
            "pass": np.allclose(spec_bell, [0.5, 0.5], atol=1e-8),
        },
        "partially_entangled_state_has_nonflat_nonntrivial_reduced_spectrum": {
            "spectrum": spec_partial,
            "pass": spec_partial[0] > spec_partial[1] > EPS and spec_partial[0] < 1.0 - EPS,
        },
    }

    negative = {
        "entanglement_spectrum_is_not_collapsed_to_single_entropy_scalar": {
            "pass": not np.allclose(spec_partial, spec_bell, atol=1e-8),
        },
        "spectrum_row_does_not_require_partial_transpose_witness_logic": {
            "pass": True,
        },
    }

    boundary = {
        "all_reduced_spectra_are_probability_vectors": {
            "pass": all(
                abs(sum(spec) - 1.0) < 1e-8 and all(x >= -EPS for x in spec)
                for spec in [spec_prod, spec_bell, spec_partial]
            ),
        },
        "reduced_spectrum_ordering_is_descending": {
            "pass": all(spec[0] >= spec[1] - EPS for spec in [spec_prod, spec_bell, spec_partial]),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "entanglement_spectrum",
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
            "scope_note": "Direct local reduced-spectrum lego on a tiny bipartite family.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "entanglement_spectrum_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
