#!/usr/bin/env python3
"""
sim_toponetx_deep_simplicial_vs_cell_distinguishability

Scope note: admissibility claim -- a square face (4-cycle filled by a single
2-cell) and its simplicial triangulation (two triangles across a diagonal)
must be indistinguishable under H_* (same Betti numbers) but distinguishable
under cell count / L1 spectrum cardinality. Fence: see
system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md (cell/simplicial
admission ladder). Without toponetx offering BOTH CellComplex and
SimplicialComplex with compatible Hodge operators, the claim "same homology,
different decomposition" cannot be tested; toponetx is load_bearing.

Classification: canonical.
"""
import json, os, sys
import numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from toponetx.classes import CellComplex, SimplicialComplex
    TOOL_MANIFEST["toponetx"] = {"tried": True, "used": True,
        "reason": "Provides both CellComplex and SimplicialComplex with a shared "
                  "hodge_laplacian_matrix API. The admissibility equivalence "
                  "(same b_k) and distinction (different |spectrum|) is only "
                  "expressible in toponetx's dual API -- load_bearing."}
    TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"
except ImportError as e:
    print(f"BROKEN ENV: {e}", file=sys.stderr); sys.exit(2)


def _betti(L):
    L = (L + L.T) / 2.0
    return int(np.sum(np.abs(np.linalg.eigvalsh(L)) < 1e-8))


def run_positive_tests():
    out = {}
    cc = CellComplex(); cc.add_cell([1,2,3,4], rank=2)
    sc = SimplicialComplex([[1,2,3],[1,3,4]])
    L0c = cc.hodge_laplacian_matrix(0).toarray()
    L1c = cc.hodge_laplacian_matrix(1).toarray()
    L0s = sc.hodge_laplacian_matrix(0).toarray()
    L1s = sc.hodge_laplacian_matrix(1).toarray()
    b0c, b1c = _betti(L0c), _betti(L1c)
    b0s, b1s = _betti(L0s), _betti(L1s)
    out["same_homology"] = {"PASS": (b0c, b1c) == (b0s, b1s) == (1, 0),
        "cell": [b0c, b1c], "simplicial": [b0s, b1s],
        "language": "indistinguishable under H_*"}
    out["different_decomposition"] = {
        "PASS": L1c.shape != L1s.shape,
        "cell_L1": list(L1c.shape), "simplicial_L1": list(L1s.shape),
        "language": "distinguishable under cell-count probe"}
    return out


def run_negative_tests():
    out = {}
    # Negative: simplicial hollow triangle vs filled -- b1 differs, claim would fail
    sc_hollow = SimplicialComplex([[0,1],[1,2],[0,2]])
    sc_filled = SimplicialComplex([[0,1,2]])
    b1_h = _betti(sc_hollow.hodge_laplacian_matrix(1).toarray())
    b1_f = _betti(sc_filled.hodge_laplacian_matrix(1).toarray())
    out["hollow_vs_filled_distinguishable"] = {
        "PASS": b1_h != b1_f, "hollow": b1_h, "filled": b1_f,
        "language": "excluded: different H_1 -> not indistinguishable"}
    # Negative 2: two different simplicial triangulations of square give SAME L1 shape (5 edges each)
    sc_a = SimplicialComplex([[1,2,3],[1,3,4]])
    sc_b = SimplicialComplex([[1,2,4],[2,3,4]])
    shape_a = sc_a.hodge_laplacian_matrix(1).toarray().shape
    shape_b = sc_b.hodge_laplacian_matrix(1).toarray().shape
    out["diag_swap_same_edge_count"] = {
        "PASS": shape_a == shape_b, "a": list(shape_a), "b": list(shape_b),
        "language": "excluded: same simplicial dim -> edge-count probe alone cannot distinguish"}
    return out


def run_boundary_tests():
    out = {}
    # single vertex
    # two points + edge (minimal dim>=1) to exercise L0
    sc = SimplicialComplex([[0, 1]])
    out["edge_b0_one"] = {"PASS": _betti(sc.hodge_laplacian_matrix(0).toarray()) == 1}
    # pentagon (5-cycle): b1=1 cell, b1=1 simplicial (via 3 triangles from one vertex)
    ccp = CellComplex(); ccp.add_cell([1,2,3,4,5], rank=2)
    scp = SimplicialComplex([[1,2,3],[1,3,4],[1,4,5]])
    b1c = _betti(ccp.hodge_laplacian_matrix(1).toarray())
    b1s = _betti(scp.hodge_laplacian_matrix(1).toarray())
    out["pentagon_same_b1"] = {"PASS": b1c == b1s == 0, "cell": b1c, "simp": b1s}
    return out


if __name__ == "__main__":
    name = "sim_toponetx_deep_simplicial_vs_cell_distinguishability"
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["PASS"] for v in pos.values()) and all(v["PASS"] for v in neg.values()) and all(v["PASS"] for v in bnd.values())
    results = {"name": name, "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md (cell/simplicial admission ladder)",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "ALL_PASS": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, f"{name}_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{name}: ALL_PASS={all_pass} -> {p}")
