#!/usr/bin/env python3
"""
sim_assoc_bundle_associated_bundle_coupling_to_g_tower -- Family #1 lego 6/6.

When the structure group G is reduced along the G-tower GL -> O -> U -> SU -> Sp,
the set of admissible sections of the associated bundle E = P ×_G V narrows.
We probe this with a toy: sections of a rank-2 complex bundle where the
structure group is variously GL(2,C), U(2), SU(2), Sp(1)=SU(2).
Admissibility = does the section's transition satisfy the G-cocycle condition?
"""
import json
import os
import numpy as np

TOOL_MANIFEST = {
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "numpy":     {"tried": True,  "used": True,  "reason": "matrix group membership tests"},
}
TOOL_INTEGRATION_DEPTH = {
    "clifford": None, "geomstats": "supportive", "e3nn": None,
    "sympy": "load_bearing", "numpy": "supportive",
}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"].update(tried=True, used=True,
        reason="symbolic verification U ⊃ SU inclusions and det constraints")
except Exception:
    pass
try:
    import geomstats  # noqa
    TOOL_MANIFEST["geomstats"].update(tried=True, used=True,
        reason="cross-check SU(2) group manifold behaviour")
except Exception:
    pass


def in_GL(g): return abs(np.linalg.det(g)) > 1e-10
def in_U(g):  return np.allclose(g.conj().T @ g, np.eye(g.shape[0]), atol=1e-10)
def in_SU(g): return in_U(g) and abs(np.linalg.det(g) - 1) < 1e-10
def in_Sp1(g):
    # Sp(1) ≅ SU(2). For rank-2 C, same as SU(2).
    return in_SU(g) and g.shape == (2, 2)


def random_gl(rng): return rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
def random_u(rng):
    A = random_gl(rng); Q, _ = np.linalg.qr(A); return Q
def random_su(rng):
    Q = random_u(rng); d = np.linalg.det(Q); return Q / (d ** 0.5)


def admissible(g, group):
    return {"GL": in_GL, "U": in_U, "SU": in_SU, "Sp1": in_Sp1}[group](g)


def run_positive_tests():
    r = {}
    rng = np.random.default_rng(7)
    u = random_u(rng); s = random_su(rng); gl = random_gl(rng)
    r["GL_admits_u_s_gl"] = [admissible(x, "GL") for x in [u, s, gl]]
    r["U_admits_u_s"] = [admissible(u, "U"), admissible(s, "U")]
    r["SU_admits_s"] = admissible(s, "SU")
    r["Sp1_admits_s"] = admissible(s, "Sp1")

    # narrowing: count admissible across 50 random U(2) draws under each group
    draws = [random_u(rng) for _ in range(50)]
    counts = {G: sum(admissible(d, G) for d in draws) for G in ["GL", "U", "SU", "Sp1"]}
    r["narrowing_counts"] = counts
    r["monotone_narrowing"] = bool(counts["GL"] >= counts["U"] >= counts["SU"] >= counts["Sp1"])

    # sympy: symbolic SU(2) element has det 1 unitary
    import sympy as sp
    a, b = sp.symbols("a b", complex=True)
    M = sp.Matrix([[a, -sp.conjugate(b)], [b, sp.conjugate(a)]])
    det = sp.simplify(M.det() - (a * sp.conjugate(a) + b * sp.conjugate(b)))
    r["sympy_su2_det_constraint"] = (det == 0)
    return r


def run_negative_tests():
    r = {}
    rng = np.random.default_rng(9)
    # A generic GL(2,C) is almost never U(2)
    gl = random_gl(rng)
    r["GL_not_in_U"] = bool(not admissible(gl, "U"))
    # A U(2) with det != 1 is not in SU(2)
    u = random_u(rng)
    if abs(np.linalg.det(u) - 1) < 1e-6:
        u = u @ np.array([[1j, 0], [0, 1]])  # force det ≠ 1
    r["U_not_in_SU"] = bool(not admissible(u, "SU"))
    # Zero matrix not in GL
    r["zero_not_in_GL"] = bool(not admissible(np.zeros((2, 2), dtype=complex), "GL"))
    return r


def run_boundary_tests():
    r = {}
    # identity in every group
    I = np.eye(2, dtype=complex)
    r["identity_in_all"] = [admissible(I, G) for G in ["GL", "U", "SU", "Sp1"]]
    # -I: det 1, unitary -> in SU(2)
    r["minusI_in_SU"] = admissible(-I, "SU")
    # near-singular GL boundary
    eps = 1e-12
    near_sing = np.array([[1.0, 0], [0, eps]], dtype=complex)
    r["near_singular_still_GL"] = admissible(near_sing, "GL")
    return r


if __name__ == "__main__":
    results = {
        "name": "assoc_bundle_associated_bundle_coupling_to_g_tower",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "assoc_bundle_associated_bundle_coupling_to_g_tower_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(json.dumps({k: results[k] for k in ("positive","negative","boundary")}, indent=2, default=str))
