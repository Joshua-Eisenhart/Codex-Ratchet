#!/usr/bin/env python3
"""
sim_toponetx_deep_hodge_laplacian_kernel_excludes_nontrivial

Scope note: admissibility claim -- on a contractible 2-complex (filled triangle)
the Hodge 1-Laplacian L1 has trivial kernel modulo the image of d0 (i.e.
dim ker L1 - dim ker L0 = b1 = 0), while on an annulus-shaped complex (hole)
b1 = 1. This is the homology-admissibility fence; see
system_v5/new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md (harmonic
representatives distinguish topology). Without toponetx's hodge_laplacian_matrix
emitting the oriented L_k, the admissibility probe has no operator to evaluate;
a numpy rebuild would re-derive exactly the tool under test, so toponetx is
load_bearing for the claim.

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
        "reason": "hodge_laplacian_matrix(k) emits the canonical L_k whose kernel "
                  "dimension is the admissibility witness for H_k. Removing "
                  "toponetx removes the oriented operator; claim has no referent."}
    TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"
except ImportError as e:
    print(f"BROKEN ENV: toponetx missing: {e}", file=sys.stderr); sys.exit(2)


def _betti1(sc):
    L1 = sc.hodge_laplacian_matrix(1).toarray()
    # harmonic dimension = nullity of L1
    eigs = np.linalg.eigvalsh((L1 + L1.T) / 2.0)
    return int(np.sum(np.abs(eigs) < 1e-8))


def run_positive_tests():
    out = {}
    # contractible: filled triangle
    sc_c = SimplicialComplex([[0,1,2]])
    b1_c = _betti1(sc_c)
    out["contractible_b1_zero"] = {"PASS": b1_c == 0, "b1": b1_c,
        "language": "admissible: harmonic 1-forms excluded on contractible shell"}
    # hole: boundary of triangle only (no 2-cell)
    sc_h = SimplicialComplex([[0,1],[1,2],[0,2]])
    b1_h = _betti1(sc_h)
    out["loop_b1_one"] = {"PASS": b1_h == 1, "b1": b1_h,
        "language": "admissible: exactly one harmonic class survives the hole"}
    return out


def run_negative_tests():
    out = {}
    # Negative: adding the filling cell must EXCLUDE the harmonic class
    sc = SimplicialComplex([[0,1],[1,2],[0,2]])
    b1_before = _betti1(sc)
    sc.add_simplex([0,1,2])
    b1_after = _betti1(sc)
    out["filling_excludes_harmonic"] = {
        "PASS": b1_before == 1 and b1_after == 0,
        "before": b1_before, "after": b1_after,
        "language": "excluded: filling-cell kills the candidate harmonic class"}
    # Negative 2: two disjoint loops must give b1=2 (not 1)
    sc2 = SimplicialComplex([[0,1],[1,2],[0,2],[3,4],[4,5],[3,5]])
    b1_2 = _betti1(sc2)
    out["two_loops_not_one"] = {"PASS": b1_2 == 2, "b1": b1_2,
        "language": "excluded: single-class claim fails for two disjoint cycles"}
    return out


def run_boundary_tests():
    out = {}
    # single edge: b1 = 0
    sc_e = SimplicialComplex([[0,1]])
    out["edge_b1_zero"] = {"PASS": _betti1(sc_e) == 0}
    # figure-eight (two loops sharing vertex): b1 = 2
    sc_8 = SimplicialComplex([[0,1],[1,2],[0,2],[0,3],[3,4],[0,4]])
    b = _betti1(sc_8)
    out["figure_eight_b1_two"] = {"PASS": b == 2, "b1": b}
    return out


if __name__ == "__main__":
    name = "sim_toponetx_deep_hodge_laplacian_kernel_excludes_nontrivial"
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["PASS"] for v in pos.values()) and all(v["PASS"] for v in neg.values()) and all(v["PASS"] for v in bnd.values())
    results = {"name": name, "classification": "canonical",
        "scope_note": "CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md (harmonic-form distinguishability)",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "ALL_PASS": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, f"{name}_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{name}: ALL_PASS={all_pass} -> {p}")
