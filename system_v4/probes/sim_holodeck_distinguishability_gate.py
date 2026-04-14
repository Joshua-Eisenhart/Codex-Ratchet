#!/usr/bin/env python3
"""sim_holodeck_distinguishability_gate.

Thesis: the holodeck only admits states that are probe-distinguishable.
Two carrier rays v, w are *indistinguishable under probe set M* iff
Tr(M_k P_v) = Tr(M_k P_w) for every M_k. We gate admissibility on a
minimal distinguishing probe family.
"""
import numpy as np
import sys, os
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _holodeck_common import write_results, summary_ok

divergence_log = "Classical baseline: holodeck distinguishability is tested here by finite probe-family numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "trace-based probe evaluation"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "clifford": None,
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


def proj(v):
    v = v / np.linalg.norm(v)
    return np.outer(v, v)


def distinguishable(P, Q, probes, tol=1e-9):
    for M in probes:
        if abs(np.trace(M @ P) - np.trace(M @ Q)) > tol:
            return True
    return False


def pauli_probes():
    X = np.array([[0, 1], [1, 0]], dtype=float)
    Y = np.array([[0, -1j], [1j, 0]])
    Z = np.array([[1, 0], [0, -1]], dtype=float)
    return [X, Y, Z]


def run_positive_tests():
    r = {}
    probes = pauli_probes()
    v = np.array([1.0, 0.0]); w = np.array([0.0, 1.0])
    r["orthogonal_distinguishable"] = distinguishable(proj(v), proj(w), probes)
    v2 = np.array([1.0, 1.0]) / np.sqrt(2); w2 = np.array([1.0, -1.0]) / np.sqrt(2)
    r["superposition_distinguishable"] = distinguishable(proj(v2), proj(w2), probes)
    return r


def run_negative_tests():
    r = {}
    probes = pauli_probes()
    v = np.array([1.0, 0.0])
    # same state -- MUST be indistinguishable
    r["same_state_distinguishable"] = distinguishable(proj(v), proj(v), probes)
    # empty probe set -- nothing is distinguishable
    v2 = np.array([0.0, 1.0])
    r["empty_probes_distinguish"] = distinguishable(proj(v), proj(v2), [])
    return r


def run_boundary_tests():
    r = {}
    probes = pauli_probes()
    # global phase -- same ray -- indistinguishable
    v = np.array([1.0, 0.0], dtype=complex)
    w = np.exp(1j * 0.7) * v
    # use real part of projector comparison
    P = np.outer(v, v.conj())
    Q = np.outer(w, w.conj())
    r["global_phase_same"] = not distinguishable(P, Q, probes, tol=1e-9)
    # near-identical states: tiny angle still distinguishable by Z
    a = np.array([1.0, 0.0]); b = np.array([np.cos(1e-3), np.sin(1e-3)])
    r["tiny_angle_distinguishable"] = distinguishable(proj(a), proj(b), probes, tol=1e-12)
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_holodeck_distinguishability_gate",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["pass"] = summary_ok(results)
    path = write_results("sim_holodeck_distinguishability_gate", results)
    print(f"pass={results['pass']} -> {path}")
    sys.exit(0 if results["pass"] else 1)
