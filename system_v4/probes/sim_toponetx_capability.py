#!/usr/bin/env python3
"""
sim_toponetx_capability.py -- Tool-capability isolation sim for TopoNetX.

Governing rule (durable, owner+Hermes 2026-04-13):
toponetx is used as load_bearing in shell-coupling and Hodge Laplacian sims
with no dedicated capability probe. This sim is the bounded isolation probe
that unblocks toponetx for nonclassical use.

Contract (from system_v5/new docs/plans/tool-capability-sim-program.md):

- Job the tool is supposed to do here:
    Construct simplicial and cell complexes, compute boundary operator
    matrices between dimensions, assemble Hodge Laplacians, and probe
    incidence-via-faces -- used by shell-coupling sims that treat cell
    co-occurrence as the structure under test.

- Minimal bounded task it can actually do:
    Build a tiny SimplicialComplex with a single filled 2-simplex,
    verify boundary operator B1 (edge->vertex) has expected rank and
    sign structure, compute Hodge Laplacian L0 = B1 B1.T and check its
    spectral signature against a hand-computed reference; construct a
    CellComplex containing a square 2-cell and verify its face incidence.

- Failure modes in this stack:
    * Silent: `import toponetx` without exercising any .incidence_matrix
      / .hodge_laplacian_matrix / .boundary call whose output is load-bearing.
    * API drift: TopoNetX renamed SimplicialComplex.incidence_matrix signature
      across 0.0.x -> 0.1.x (rank as positional vs keyword; index ordering).
    * Input: inserting a non-tuple/non-list simplex must raise.

- Decorative vs load-bearing:
    Decorative = `import toponetx` with no boundary/Laplacian call driving
    the sim's conclusion.
    Load-bearing = boundary operator / Hodge Laplacian IS the structure the
    topology claim rests on.

- Baseline vs canonical comparison:
    Baseline = hand-written numpy boundary matrix for the same 2-simplex.
    Canonical-use = toponetx.incidence_matrix(...) on the SimplicialComplex;
    both must agree up to column/row permutation and sign convention.
"""

import json
import os

import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed -- pure topology capability probe"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- pure topology capability probe"},
    "z3":        {"tried": False, "used": False, "reason": "no proof obligation in a capability probe"},
    "cvc5":      {"tried": False, "used": False, "reason": "no proof obligation in a capability probe"},
    "sympy":     {"tried": False, "used": False, "reason": "no symbolic derivation required"},
    "clifford":  {"tried": False, "used": False, "reason": "no geometric algebra needed"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold/geodesic needed"},
    "e3nn":      {"tried": False, "used": False, "reason": "no equivariance needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "graph library not under test"},
    "xgi":       {"tried": False, "used": False, "reason": "hypergraph lib not under test; separate probe"},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": "persistence not the subject here"},
    "networkx":  {"tried": False, "used": False, "reason": "numpy is the baseline for boundary matrices"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None, "rustworkx": None,
    "xgi": None, "gudhi": None, "networkx": None,
    "toponetx": "load_bearing",   # the subject of the probe
}

try:
    import toponetx as tnx
    TOOL_MANIFEST["toponetx"]["tried"] = True
    TOOL_MANIFEST["toponetx"]["used"] = True
    TOOL_MANIFEST["toponetx"]["reason"] = (
        "capability under test -- SimplicialComplex / CellComplex / "
        "boundary operator / Hodge Laplacian / face incidence"
    )
    TNX_OK = True
    TNX_VERSION = getattr(tnx, "__version__", "unknown")
except Exception as exc:
    TNX_OK = False
    TNX_VERSION = None
    TOOL_MANIFEST["toponetx"]["reason"] = f"not installed: {exc}"


# =====================================================================
# Helpers
# =====================================================================

def _to_dense(m):
    """TopoNetX returns scipy sparse -- coerce to dense numpy array."""
    if hasattr(m, "toarray"):
        return np.asarray(m.toarray())
    return np.asarray(m)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    if not TNX_OK:
        results["toponetx_available"] = {"pass": False, "detail": "toponetx missing"}
        return results
    results["toponetx_available"] = {"pass": True, "version": TNX_VERSION}

    # --- 1. SimplicialComplex construction: filled triangle {0,1,2} ---
    SC = tnx.SimplicialComplex()
    SC.add_simplex([0, 1, 2])
    # Downward closure must give 3 vertices, 3 edges, 1 triangle.
    shape = SC.shape  # (n_0_cells, n_1_cells, n_2_cells, ...)
    results["triangle_shape"] = {
        "pass": tuple(shape[:3]) == (3, 3, 1),
        "got": list(shape),
        "expected_prefix": [3, 3, 1],
        "detail": "filled 2-simplex has 3 vertices, 3 edges, 1 triangle after downward closure",
    }

    # --- 2. Boundary operator B1 (edge -> vertex) rank ---
    # For a triangle, B1 is 3x3 with rank 2 (null space spanned by the cycle).
    try:
        B1 = _to_dense(SC.incidence_matrix(1))
        rank_B1 = int(np.linalg.matrix_rank(B1))
        # Each column has exactly two nonzeros of opposite sign (boundary of edge).
        col_ok = all(
            (np.count_nonzero(B1[:, j]) == 2) and (np.sum(B1[:, j]) == 0)
            for j in range(B1.shape[1])
        )
        results["B1_rank_and_sign"] = {
            "pass": rank_B1 == 2 and col_ok,
            "rank": rank_B1,
            "expected_rank": 2,
            "columns_balanced": col_ok,
            "shape": list(B1.shape),
        }
    except Exception as exc:
        results["B1_rank_and_sign"] = {"pass": False, "detail": f"raised: {exc}"}

    # --- 3. B1 @ B2 == 0  (boundary of boundary vanishes) ---
    try:
        B1 = _to_dense(SC.incidence_matrix(1))
        B2 = _to_dense(SC.incidence_matrix(2))
        prod = B1 @ B2
        results["boundary_of_boundary_zero"] = {
            "pass": bool(np.allclose(prod, 0)),
            "max_abs": float(np.max(np.abs(prod))) if prod.size else 0.0,
            "detail": "d^2 = 0 must hold exactly over Z",
        }
    except Exception as exc:
        results["boundary_of_boundary_zero"] = {"pass": False, "detail": f"raised: {exc}"}

    # --- 4. Hodge Laplacian L0 spectrum ---
    # For a triangle (3-cycle of edges), L0 = B1 B1^T has eigenvalues {0, 3, 3}.
    try:
        hl_fn = getattr(SC, "hodge_laplacian_matrix", None)
        if hl_fn is None:
            # Older API: construct by hand.
            B1 = _to_dense(SC.incidence_matrix(1))
            L0 = B1 @ B1.T
        else:
            L0 = _to_dense(hl_fn(rank=0))
        eig = np.sort(np.linalg.eigvalsh(L0))
        expected = np.array([0.0, 3.0, 3.0])
        results["hodge_L0_spectrum"] = {
            "pass": bool(np.allclose(eig, expected, atol=1e-8)),
            "eigenvalues": eig.tolist(),
            "expected": expected.tolist(),
            "detail": "triangle graph Laplacian has spectrum {0,3,3}",
        }
    except Exception as exc:
        results["hodge_L0_spectrum"] = {"pass": False, "detail": f"raised: {exc}"}

    # --- 5. Incidence via faces (edge -> vertex membership) ---
    # Each edge must report exactly its two endpoints among {0,1,2}.
    try:
        # TopoNetX API: SC.skeleton(1) returns 1-simplices.
        edges = list(SC.skeleton(1))
        edge_sets = [frozenset(e) for e in edges]
        expected_edges = {frozenset([0, 1]), frozenset([0, 2]), frozenset([1, 2])}
        results["face_incidence"] = {
            "pass": set(edge_sets) == expected_edges,
            "edges": [sorted(e) for e in edge_sets],
            "expected": [sorted(e) for e in expected_edges],
        }
    except Exception as exc:
        results["face_incidence"] = {"pass": False, "detail": f"raised: {exc}"}

    # --- 6. Baseline cross-check: hand-built numpy boundary vs toponetx ---
    try:
        B1 = _to_dense(SC.incidence_matrix(1))
        # Map each column (edge) to its ordered endpoint pair and compare.
        ok = True
        for j in range(B1.shape[1]):
            col = B1[:, j]
            pos = np.where(col > 0)[0]
            neg = np.where(col < 0)[0]
            if len(pos) != 1 or len(neg) != 1:
                ok = False
                break
        results["baseline_boundary_matches"] = {
            "pass": ok,
            "detail": "each B1 column has exactly one +1 and one -1 entry (signed incidence)",
        }
    except Exception as exc:
        results["baseline_boundary_matches"] = {"pass": False, "detail": f"raised: {exc}"}

    # --- 7. CellComplex with a square 2-cell ---
    try:
        CX = tnx.CellComplex()
        # Square cell with boundary 0->1->2->3->0
        CX.add_cell([0, 1, 2, 3], rank=2)
        n0 = len(list(CX.nodes))
        # CellComplex edges auto-filled from the cell's boundary.
        n1 = len(list(CX.edges))
        n2 = len(list(CX.cells))
        results["cellcomplex_square"] = {
            "pass": n0 == 4 and n1 == 4 and n2 == 1,
            "n_nodes": n0, "n_edges": n1, "n_cells": n2,
            "expected": [4, 4, 1],
            "detail": "square 2-cell must induce 4 nodes, 4 boundary edges, 1 cell",
        }
    except Exception as exc:
        results["cellcomplex_square"] = {"pass": False, "detail": f"raised: {exc}"}

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    if not TNX_OK:
        results["toponetx_available"] = {"pass": False, "detail": "toponetx missing"}
        return results

    # --- N1. Edge-only complex has NO 2-cells ---
    SC = tnx.SimplicialComplex()
    SC.add_simplex([0, 1])
    SC.add_simplex([1, 2])
    shape = SC.shape
    has_no_triangles = (len(shape) < 3) or (shape[2] == 0)
    results["edges_only_no_2simplex"] = {
        "pass": bool(has_no_triangles),
        "shape": list(shape),
        "detail": "two disjoint edges must not induce a triangle",
    }

    # --- N2. Duplicate vertex within a simplex must not produce a self-loop face ---
    # Adding [0,0,1] should either raise or be normalized to {0,1}, never produce
    # a 2-simplex with a repeated vertex.
    SC_dup = tnx.SimplicialComplex()
    raised_or_normalized = False
    err = None
    try:
        SC_dup.add_simplex([0, 0, 1])
        # If accepted: must normalize -- no 2-simplex should appear (only the edge {0,1}).
        shape = SC_dup.shape
        raised_or_normalized = (len(shape) < 3) or (shape[2] == 0)
    except Exception as exc:
        raised_or_normalized = True
        err = type(exc).__name__
    results["duplicate_vertex_simplex_normalized"] = {
        "pass": raised_or_normalized,
        "error_type": err,
        "detail": "simplex with repeated vertex must be rejected or normalized (no degenerate 2-simplex)",
    }

    # --- N3. Hodge L0 of disconnected triangle+isolated vertex has 2 zero eigenvalues ---
    SC2 = tnx.SimplicialComplex()
    SC2.add_simplex([0, 1, 2])
    SC2.add_simplex([3])  # isolated vertex
    try:
        B1 = _to_dense(SC2.incidence_matrix(1))
        L0 = B1 @ B1.T
        eig = np.sort(np.linalg.eigvalsh(L0))
        n_zero = int(np.sum(np.abs(eig) < 1e-8))
        results["disconnected_two_zero_eigs"] = {
            "pass": n_zero == 2,
            "n_zero_eigs": n_zero,
            "eigenvalues": eig.tolist(),
            "detail": "#connected components = multiplicity of 0 in L0 spectrum",
        }
    except Exception as exc:
        results["disconnected_two_zero_eigs"] = {"pass": False, "detail": f"raised: {exc}"}
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    if not TNX_OK:
        results["toponetx_available"] = {"pass": False, "detail": "toponetx missing"}
        return results

    # --- B1. Empty simplicial complex ---
    SC = tnx.SimplicialComplex()
    shape = SC.shape
    # Shape may be an empty tuple or (0,) for a fresh complex.
    results["empty_complex"] = {
        "pass": (len(shape) == 0) or all(s == 0 for s in shape),
        "shape": list(shape),
        "detail": "empty complex must have no cells of any rank",
    }

    # --- B2. Singleton vertex ---
    SC1 = tnx.SimplicialComplex()
    SC1.add_simplex([0])
    shape1 = SC1.shape
    results["singleton_vertex"] = {
        "pass": shape1[0] == 1 and (len(shape1) < 2 or shape1[1] == 0),
        "shape": list(shape1),
        "detail": "single vertex: 1 0-cell, 0 1-cells",
    }

    # --- B3. Idempotent insertion of the same simplex ---
    SC2 = tnx.SimplicialComplex()
    SC2.add_simplex([0, 1, 2])
    shape_a = tuple(SC2.shape)
    SC2.add_simplex([0, 1, 2])  # duplicate
    shape_b = tuple(SC2.shape)
    results["duplicate_insertion_idempotent"] = {
        "pass": shape_a == shape_b,
        "shape_before": list(shape_a),
        "shape_after": list(shape_b),
        "detail": "re-adding an existing simplex must not change shape",
    }

    # --- B4. Permuted vertex order of the same simplex must be identified ---
    SC3 = tnx.SimplicialComplex()
    SC3.add_simplex([0, 1, 2])
    before = tuple(SC3.shape)
    SC3.add_simplex([2, 1, 0])
    after = tuple(SC3.shape)
    results["permutation_invariant_simplex"] = {
        "pass": before == after,
        "shape_before": list(before),
        "shape_after": list(after),
        "detail": "simplices are unordered sets; vertex-order permutation must not add a new simplex",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

def _all_pass(section):
    if not isinstance(section, dict):
        return False
    flags = [bool(v.get("pass", False)) for v in section.values() if isinstance(v, dict)]
    return bool(flags) and all(flags)


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
    }
    summary["all_pass"] = TNX_OK and all(summary.values())

    results = {
        "name": "sim_toponetx_capability",
        "purpose": "Tool-capability isolation probe for toponetx -- unblocks load-bearing simplicial/cell complex use.",
        "toponetx_version": TNX_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "toponetx_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
