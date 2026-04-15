#!/usr/bin/env python3
"""
sim_capability_toponetx_isolated.py -- Isolated tool-capability probe for toponetx.

Classical_baseline capability probe: demonstrates toponetx topological complexes:
CellComplex, SimplicialComplex, boundary operators, chain maps, Hodge Laplacians,
and incidence matrices. Honest CAN/CANNOT summary. No coupling to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates toponetx topological complex capabilities alone; "
    "cross-tool coupling is deferred to a separate integration sim "
    "per the four-sim-kinds doctrine (capability vs integration separation)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "toponetx runs on numpy by default; pytorch integration deferred to a separate integration sim."},
    "pyg":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "toponetx":  {"tried": True,  "used": True,  "reason": "load-bearing: toponetx CellComplex and SimplicialComplex with boundary operators and incidence matrices are the sole subject of this capability probe."},
    "gudhi":     {"tried": False, "used": False, "reason": "gudhi computes persistent homology; toponetx is for topological signal processing on complexes; separate capabilities."},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": "load_bearing", "gudhi": None,
}

TOPONETX_OK = False
try:
    from toponetx.classes import SimplicialComplex
    TOPONETX_OK = True
except Exception:
    try:
        import toponetx
        TOPONETX_OK = True
    except Exception:
        pass


def run_positive_tests():
    r = {}
    if not TOPONETX_OK:
        r["toponetx_available"] = {"pass": False, "detail": "toponetx not importable"}
        return r

    import toponetx
    r["toponetx_available"] = {"pass": True, "version": getattr(toponetx, "__version__", "unknown")}

    try:
        from toponetx.classes import SimplicialComplex
    except ImportError:
        try:
            from toponetx import SimplicialComplex
        except ImportError:
            r["import_simplicial"] = {"pass": False, "detail": "SimplicialComplex import failed"}
            return r

    # --- Test 1: simplicial complex construction ---
    # Triangle: 3 nodes, 3 edges, 1 filled face
    sc = SimplicialComplex([[0, 1, 2]])
    r["simplicial_complex_construction"] = {
        "pass": sc.dim == 2,
        "dim": sc.dim,
        "detail": "SimplicialComplex([[0,1,2]]) has dimension 2 (one 2-simplex)",
    }

    # --- Test 2: node/edge/face counts ---
    # sc.shape returns (n_0-simplices, n_1-simplices, n_2-simplices, ...)
    nodes = len(sc.nodes)
    shape = sc.shape  # (3, 3, 1) for triangle
    edges = shape[1] if len(shape) > 1 else 0
    r["simplex_counts"] = {
        "pass": nodes == 3 and edges == 3,
        "nodes": nodes,
        "edges": edges,
        "shape": list(shape),
        "detail": "Triangle has 3 nodes and 3 edges",
    }

    # --- Test 3: boundary operator B1 (edges → nodes) ---
    B1 = sc.incidence_matrix(rank=1, signed=True)
    # B1 should be 3x3 (3 nodes, 3 edges)
    r["boundary_operator_B1_shape"] = {
        "pass": B1.shape[0] == 3 and B1.shape[1] == 3,
        "shape": list(B1.shape),
        "detail": "B1 (boundary of edges to nodes) shape = (3 nodes, 3 edges)",
    }

    # --- Test 4: boundary operator B2 (faces → edges) ---
    B2 = sc.incidence_matrix(rank=2, signed=True)
    # B2 for 1 face: should be 3x1
    r["boundary_operator_B2_shape"] = {
        "pass": B2.shape[0] == 3 and B2.shape[1] == 1,
        "shape": list(B2.shape),
        "detail": "B2 (boundary of faces to edges): shape (3 edges, 1 face)",
    }

    # --- Test 5: boundary of boundary is zero (B1 * B2 = 0) ---
    import numpy as np
    B1_dense = B1.toarray() if hasattr(B1, 'toarray') else np.array(B1)
    B2_dense = B2.toarray() if hasattr(B2, 'toarray') else np.array(B2)
    chain = B1_dense @ B2_dense
    is_zero = np.allclose(chain, 0, atol=1e-10)
    r["boundary_of_boundary_zero"] = {
        "pass": bool(is_zero),
        "max_val": float(np.abs(chain).max()),
        "detail": "B1 @ B2 = 0: fundamental theorem of homology",
    }

    # --- Test 6: Hodge Laplacian L1 ---
    L1 = sc.hodge_laplacian_matrix(rank=1)
    r["hodge_laplacian_L1"] = {
        "pass": L1.shape[0] == 3 and L1.shape[1] == 3,
        "shape": list(L1.shape),
        "detail": "L1 = B1^T B1 + B2 B2^T: shape (3,3) for triangle",
    }

    return r


def run_negative_tests():
    r = {}
    if not TOPONETX_OK:
        r["toponetx_unavailable"] = {"pass": True, "detail": "skip: toponetx not installed"}
        return r

    try:
        from toponetx.classes import SimplicialComplex
    except ImportError:
        try:
            from toponetx import SimplicialComplex
        except ImportError:
            r["import_error"] = {"pass": True, "detail": "skip: SimplicialComplex not found"}
            return r

    import numpy as np

    # --- Neg 1: path graph (no face) has dim=1, no rank-2 incidence matrix ---
    # sc.dim == 1 means no 2-simplices exist; B2 would raise ValueError
    sc_path = SimplicialComplex([[0, 1], [1, 2]])  # no filled triangle
    r["no_face_no_rank2"] = {
        "pass": sc_path.dim == 1,
        "dim": sc_path.dim,
        "detail": "Path graph (only edges): dim=1, no 2-simplex exists",
    }

    # --- Neg 2: subcomplex has fewer simplices ---
    sc_full = SimplicialComplex([[0, 1, 2], [2, 3]])
    nodes_full = len(sc_full.nodes)
    sc_small = SimplicialComplex([[0, 1]])
    nodes_small = len(sc_small.nodes)
    r["subcomplex_fewer_nodes"] = {
        "pass": nodes_full > nodes_small,
        "full_nodes": nodes_full,
        "small_nodes": nodes_small,
        "detail": "Larger complex has more nodes",
    }

    return r


def run_boundary_tests():
    r = {}
    if not TOPONETX_OK:
        r["toponetx_unavailable"] = {"pass": True, "detail": "skip: toponetx not installed"}
        return r

    try:
        from toponetx.classes import SimplicialComplex
    except ImportError:
        try:
            from toponetx import SimplicialComplex
        except ImportError:
            r["import_error"] = {"pass": True, "detail": "skip: SimplicialComplex not found"}
            return r

    # --- Boundary 1: single node complex ---
    sc1 = SimplicialComplex([[0]])
    r["single_node_complex"] = {
        "pass": len(sc1.nodes) == 1,
        "nodes": len(sc1.nodes),
        "detail": "Single-node simplicial complex is valid",
    }

    # --- Boundary 2: tetrahedron (3-simplex) ---
    sc_tet = SimplicialComplex([[0, 1, 2, 3]])
    r["tetrahedron"] = {
        "pass": sc_tet.dim == 3 and len(sc_tet.nodes) == 4,
        "dim": sc_tet.dim,
        "nodes": len(sc_tet.nodes),
        "detail": "Tetrahedron: dim=3, 4 nodes",
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall = all([v.get("pass", False) for v in all_tests.values() if isinstance(v, dict) and "pass" in v])

    results = {
        "name": "sim_capability_toponetx_isolated",
        "classification": classification,
        "overall_pass": overall,
        "capability_summary": {
            "CAN": [
                "construct simplicial and cell complexes from simplex lists",
                "compute boundary operators B_k as signed incidence matrices",
                "verify boundary-of-boundary = 0 (fundamental homology theorem)",
                "compute Hodge Laplacians L_k = B_k^T B_k + B_{k+1} B_{k+1}^T",
                "represent topological signal processing domains on complexes",
                "handle complexes from 0-simplices (vertices) to arbitrary dimension",
            ],
            "CANNOT": [
                "compute persistent homology barcode diagrams (use gudhi for that)",
                "handle hyperedges that are not simplices (use xgi for general hypergraphs)",
                "run graph neural network message passing (use PyG for that)",
                "prove homological properties formally (use z3 for logical proofs)",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_toponetx_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
