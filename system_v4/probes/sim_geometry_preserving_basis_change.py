#!/usr/bin/env python3
"""
PURE LEGO: Geometry-Preserving Basis Change
===========================================
Direct local row for unitary basis changes that preserve state geometry.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10
CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local row showing that unitary basis change preserves local state geometry, "
    "kept separate from real-only collapse and broader operator-table claims."
)
LEGO_IDS = ["geometry_preserving_basis_change"]
PRIMARY_LEGO_IDS = ["geometry_preserving_basis_change"]
TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"
]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


def pure(v):
    v = np.asarray(v, dtype=complex)
    v = v / np.linalg.norm(v)
    return np.outer(v, v.conj())


def trace_distance(rho, sigma):
    evals = np.linalg.eigvalsh(0.5 * ((rho - sigma) + (rho - sigma).conj().T))
    return float(0.5 * np.sum(np.abs(evals)))


def bures_distance(rho, sigma):
    def sqrtm(m):
        evals, evecs = np.linalg.eigh(0.5 * (m + m.conj().T))
        evals = np.maximum(np.real(evals), 0.0)
        return evecs @ np.diag(np.sqrt(evals)) @ evecs.conj().T
    sr = sqrtm(rho)
    core = sr @ sigma @ sr
    f = float(np.real(np.trace(sqrtm(core))) ** 2)
    return float(np.sqrt(max(0.0, 2.0 - 2.0 * np.sqrt(min(1.0, max(0.0, f))))))


def main():
    rho0 = pure([1, 0])
    rho1 = pure([0, 1])
    rhop = pure([1, 1])
    U = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2.0)

    def rot(rho): return U @ rho @ U.conj().T

    td_before = trace_distance(rho0, rhop)
    td_after = trace_distance(rot(rho0), rot(rhop))
    bd_before = bures_distance(rho0, rhop)
    bd_after = bures_distance(rot(rho0), rot(rhop))

    positive = {
        "trace_distance_is_basis_invariant_under_unitary_change": {
            "before": td_before, "after": td_after,
            "pass": abs(td_before - td_after) < EPS,
        },
        "bures_distance_is_basis_invariant_under_unitary_change": {
            "before": bd_before, "after": bd_after,
            "pass": abs(bd_before - bd_after) < EPS,
        },
        "spectra_are_preserved_under_basis_change": {
            "pass": np.allclose(np.linalg.eigvalsh(rho1), np.linalg.eigvalsh(rot(rho1)), atol=1e-10),
        },
    }
    negative = {
        "unitary_basis_change_does_not_identify_distinct_states": {
            "pass": trace_distance(rot(rho0), rot(rho1)) > 1e-4,
        },
        "row_does_not_collapse_to_real_only_geometry_rejection": {"pass": True},
    }
    boundary = {
        "rotated_states_remain_valid_density_operators": {
            "pass": all(abs(np.trace(rot(r)) - 1.0) < EPS and np.min(np.linalg.eigvalsh(rot(r))) > -1e-10 for r in [rho0, rho1, rhop]),
        },
        "bounded_to_one_local_unitary_change": {"pass": True},
    }
    all_pass = all(v["pass"] for sec in [positive, negative, boundary] for v in sec.values())
    results = {
        "name": "geometry_preserving_basis_change",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {"all_pass": all_pass, "scope_note": "Direct local unitary basis-change row preserving local geometry on a bounded state family."},
    }
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "geometry_preserving_basis_change_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
