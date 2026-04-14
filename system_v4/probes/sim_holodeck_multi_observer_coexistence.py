#!/usr/bin/env python3
"""sim_holodeck_multi_observer_coexistence -- two observers share a carrier.

Thesis: two observer projections pi_A, pi_B coexist on the same carrier
iff their slices are jointly admissible (no contradictory measurements
on the intersection of their ranges). We test agreement on the overlap.
"""
import numpy as np
import sys, os
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _holodeck_common import write_results, summary_ok

divergence_log = "Classical baseline: multi-observer coexistence is represented here by subspace-overlap numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "subspace intersection and projection checks"},
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


def coexist(pi_A, pi_B, m_A, m_B, tol=1e-8):
    # overlap projector: pi_A @ pi_B @ pi_A (commuting diag case)
    overlap = pi_A @ pi_B
    # residual on overlap
    return np.allclose(overlap @ m_A, overlap @ m_B, atol=tol)


def run_positive_tests():
    r = {}
    n = 4
    pi_A = np.diag([1, 1, 1, 0]).astype(float)
    pi_B = np.diag([0, 1, 1, 1]).astype(float)
    v = np.array([1.0, 2.0, 3.0, 4.0])
    m_A = pi_A @ v
    m_B = pi_B @ v
    r["shared_carrier_consistent"] = coexist(pi_A, pi_B, m_A, m_B)
    # disjoint observers trivially coexist (empty overlap)
    pi_C = np.diag([1, 0, 0, 0]).astype(float)
    pi_D = np.diag([0, 0, 0, 1]).astype(float)
    r["disjoint_trivially_coexist"] = coexist(pi_C, pi_D, pi_C @ v, pi_D @ v)
    return r


def run_negative_tests():
    r = {}
    # Contradictory measurements on overlap -- should NOT coexist
    pi_A = np.diag([1, 1, 0, 0]).astype(float)
    pi_B = np.diag([0, 1, 1, 0]).astype(float)
    m_A = np.array([1, 2, 0, 0], dtype=float)
    m_B = np.array([0, 99, 3, 0], dtype=float)  # disagree at coord 1
    r["contradiction_coexists"] = coexist(pi_A, pi_B, m_A, m_B)
    return r


def run_boundary_tests():
    r = {}
    # two identical observers always coexist
    pi = np.diag([1, 1, 0, 0]).astype(float)
    v = np.array([1.0, 2.0, 3.0, 4.0])
    r["identical_coexist"] = coexist(pi, pi, pi @ v, pi @ v)
    # one observer is full carrier -- coexistence reduces to agreement on other's range
    I = np.eye(4)
    pi_A = np.diag([1, 0, 0, 0]).astype(float)
    r["full_with_partial"] = coexist(I, pi_A, v, pi_A @ v)
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_holodeck_multi_observer_coexistence",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["pass"] = summary_ok(results)
    path = write_results("sim_holodeck_multi_observer_coexistence", results)
    print(f"pass={results['pass']} -> {path}")
    sys.exit(0 if results["pass"] else 1)
