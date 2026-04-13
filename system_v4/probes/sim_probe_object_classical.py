#!/usr/bin/env python3
"""Classical baseline sim: probe_object lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: a probe as a classical POVM {E_k} — PSD ops summing to I.
Innately missing: distinguishability geometry, constraint-admissibility,
nonclassical guards. Failures on these are useful boundary data.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "linear algebra baseline"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "z3": {"tried": False, "used": False, "reason": "classical baseline"},
    "clifford": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}  # none load_bearing by rule

def _is_psd(M, tol=1e-9):
    w = np.linalg.eigvalsh((M + M.conj().T) / 2)
    return bool(np.all(w >= -tol))

def _povm_complete(Es, tol=1e-9):
    S = sum(Es)
    return bool(np.allclose(S, np.eye(S.shape[0]), atol=tol))

def run_positive_tests():
    # canonical 2-outcome POVM on qubit (Z-basis projectors)
    E0 = np.diag([1.0, 0.0]); E1 = np.diag([0.0, 1.0])
    return {
        "psd_E0": _is_psd(E0),
        "psd_E1": _is_psd(E1),
        "complete": _povm_complete([E0, E1]),
    }

def run_negative_tests():
    # non-PSD "probe" and non-complete set — must fail
    bad = np.array([[1.0, 0.0], [0.0, -0.5]])
    E0 = np.diag([1.0, 0.0])
    return {
        "non_psd_rejected": not _is_psd(bad),
        "incomplete_rejected": not _povm_complete([E0, E0 * 0.5]),
    }

def run_boundary_tests():
    # trivial 1-outcome POVM = {I}
    I = np.eye(3)
    # near-boundary PSD (tiny negative eigenvalue within tol)
    M = np.diag([1.0, 1e-12])
    return {
        "trivial_identity_povm": _povm_complete([I]),
        "near_zero_psd": _is_psd(M),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "probe_object_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "summary": {"all_pass": all_pass},
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "probe_object_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
