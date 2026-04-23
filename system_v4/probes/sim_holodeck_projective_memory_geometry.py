#!/usr/bin/env python3
"""sim_holodeck_projective_memory_geometry -- memory geometry under projection.

Thesis: memory on the holodeck is stored as rank-1 projectors P = |v><v|.
The memory geometry is then the Fubini-Study-like chordal distance
d(P,Q) = sqrt(1 - Tr(PQ)) on unit rays. We test nonnegativity, symmetry,
and the identity-of-indiscernibles under projection (classical_baseline).
Clifford algebra is used supportively to represent vectors as Cl(3) 1-vectors.
"""
import numpy as np
import sys, os
from clifford import Cl
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _holodeck_common import write_results, summary_ok

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']

divergence_log = "Classical baseline: projective memory geometry is modeled here by projector-distance numerics with Clifford-backed vectors, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "projector arithmetic and chordal-distance numerics"},
    "clifford": {"tried": True, "used": True, "reason": "Cl(3) vector construction"},
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
    "clifford": "supportive",
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


def vec_to_np(mv):
    return np.array([mv[e1], mv[e2], mv[e3]], dtype=float)


def proj(v):
    v = v / np.linalg.norm(v)
    return np.outer(v, v)


def chordal(P, Q):
    return float(np.sqrt(max(0.0, 1.0 - np.trace(P @ Q))))


def run_positive_tests():
    r = {}
    v = vec_to_np(1.0 * e1 + 2.0 * e2)
    w = vec_to_np(1.0 * e2 + 1.0 * e3)
    P, Q = proj(v), proj(w)
    r["nonneg"] = chordal(P, Q) >= 0
    r["symmetric"] = abs(chordal(P, Q) - chordal(Q, P)) < 1e-12
    r["self_zero"] = chordal(P, P) < 1e-6
    return r


def run_negative_tests():
    r = {}
    v = vec_to_np(1.0 * e1)
    w = vec_to_np(1.0 * e2)
    P, Q = proj(v), proj(w)
    # distinct rays should NOT have zero distance
    r["distinct_zero"] = chordal(P, Q) < 1e-9
    # triangle violation claim: d(P,Q) > d(P,R) + d(R,Q)
    u = vec_to_np(1.0 * e1 + 1.0 * e2)
    R = proj(u)
    r["triangle_violated"] = chordal(P, Q) > chordal(P, R) + chordal(R, Q) + 1e-9
    return r


def run_boundary_tests():
    r = {}
    # orthogonal rays give maximum chordal distance = 1
    P = proj(vec_to_np(1.0 * e1))
    Q = proj(vec_to_np(1.0 * e2))
    r["orthogonal_max"] = abs(chordal(P, Q) - 1.0) < 1e-9
    # scaled vectors produce same projector
    P1 = proj(vec_to_np(1.0 * e1 + 2.0 * e3))
    P2 = proj(vec_to_np(3.0 * e1 + 6.0 * e3))
    r["scale_invariant"] = np.allclose(P1, P2)
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_holodeck_projective_memory_geometry",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["pass"] = summary_ok(results)
    path = write_results("sim_holodeck_projective_memory_geometry", results)
    print(f"pass={results['pass']} -> {path}")
    sys.exit(0 if results["pass"] else 1)
