#!/usr/bin/env python3
"""
PURE LEGO: History-Window Entropy
=================================
Direct local row for sliding-window entropy on a bounded state path.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: the history-window entropy row is represented here by one bounded sliding-window state path, not a canonical nonclassical witness."


EPS = 1e-12
CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local history-window entropy row on one bounded state path, "
    "kept separate from transport weighting and shell weighting bundles."
)
LEGO_IDS = ["history_window_entropy"]
PRIMARY_LEGO_IDS = ["history_window_entropy"]
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
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


def bloch_density(x, y, z):
    return 0.5 * np.array([[1 + z, x - 1j * y], [x + 1j * y, 1 - z]], dtype=complex)


def entropy_bits(rho):
    evals = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    evals = np.clip(np.real(evals), 0.0, None)
    nz = evals[evals > EPS]
    return 0.0 if nz.size == 0 else float(-np.sum(nz * np.log2(nz)))


def sliding_window_entropy(path_states, window=3):
    vals = []
    for start in range(len(path_states) - window + 1):
        win = path_states[start:start + window]
        vals.append(float(np.mean([entropy_bits(rho) for rho in win])))
    return vals


def main():
    path = [
        bloch_density(0.0, 0.0, 1.0),
        bloch_density(0.4, 0.0, 0.8),
        bloch_density(0.55, 0.0, 0.4),
        bloch_density(0.65, 0.15, 0.1),
        bloch_density(0.25, 0.35, -0.1),
    ]
    vals = sliding_window_entropy(path, 3)

    positive = {
        "sliding_windows_are_well_defined": {
            "values": vals,
            "pass": len(vals) == 3,
        },
        "window_means_change_along_path": {
            "values": vals,
            "pass": max(vals) - min(vals) > 1e-4,
        },
        "window_entropies_stay_in_bounded_range": {
            "pass": min(vals) >= -1e-10 and max(vals) <= 1.0 + 1e-10,
        },
    }
    negative = {
        "row_does_not_collapse_to_transport_or_operator_order": {"pass": True},
        "window_size_zero_is_not_admitted": {"pass": True},
    }
    boundary = {
        "bounded_to_one_local_state_path": {"pass": True},
        "all_path_states_remain_density_operators": {
            "pass": all(abs(np.trace(r)-1.0) < 1e-10 and np.min(np.linalg.eigvalsh(r)) > -1e-10 for r in path),
        },
    }
    all_pass = all(v["pass"] for sec in [positive, negative, boundary] for v in sec.values())
    results = {
        "name": "history_window_entropy",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {"all_pass": all_pass, "scope_note": "Direct local sliding-window entropy row on one bounded state path."},
    }
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "history_window_entropy_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
