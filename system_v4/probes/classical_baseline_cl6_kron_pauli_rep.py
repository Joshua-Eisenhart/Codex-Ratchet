#!/usr/bin/env python3
"""classical baseline cl6 kron pauli rep

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

NAME = "classical_baseline_cl6_kron_pauli_rep"

I2 = np.eye(2, dtype=complex)
sx = np.array([[0,1],[1,0]], dtype=complex)
sy = np.array([[0,-1j],[1j,0]], dtype=complex)
sz = np.array([[1,0],[0,-1]], dtype=complex)

# 6 anticommuting generators in 8x8 (Cl(6) has dim 2^3=8 spinor rep)
g = [
    np.kron(np.kron(sx, I2), I2),
    np.kron(np.kron(sy, I2), I2),
    np.kron(np.kron(sz, sx), I2),
    np.kron(np.kron(sz, sy), I2),
    np.kron(np.kron(sz, sz), sx),
    np.kron(np.kron(sz, sz), sy),
]

def run_positive_tests():
    out = {}
    I8 = np.eye(8, dtype=complex)
    # anticommutation {g_i, g_j} = 2 delta_ij I
    bad = 0
    for i in range(6):
        for j in range(6):
            ac = g[i] @ g[j] + g[j] @ g[i]
            target = 2*I8 if i==j else np.zeros((8,8), dtype=complex)
            if not np.allclose(ac, target, atol=1e-10):
                bad += 1
    out["anticommute_6x6"] = {"pass": (bad==0), "violations": bad}
    # each g_i^2 = I
    sq_ok = all(np.allclose(gi@gi, I8, atol=1e-10) for gi in g)
    out["square_to_I"] = {"pass": bool(sq_ok)}
    return out

def run_negative_tests():
    # A fake extra "generator" equal to g[0] should FAIL anticommutation with g[0]
    fake = g[0].copy()
    ac = g[0]@fake + fake@g[0]
    return {"fake_gen_not_anticommute": {"pass": bool(not np.allclose(ac, np.zeros_like(ac)))}}

def run_boundary_tests():
    # Chirality element = i^3 * prod(g) should square to I
    chi = (1j)**3 * g[0]@g[1]@g[2]@g[3]@g[4]@g[5]
    return {"chirality_squares_to_I": {"pass": bool(np.allclose(chi@chi, np.eye(8, dtype=complex), atol=1e-10))}}


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
