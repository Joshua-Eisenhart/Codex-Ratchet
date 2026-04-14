#!/usr/bin/env python3
"""
sim_toponetx_gudhi_joint_same_complex_parity

Scope note: admissibility claim (joint/compound) -- a simplicial complex built
identically in toponetx (as SimplicialComplex) and gudhi (as SimplexTree) must
yield the same Betti numbers. If either tool reports different b_k from the
other, the whole homology-admissibility ladder loses a degree of freedom and
no single-tool claim is trustworthy (parity fence, see
LADDERS_FENCES_ADMISSION_REFERENCE.md). Both tools are load_bearing: removing
either one dissolves the parity claim itself.

Classification: canonical.
"""
import json, os, sys
import numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from toponetx.classes import SimplicialComplex
    TOOL_MANIFEST["toponetx"] = {"tried": True, "used": True,
        "reason": "Provides the Hodge-Laplacian nullity witness for b_k. "
                  "Parity claim is meaningless without its b_k value."}
    TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"
except ImportError as e:
    print(f"BROKEN ENV: toponetx missing: {e}", file=sys.stderr); sys.exit(2)
try:
    import gudhi
    TOOL_MANIFEST["gudhi"] = {"tried": True, "used": True,
        "reason": "Provides the Betti-number witness via persistent_betti_numbers. "
                  "Parity claim needs its independent b_k value."}
    TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"
except ImportError as e:
    print(f"BROKEN ENV: gudhi missing: {e}", file=sys.stderr); sys.exit(2)


def _betti_tnx(simplices, k):
    sc = SimplicialComplex(simplices)
    if sc.dim < k + 1 and k > 0:
        # hodge requires rank+1 to exist; otherwise nullity = dim of C_k - rank B_k
        pass
    L = sc.hodge_laplacian_matrix(k).toarray()
    L = (L + L.T) / 2.0
    return int(np.sum(np.abs(np.linalg.eigvalsh(L)) < 1e-8))


def _betti_gudhi(simplices, k):
    st = gudhi.SimplexTree()
    for s in simplices:
        st.insert(list(s), filtration=0.0)
    # gudhi only tracks H_k up to its internal dimension; bump so k is resolvable
    st.set_dimension(max(st.dimension(), k + 1))
    st.compute_persistence()
    # Count infinite-death intervals in dimension k (these are the true Betti classes
    # for an unfiltered complex). betti_numbers() can omit them if max dim is low.
    ivs = st.persistence_intervals_in_dimension(k)
    import math
    return int(sum(1 for b, d in ivs if math.isinf(d) or d > b + 1e-12))


def _pair(simplices, k_list):
    return [(_betti_tnx(simplices, k), _betti_gudhi(simplices, k)) for k in k_list]


def run_positive_tests():
    out = {}
    # filled triangle: b0=1, b1=0
    tri = [[0,1,2]]
    pairs = _pair(tri, [0, 1])
    out["filled_triangle_parity"] = {
        "PASS": all(a == b for a, b in pairs), "pairs_tnx_gudhi": pairs,
        "language": "admissible: tools parity-agree on b_0,b_1"}
    # hollow triangle: b0=1, b1=1
    hollow = [[0,1],[1,2],[0,2]]
    pairs2 = _pair(hollow, [0, 1])
    out["hollow_triangle_parity"] = {
        "PASS": all(a == b for a, b in pairs2), "pairs_tnx_gudhi": pairs2}
    # tetrahedron boundary: b0=1, b1=0, b2=1
    sphere = [[0,1,2],[0,1,3],[0,2,3],[1,2,3]]
    pairs3 = _pair(sphere, [0, 1, 2])
    out["sphere_parity"] = {
        "PASS": all(a == b for a, b in pairs3), "pairs_tnx_gudhi": pairs3}
    return out


def run_negative_tests():
    out = {}
    # Negative: construct deliberately INEQUIVALENT inputs (extra edge in gudhi)
    # and confirm parity is violated -> parity probe actually discriminates.
    base = [[0,1],[1,2],[0,2]]
    sc = SimplicialComplex(base)
    b1_tnx = _betti_tnx(base, 1)
    st = gudhi.SimplexTree()
    for s in base:
        st.insert(list(s), filtration=0.0)
    st.insert([0,1,2], filtration=0.0)   # fill only in gudhi
    st.compute_persistence()
    import math
    ivs = st.persistence_intervals_in_dimension(1)
    b1_g = int(sum(1 for b, d in ivs if math.isinf(d) or d > b + 1e-12))
    out["intentional_mismatch_detected"] = {
        "PASS": b1_tnx != b1_g, "tnx_b1": b1_tnx, "gudhi_b1": b1_g,
        "language": "excluded: parity probe flags input divergence"}
    # Negative 2: two disjoint filled triangles -> b0=2, parity must hold
    two = [[0,1,2],[3,4,5]]
    pairs = _pair(two, [0, 1])
    out["two_components_parity_holds"] = {
        "PASS": pairs[0] == (2, 2) and pairs[1] == (0, 0), "pairs": pairs}
    return out


def run_boundary_tests():
    out = {}
    # single edge: b0=1, b1=0
    edge = [[0, 1]]
    pairs = _pair(edge, [0, 1])
    out["edge_parity"] = {"PASS": pairs == [(1, 1), (0, 0)], "pairs": pairs}
    # square-with-diagonal (two triangles): b0=1, b1=0
    sq = [[0,1,2],[0,2,3]]
    pairs = _pair(sq, [0, 1])
    out["square_parity"] = {"PASS": all(a == b for a, b in pairs), "pairs": pairs}
    return out


if __name__ == "__main__":
    name = "sim_toponetx_gudhi_joint_same_complex_parity"
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["PASS"] for v in pos.values()) and all(v["PASS"] for v in neg.values()) and all(v["PASS"] for v in bnd.values())
    results = {"name": name, "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md (parity fence between topology tools)",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "ALL_PASS": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, f"{name}_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{name}: ALL_PASS={all_pass} -> {p}")
