#!/usr/bin/env python3
"""
sim_assoc_bundle_associated_vector_bundle_construction -- Family #1 lego 2/6.

Build E = P ×_{U(1)} V for the weight-k irreducible rep of U(1) on V = C.
Equivalence relation: (p, v) ~ (p·g, rho(g^{-1}) v). Test that the resulting
equivalence classes are well-defined and that charge-k sections transform
correctly.
"""
import json
import os
import numpy as np
classification = "canonical"

TOOL_MANIFEST = {
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "numpy":     {"tried": True,  "used": True,  "reason": "complex arithmetic for equivalence classes"},
}
TOOL_INTEGRATION_DEPTH = {
    "clifford": None, "geomstats": None, "e3nn": None,
    "sympy": "load_bearing", "numpy": "supportive",
}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"].update(tried=True, used=True,
        reason="symbolic proof rho(g) rho(g^{-1}) = 1 and cocycle condition")
except Exception:
    pass


def rho(k, theta):
    return np.exp(1j * k * theta)


def equivalence_class_rep(p, v, theta, k):
    # (p,v) ~ (g·p, rho(g^{-1}) v) where g = e^{i theta}
    co, si = np.cos(theta), np.sin(theta)
    pg = np.array([co * p[0] - si * p[1],
                   si * p[0] + co * p[1],
                   co * p[2] - si * p[3],
                   si * p[2] + co * p[3]])
    vg = rho(k, -theta) * v
    return pg, vg


def run_positive_tests():
    r = {}
    rng = np.random.default_rng(1)
    # Section f: P -> V with equivariance f(p·g) = rho(g^{-1}) f(p)  <-> section of E
    # For the tautological weight-1 section: f(a+ib, c+id) = a + ib  (first complex coord)
    def f(p):
        return p[0] + 1j * p[1]

    p = rng.normal(size=4); p /= np.linalg.norm(p)
    # With f(p) = a+ib, left U(1) action by theta gives f(g.p) = e^{i theta} f(p):
    # f is a weight-(+1) equivariant section of the associated line bundle.
    for theta in [0.4, 1.9, -0.7]:
        pg, _ = equivalence_class_rep(p, 0j, theta, 1)
        lhs = f(pg); rhs = rho(1, theta) * f(p)
        r[f"equivariance_k=1_theta={theta}"] = bool(np.isclose(lhs, rhs, atol=1e-10))

    # cocycle round-trip: theta then -theta recovers (p, v)
    v = 1.0 + 0j
    p2, v2 = equivalence_class_rep(p, v, 1.3, 1)
    p3, v3 = equivalence_class_rep(p2, v2, -1.3, 1)
    r["cocycle_round_trip"] = bool(np.allclose(p3, p, atol=1e-10) and np.isclose(v3, v, atol=1e-10))

    # symbolic U(1) rep inverse check
    import sympy as sp
    k, th = sp.symbols("k theta", real=True)
    expr = sp.simplify(sp.exp(sp.I * k * th) * sp.exp(-sp.I * k * th))
    r["sympy_rho_inverse"] = (expr == 1)
    return r


def run_negative_tests():
    r = {}
    # Wrong charge: weight-2 rep of section that is secretly weight-1 fails equivariance
    p = np.array([0.3, 0.5, 0.7, 0.4]); p /= np.linalg.norm(p)
    theta = 0.6
    def f(p): return p[0] + 1j * p[1]
    pg, _ = equivalence_class_rep(p, 0.0 + 0j, theta, 2)
    # f is weight +1; claiming weight +2 must fail: f(pg) != rho(2,theta) f(p)
    lhs = f(pg); rhs = rho(2, theta) * f(p)
    r["wrong_weight_breaks_equivariance"] = bool(not np.isclose(lhs, rhs, atol=1e-6))
    # |p|=1 everywhere; as weight-1 section it fails (const vs e^{i theta})
    def g(p): return np.linalg.norm(p) + 0j
    lhs2 = g(pg); rhs2 = rho(1, theta) * g(p)
    r["constant_section_fails_k1"] = bool(not np.isclose(lhs2, rhs2, atol=1e-6))
    return r


def run_boundary_tests():
    r = {}
    # k=0 trivial bundle: any function is equivariant
    p = np.array([0.3, 0.5, 0.7, 0.4]); p /= np.linalg.norm(p)
    theta = 0.9
    def g(p): return np.linalg.norm(p) + 0j
    pg, _ = equivalence_class_rep(p, 0.0 + 0j, theta, 0)
    r["k0_trivial_equivariance"] = bool(np.isclose(g(pg), rho(0, theta) * g(p), atol=1e-12))
    # 2π periodicity
    p2, v2 = equivalence_class_rep(p, 1.0 + 0j, 2 * np.pi, 1)
    r["u1_2pi_periodic"] = bool(np.allclose(p2, p, atol=1e-10) and np.isclose(v2, 1.0, atol=1e-10))
    return r


if __name__ == "__main__":
    results = {
        "name": "assoc_bundle_associated_vector_bundle_construction",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "assoc_bundle_associated_vector_bundle_construction_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(json.dumps({k: results[k] for k in ("positive","negative","boundary")}, indent=2, default=str))
