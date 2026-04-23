#!/usr/bin/env python3
"""sim 2: toponetx Hodge-Laplacian kernel dim == gudhi Betti number on a cell complex.
Torus as 3x3 periodic grid of squares. Both tools load-bearing.
"""
import json, os, numpy as np
from toponetx.classes import CellComplex
import gudhi

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "numeric linalg only"},
    "pyg": {"tried": False, "used": False, "reason": "no MP"},
    "z3": {"tried": False, "used": False, "reason": "numeric check"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT"},
    "sympy": {"tried": False, "used": False, "reason": "numeric"},
    "clifford": {"tried": False, "used": False, "reason": "no geometry"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "not required"},
    "xgi": {"tried": False, "used": False, "reason": "cell complex not hypergraph"},
    "toponetx": {"tried": True, "used": True, "reason": "builds CellComplex, provides incidence matrices for Hodge Laplacians; load-bearing"},
    "gudhi": {"tried": True, "used": True, "reason": "independently computes Betti via simplicial persistence; load-bearing cross-check"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"

N_TORUS = 4  # need >=4 for valid simplicial torus triangulation (no self-id of diagonals)

def torus_cell_complex(n=N_TORUS):
    cc = CellComplex()
    def v(i,j): return (i%n)*n + (j%n)
    for i in range(n):
        for j in range(n):
            cc.add_cell([v(i,j), v(i+1,j), v(i+1,j+1), v(i,j+1)], rank=2)
    return cc

def hodge_kernels(cc):
    B1 = cc.incidence_matrix(1).toarray().astype(float)
    B2 = cc.incidence_matrix(2).toarray().astype(float)
    L0 = B1 @ B1.T
    L1 = B1.T @ B1 + B2 @ B2.T
    L2 = B2.T @ B2
    return [int((np.linalg.eigvalsh(L) < 1e-8).sum()) for L in (L0, L1, L2)]

def torus_betti_via_gudhi(n=N_TORUS):
    # Encode the same cell complex as simplicial (triangulate each square)
    st = gudhi.SimplexTree()
    def v(i,j): return (i%n)*n + (j%n)
    for i in range(n):
        for j in range(n):
            a,b,c,d = v(i,j), v(i+1,j), v(i+1,j+1), v(i,j+1)
            st.insert([a,b,c], filtration=0.0); st.insert([a,c,d], filtration=0.0)
    st.set_dimension(2)
    st.compute_persistence(persistence_dim_max=True)
    b = st.betti_numbers()
    while len(b) < 3: b.append(0)
    return b[:3]

def run_positive_tests():
    cc = torus_cell_complex(N_TORUS)
    hk = hodge_kernels(cc)
    bg = torus_betti_via_gudhi(N_TORUS)
    return {f"torus_{N_TORUS}x{N_TORUS}": {"hodge_kernels": hk, "gudhi_betti": bg,
                          "expected": [1,2,1],
                          "pass": hk == [1,2,1] and bg == [1,2,1] and hk == bg}}

def run_negative_tests():
    # disk (single square, no periodic) has Betti (1,0,0) and Hodge kernel dims same
    cc = CellComplex()
    cc.add_cell([0,1,2,3], rank=2)
    hk = hodge_kernels(cc)
    st = gudhi.SimplexTree()
    st.insert([0,1,2], filtration=0.0); st.insert([0,2,3], filtration=0.0)
    st.set_dimension(2)
    st.compute_persistence(persistence_dim_max=True)
    bg = st.betti_numbers()
    while len(bg) < 3: bg.append(0);
    bg = bg[:3]
    return {"disk_not_torus": {"hodge_kernels": hk, "gudhi_betti": bg,
                               "pass": hk != [1,2,1] and bg != [1,2,1] and hk == bg}}

def run_boundary_tests():
    # Sphere S^2 as tetrahedron boundary: Betti (1,0,1). Hodge kernels should match.
    st = gudhi.SimplexTree()
    for tri in [[0,1,2],[0,1,3],[0,2,3],[1,2,3]]:
        st.insert(tri, filtration=0.0)
    st.set_dimension(2)
    st.compute_persistence(persistence_dim_max=True)
    bg = st.betti_numbers()
    while len(bg) < 3: bg.append(0)
    bg = bg[:3]
    # Build same as CellComplex with triangular 2-cells
    cc = CellComplex()
    for tri in [[0,1,2],[0,1,3],[0,2,3],[1,2,3]]:
        cc.add_cell(tri, rank=2)
    hk = hodge_kernels(cc)
    return {"sphere_tetrahedron": {"hodge_kernels": hk, "gudhi_betti": bg,
                                    "expected": [1,0,1],
                                    "pass": hk == [1,0,1] and bg == [1,0,1]}}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "toponetx_gudhi_hodge_betti_cross",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "toponetx_gudhi_hodge_betti_cross_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
    print(f"ALL_PASS={all_pass}")
