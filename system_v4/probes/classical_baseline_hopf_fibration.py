#!/usr/bin/env python3
"""classical baseline hopf fibration

classical_baseline, numpy-only. Non-canon. Lane_B-eligible.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "numpy":    {"tried": True,  "used": True,  "reason": "load-bearing linear algebra / rng for classical baseline"},
    "pytorch":  {"tried": False, "used": False, "reason": "classical_baseline sim; torch not required"},
    "pyg":      {"tried": False, "used": False, "reason": "no graph-NN step in this baseline"},
    "z3":       {"tried": False, "used": False, "reason": "equality-based checks; no UNSAT proof in baseline"},
    "cvc5":     {"tried": False, "used": False, "reason": "equality-based checks; no UNSAT proof in baseline"},
    "sympy":    {"tried": False, "used": False, "reason": "numerical identity sufficient; symbolic not needed here"},
    "clifford": {"tried": False, "used": False, "reason": "matrix rep baseline; Cl(n) algebra deferred to canonical lane"},
    "geomstats":{"tried": False, "used": False, "reason": "flat/discrete baseline; manifold tooling out of scope"},
    "e3nn":     {"tried": False, "used": False, "reason": "no equivariant NN in baseline"},
    "rustworkx":{"tried": False, "used": False, "reason": "small adjacency handled by numpy"},
    "xgi":      {"tried": False, "used": False, "reason": "no hypergraph structure in this sim"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex in this sim"},
    "gudhi":    {"tried": False, "used": False, "reason": "no persistent homology in this sim"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None, "rustworkx": None,
    "xgi": None, "toponetx": None, "gudhi": None,
}

NAME = "classical_baseline_hopf_fibration"

def hopf(z1, z2):
    # map S^3 subset C^2 -> S^2 subset R^3
    x = 2*(z1*np.conj(z2)).real
    y = 2*(z1*np.conj(z2)).imag
    z = abs(z1)**2 - abs(z2)**2
    return np.array([x, y, z])

def run_positive_tests():
    rng = np.random.default_rng(0)
    out = {}
    for k in range(6):
        z = rng.standard_normal(2) + 1j*rng.standard_normal(2)
        z = z / np.linalg.norm(z)  # on S^3
        p = hopf(z[0], z[1])
        out[f"on_s2_{k}"] = {"pass": bool(np.isclose(np.linalg.norm(p), 1.0, atol=1e-10))}
    # Fiber invariance: multiply by e^{i phi} leaves point on S^2 unchanged
    z = np.array([0.6+0.1j, 0.2-0.77j]); z = z/np.linalg.norm(z)
    p1 = hopf(z[0], z[1])
    phi = 1.234
    z2 = z * np.exp(1j*phi)
    p2 = hopf(z2[0], z2[1])
    out["fiber_invariance"] = {"pass": bool(np.allclose(p1, p2, atol=1e-10))}
    return out

def run_negative_tests():
    # Non-U(1) perturbation (different phase per component) should move the point
    z = np.array([0.6+0.1j, 0.2-0.77j]); z = z/np.linalg.norm(z)
    p1 = hopf(z[0], z[1])
    z2 = np.array([z[0]*np.exp(1j*0.5), z[1]*np.exp(1j*1.1)])
    z2 = z2/np.linalg.norm(z2)
    p2 = hopf(z2[0], z2[1])
    return {"nonuniform_phase_moves_point": {"pass": bool(not np.allclose(p1, p2, atol=1e-6))}}

def run_boundary_tests():
    # North pole: z2=0 -> (0,0,1)
    p = hopf(1.0+0j, 0.0+0j)
    # South pole: z1=0 -> (0,0,-1)
    q = hopf(0.0+0j, 1.0+0j)
    return {"north_pole": {"pass": bool(np.allclose(p, [0,0,1]))},
            "south_pole": {"pass": bool(np.allclose(q, [0,0,-1]))}}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        all(v.get("pass") for v in pos.values()) and
        all(v.get("pass") for v in neg.values()) and
        all(v.get("pass") for v in bnd.values())
    )
    results = {
        "name": NAME,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, NAME + "_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{NAME}: all_pass={all_pass} -> {out_path}")
