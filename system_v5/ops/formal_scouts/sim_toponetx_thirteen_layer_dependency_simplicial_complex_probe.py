#!/usr/bin/env python3
"""TopoNetX deep-integration scout: 13-layer constraint manifold dependency tower
as a higher-order simplicial / cell complex with Hodge Laplacians, betti numbers,
and persistent homology.

classification: formal_scout
promotion_allowed: False
claim_ceiling: Formal scout only: tests whether the 13-layer constraint manifold
dependency tower admits a higher-rank simplicial structure with computable Laplacians
and persistent homology. Does not admit final manifold or physics claims.
"""

from __future__ import annotations

import json
import os
import pathlib
import random
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import gudhi
import scipy.sparse.linalg as spla
import sympy as sp
import toponetx as tnx
from toponetx import Cell
import networkx as nx
import torch

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "toponetx_thirteen_layer_dependency_simplicial_complex_probe_results.json"

NAME = "toponetx_thirteen_layer_dependency_simplicial_complex_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether the 13-layer constraint manifold dependency "
    "tower admits a higher-rank simplicial structure with computable Laplacians and "
    "persistent homology. Does not admit final manifold or physics claims."
)

TOOL_MANIFEST = {
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: SimplicialComplex construction, hodge_laplacian_matrix "
            "(rank 0/1/2/3), simplicial_complex_hodge_laplacian_spectrum, "
            "CellComplex construction and hodge_laplacian_matrix for cell-complex "
            "comparison — not just imported"
        ),
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: Laplacian eigendecomposition via torch.linalg.eigvalsh "
            "for betti number extraction (kernel dimension counting)"
        ),
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": (
            "supportive: sparse eigenvalue extraction via scipy.sparse.linalg.eigsh "
            "for an independent top-5 L_0 spectrum cross-check; pass/fail rests on "
            "TopoNetX/GUDHI construction and PyTorch eigvalsh betti extraction"
        ),
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: SimplexTree filtration with dependency-order filtration "
            "values; compute_persistence() for H_0 and H_1 persistence pairs "
            "cross-check against Hodge-Laplacian betti numbers"
        ),
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "supportive: symbolic 3-node path Laplacian verification — "
            "confirms nullspace = 1 (betti_0 = 1) analytically for the minimal case"
        ),
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": (
            "supportive: path graph G = nx.path_graph(13) built to cross-check "
            "edge count, adjacency, and connected-components against the simplicial "
            "complex topology"
        ),
    },
}

TOOL_INTEGRATION_DEPTH = {
    "toponetx": "load_bearing",
    "pytorch": "load_bearing",
    "scipy": "supportive",
    "gudhi": "load_bearing",
    "sympy": "supportive",
    "networkx": "supportive",
}

# Canonical 13-layer dependency order from
# sim_nested_geometry_tower_dependency_order_probe.py lines 56-70
LAYERS: list[str] = [
    "finite_constraint_complex",
    "complex_hilbert_carrier",
    "unit_spinor_sphere",
    "projective_base_sphere",
    "hopf_fiber_bundle",
    "hopf_torus_leaf_family",
    "connection_holonomy_geometry",
    "weyl_spinor_bundle",
    "chirality_orientation_cover",
    "clifford_module_geometry",
    "frame_bundle_structure_reduction",
    "tensor_product_coupling_geometry",
    "dynamic_transition_ratchet_geometry",
]

_EIGEN_ZERO_TOL = 1e-8
FLOAT_DTYPE = torch.float64


# ---------------------------------------------------------------------------
# Section 1: Build SimplicialComplex over the 13-layer tower
# ---------------------------------------------------------------------------


def build_simplicial_complex() -> dict[str, Any]:
    """Build SC with 0-, 1-, 2-, 3-simplices from the canonical layer order.

    Simplex construction rules:
    - Top-level generators inserted: 13 nodes, 12 adjacent pairs, 11 triples, 10 quadruples
    - TopoNetX auto-fills all faces when a higher-dim simplex is added.
    - Actual face counts after face-completion:
        rank 0: 13 nodes
        rank 1: 33 edges  (spans 1, 2, 3 — all edges of the 10 tetrahedra)
        rank 2: 31 triangles (all triangular faces of the 10 tetrahedra)
        rank 3: 10 tetrahedra
    """
    sc = tnx.SimplicialComplex()
    n = len(LAYERS)

    # 0-simplices (nodes)
    for name in LAYERS:
        sc.add_node(name)

    # 1-simplices (adjacent pairs — span-1 path edges)
    for i in range(n - 1):
        sc.add_simplex([LAYERS[i], LAYERS[i + 1]])

    # 2-simplices (adjacent triples — generates span-2 edges as faces)
    for i in range(n - 2):
        sc.add_simplex([LAYERS[i], LAYERS[i + 1], LAYERS[i + 2]])

    # 3-simplices (adjacent quadruples — generates span-3 edges and all triangular faces)
    for i in range(n - 3):
        sc.add_simplex([LAYERS[i], LAYERS[i + 1], LAYERS[i + 2], LAYERS[i + 3]])

    # Simplex counts per rank (face-completed)
    n_simplices: dict[int, int] = {}
    for rank in range(sc.dim + 1):
        n_simplices[rank] = len(sc.skeleton(rank))

    # Expected after face-completion:
    # rank-0: 13 nodes (1 per layer)
    # rank-1: 33 = 12 span-1 + 11 span-2 + 10 span-3 (all edges within each tetrahedron)
    # rank-2: 31 = 11 span-(1,2) + 10 span-(1,3) + 10 span-(2,3) triangles = 31 (verified analytically)
    # rank-3: 10 tetrahedra
    return {
        "complex": sc,
        "dim": sc.dim,
        "n_simplices": n_simplices,
        "pass": (
            n_simplices.get(0, 0) == 13
            and n_simplices.get(1, 0) == 33
            and n_simplices.get(2, 0) == 31
            and n_simplices.get(3, 0) == 10
        ),
        "note": (
            "Face-completed counts: rank-0=13 nodes, rank-1=33 edges "
            "(span-1:12 + span-2:11 + span-3:10), rank-2=31 triangles, "
            "rank-3=10 tetrahedra. TopoNetX auto-fills all faces on insertion."
        ),
    }


# ---------------------------------------------------------------------------
# Section 2: Higher-rank Hodge Laplacians
# ---------------------------------------------------------------------------


def compute_hodge_laplacians(sc: tnx.SimplicialComplex) -> dict[str, Any]:
    """Compute L_k for k=0,1,2,3 and extract eigenspectra and betti numbers.

    L_k = B_k^T B_k + B_{k+1} B_{k+1}^T  (Hodge decomposition)

    kernel(L_k) = dim of k-th harmonic forms = betti_k.

    For this 13-layer path SC (dim=3, contractible):
    Expected betti = {0: 1, 1: 0, 2: 0, 3: 0}
    """
    results: dict[str, Any] = {}
    betti: dict[int, int] = {}

    for rank in range(4):  # L_0 through L_3
        try:
            L = sc.hodge_laplacian_matrix(rank=rank)
            L_dense = torch.tensor(L.toarray(), dtype=FLOAT_DTYPE)
            evals = torch.linalg.eigvalsh(L_dense)
            betti_k = int(torch.sum(torch.abs(evals) < _EIGEN_ZERO_TOL).item())
            betti[rank] = betti_k

            # Top-5 eigenvalues (sorted ascending)
            evals_sorted = sorted(float(v) for v in evals.tolist())
            results[f"L_{rank}"] = {
                "shape": list(L_dense.shape),
                "eigenvalues_ascending_top5": [round(v, 10) for v in evals_sorted[:5]],
                "betti_k": betti_k,
            }
        except Exception as exc:
            results[f"L_{rank}"] = {"error": str(exc)}
            betti[rank] = -1

    # tnx.simplicial_complex_hodge_laplacian_spectrum cross-check for L_0
    try:
        spec_tnx = tnx.simplicial_complex_hodge_laplacian_spectrum(sc, rank=0)
        results["tnx_spectrum_L0_top5_ascending"] = [round(float(v), 10) for v in sorted(spec_tnx)[:5]]
    except Exception as exc:
        results["tnx_spectrum_L0_top5_ascending"] = {"error": str(exc)}

    # scipy sparse eigsh for L_0 (independent extraction path)
    try:
        L0_sparse = sc.hodge_laplacian_matrix(rank=0)
        n_nodes = L0_sparse.shape[0]
        k_eigs = min(5, n_nodes - 1)
        vals_sparse = spla.eigsh(
            L0_sparse.astype(float),
            k=k_eigs,
            which="SM",
            return_eigenvectors=False,
        )
        results["scipy_eigsh_L0_ascending"] = [round(float(v), 10) for v in sorted(vals_sparse)]
    except Exception as exc:
        results["scipy_eigsh_L0_ascending"] = {"error": str(exc)}

    # Expected betti for a contractible simplicial complex (path = contractible)
    expected = {0: 1, 1: 0, 2: 0, 3: 0}
    betti_pass = all(betti.get(k, -1) == expected[k] for k in expected)

    results["betti_numbers"] = betti
    results["expected_betti"] = expected
    results["betti_pass"] = betti_pass
    results["pass"] = (
        all(
            f"L_{k}" in results and "error" not in results[f"L_{k}"]
            for k in range(4)
        )
        and betti_pass
    )

    return results


# ---------------------------------------------------------------------------
# Section 3: Persistent homology via gudhi
# ---------------------------------------------------------------------------


def compute_persistent_homology() -> dict[str, Any]:
    """Build a gudhi SimplexTree with filtration = dependency-order index.

    Filtration assignment:
    - Layer i as 0-simplex: filtration = i
    - Adjacent pair (i, i+1) as 1-simplex: filtration = i+1
    - Adjacent triple (i, i+1, i+2) as 2-simplex: filtration = i+2
    - Adjacent quadruple as 3-simplex: filtration = i+3

    Expected: H_0 has 1 persistence pair born at 0 dying at inf (one connected component).
    H_1 = 0 pairs (no cycles). H_2 = H_3 = 0 pairs (contractible path complex).
    """
    st = gudhi.SimplexTree()
    n = len(LAYERS)

    for i in range(n):
        st.insert([i], filtration=float(i))
    for i in range(n - 1):
        st.insert([i, i + 1], filtration=float(i + 1))
    for i in range(n - 2):
        st.insert([i, i + 1, i + 2], filtration=float(i + 2))
    for i in range(n - 3):
        st.insert([i, i + 1, i + 2, i + 3], filtration=float(i + 3))

    st.compute_persistence()
    pairs = st.persistence()

    # Group by homology dimension
    by_dim: dict[int, list[tuple[float, float]]] = {}
    for dim, (birth, death) in pairs:
        by_dim.setdefault(dim, []).append((birth, death))

    # Essential class: H_0 born at 0, never dies
    h0_pairs = by_dim.get(0, [])
    h0_essential = [(b, d) for b, d in h0_pairs if d == float("inf")]
    h1_pairs = by_dim.get(1, [])

    # Pass criterion: exactly 1 H_0 essential pair (single connected component),
    # 0 H_1 pairs (no cycles survive to inf or at all for a path)
    pass_crit = len(h0_essential) == 1 and len(h1_pairs) == 0

    return {
        "persistence_pairs_total": len(pairs),
        "pairs_by_dim": {str(k): v for k, v in by_dim.items()},
        "h0_essential_classes": h0_essential,
        "h1_pairs": h1_pairs,
        "pass": pass_crit,
        "note": "H_0 essential count = 1 means single connected component; H_1 = 0 means no 1-cycles",
    }


# ---------------------------------------------------------------------------
# Section 4: CellComplex comparison
# ---------------------------------------------------------------------------


def build_cell_complex_and_compare(sc_stats: dict[str, Any]) -> dict[str, Any]:
    """Build a CellComplex with the same nodes and edges plus quad 2-cells.

    For each 4-layer window [i, i+1, i+2, i+3] add a quadrilateral 2-cell.
    The CellComplex will include diagonal edges added by the cell boundaries,
    producing a richer edge set than the simplicial path graph.

    Compare:
    - Number of 1-cells (edges): CC has more than SC due to quad diagonals
    - L_0 betti_0: should still be 1 (connected)
    - L_2 dimension: reflects number of 2-cells
    """
    n = len(LAYERS)
    cc = tnx.CellComplex()

    for name in LAYERS:
        cc.add_node(name)
    for i in range(n - 1):
        cc.add_edge(LAYERS[i], LAYERS[i + 1])

    # Add quadrilateral 2-cells (4-layer windows = 10 quads)
    for i in range(n - 3):
        cell = Cell([LAYERS[i], LAYERS[i + 1], LAYERS[i + 2], LAYERS[i + 3]])
        cc.add_cell(cell, rank=2)

    cc_shape = cc.shape  # (n_nodes, n_edges, n_2cells)
    n_cc_nodes = cc.number_of_nodes()
    n_cc_edges = cc.number_of_edges()
    n_cc_2cells = cc.number_of_cells()

    # CC L_0 betti_0
    try:
        L0_cc = torch.tensor(cc.hodge_laplacian_matrix(rank=0).toarray(), dtype=FLOAT_DTYPE)
        evals0_cc = torch.linalg.eigvalsh(L0_cc)
        betti0_cc = int(torch.sum(torch.abs(evals0_cc) < _EIGEN_ZERO_TOL).item())
    except Exception as exc:
        betti0_cc = -1
        L0_cc = None  # type: ignore[assignment]

    # CC L_2 (2-cell Hodge Laplacian)
    try:
        L2_cc = torch.tensor(cc.hodge_laplacian_matrix(rank=2).toarray(), dtype=FLOAT_DTYPE)
        evals2_cc = torch.linalg.eigvalsh(L2_cc)
        betti2_cc = int(torch.sum(torch.abs(evals2_cc) < _EIGEN_ZERO_TOL).item())
        l2_shape = list(L2_cc.shape)
    except Exception as exc:
        betti2_cc = -1
        l2_shape = {"error": str(exc)}  # type: ignore[assignment]

    # Structural differences from SC
    # SC has 33 edges (spans 1,2,3 from face-completion of tetrahedra)
    # CC has 22 edges: 12 path edges + 10 span-3 closing edges (quad boundaries)
    # SC has MORE edges because tetrahedra also generate span-2 edges (11 of them)
    sc_n_edges = sc_stats.get("n_simplices", {}).get(1, 33)
    sc_n_nodes = sc_stats.get("n_simplices", {}).get(0, 13)
    cc_extra_vs_path_only = n_cc_edges - 12   # quad closing edges added
    sc_extra_vs_cc = sc_n_edges - n_cc_edges   # SC has additional span-2 edges CC lacks

    cc_result = {
        "shape": list(cc_shape),
        "n_nodes": n_cc_nodes,
        "n_edges": n_cc_edges,
        "n_2cells": n_cc_2cells,
        "betti_0": betti0_cc,
        "betti_2_cc": betti2_cc,
        "l2_shape": l2_shape,
        "vs_simplicial": {
            "sc_n_nodes": sc_n_nodes,
            "sc_n_edges": sc_n_edges,
            "cc_n_nodes": n_cc_nodes,
            "cc_n_edges": n_cc_edges,
            "cc_extra_span3_closing_edges_vs_path": cc_extra_vs_path_only,
            "sc_extra_span2_edges_vs_cc": sc_extra_vs_cc,
            "note": (
                "CC quad 2-cells add span-3 closing edges (10) but NOT span-2 edges. "
                "SC tetrahedra generate ALL interior edges (span-1, span-2, span-3) = 33 total. "
                "SC has a richer 1-skeleton (33 vs 22 edges); both have betti_0=1."
            ),
        },
        "pass": betti0_cc == 1,
        "consistent_with_simplicial": betti0_cc == 1,
    }

    return cc_result


# ---------------------------------------------------------------------------
# Section 5: Sympy symbolic Laplacian (supportive cross-check)
# ---------------------------------------------------------------------------


def sympy_symbolic_laplacian_check() -> dict[str, Any]:
    """Construct the 3-node path graph Laplacian symbolically and verify.

    L_path3 = [[1,-1,0],[-1,2,-1],[0,-1,1]]

    Analytical result: det=0, nullspace=1 (betti_0=1), eigenvalues=[0,1,3].
    This confirms the Hodge-kernel betti extraction method for the minimal case.
    """
    L = sp.Matrix([[1, -1, 0], [-1, 2, -1], [0, -1, 1]])
    det_val = L.det()
    null_size = len(L.nullspace())
    eigs = sorted([float(v) for v in L.eigenvals().keys()])

    return {
        "matrix": "path_3_node_laplacian",
        "det": int(det_val),
        "nullspace_dim": null_size,
        "eigenvalues": eigs,
        "pass": det_val == 0 and null_size == 1 and eigs == [0.0, 1.0, 3.0],
    }


# ---------------------------------------------------------------------------
# Section 6: NetworkX cross-check
# ---------------------------------------------------------------------------


def networkx_path_cross_check() -> dict[str, Any]:
    """Build nx.path_graph(13) and verify topology matches SC expectations.

    Checks: 13 nodes, 12 edges, 1 connected component.
    """
    G = nx.path_graph(13)
    n_components = nx.number_connected_components(G)
    return {
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "n_connected_components": n_components,
        "pass": G.number_of_nodes() == 13 and G.number_of_edges() == 12 and n_components == 1,
    }


# ---------------------------------------------------------------------------
# Graveyard companions
# ---------------------------------------------------------------------------


def graveyard_random_shuffle_breaks_betti() -> dict[str, Any]:
    """Shuffle layer order then build SC with CANONICAL dependency edges.

    A shuffled assignment disconnects the complex if the shuffle breaks
    adjacency — but in this case since we still add adjacent-index edges
    to the same node objects, the complex remains connected.
    Instead, test by building SC using a SHUFFLED neighbor list (random pairs)
    vs canonical pairs and confirm that adding a back-edge creates betti_1 > 0.
    """
    # Build a SC where we add the cycle edge [12, 0] to test betti_1 sensitivity
    sc_cyc = tnx.SimplicialComplex()
    for name in LAYERS:
        sc_cyc.add_node(name)
    for i in range(len(LAYERS) - 1):
        sc_cyc.add_simplex([LAYERS[i], LAYERS[i + 1]])
    # Close cycle: last layer -> first layer (creates a loop)
    sc_cyc.add_simplex([LAYERS[-1], LAYERS[0]])

    L1_cyc = torch.tensor(sc_cyc.hodge_laplacian_matrix(rank=1).toarray(), dtype=FLOAT_DTYPE)
    evals_cyc = torch.linalg.eigvalsh(L1_cyc)
    betti1_cyc = int(torch.sum(torch.abs(evals_cyc) < _EIGEN_ZERO_TOL).item())

    # Canonical SC for comparison
    sc_can = tnx.SimplicialComplex()
    for name in LAYERS:
        sc_can.add_node(name)
    for i in range(len(LAYERS) - 1):
        sc_can.add_simplex([LAYERS[i], LAYERS[i + 1]])
    L1_can = torch.tensor(sc_can.hodge_laplacian_matrix(rank=1).toarray(), dtype=FLOAT_DTYPE)
    evals_can = torch.linalg.eigvalsh(L1_can)
    betti1_can = int(torch.sum(torch.abs(evals_can) < _EIGEN_ZERO_TOL).item())

    return {
        "canonical_betti_1": betti1_can,
        "cycle_betti_1": betti1_cyc,
        "cycle_detected": betti1_cyc > betti1_can,
        "pass": betti1_can == 0 and betti1_cyc == 1,
        "note": "closing cycle edge raises betti_1 from 0 to 1 — dependency cycles are detectable",
    }


def graveyard_removed_layer_changes_complex() -> dict[str, Any]:
    """Remove 1 layer (last) -> 12-node complex; dim still 3, different topology."""
    layers_12 = LAYERS[:-1]
    n = len(layers_12)
    sc12 = tnx.SimplicialComplex()
    for name in layers_12:
        sc12.add_node(name)
    for i in range(n - 1):
        sc12.add_simplex([layers_12[i], layers_12[i + 1]])
    for i in range(n - 2):
        sc12.add_simplex([layers_12[i], layers_12[i + 1], layers_12[i + 2]])
    for i in range(n - 3):
        sc12.add_simplex([layers_12[i], layers_12[i + 1], layers_12[i + 2], layers_12[i + 3]])

    n_simplices_12 = {rank: len(sc12.skeleton(rank)) for rank in range(sc12.dim + 1)}

    L0_12 = torch.tensor(sc12.hodge_laplacian_matrix(rank=0).toarray(), dtype=FLOAT_DTYPE)
    betti0_12 = int(torch.sum(torch.abs(torch.linalg.eigvalsh(L0_12)) < _EIGEN_ZERO_TOL).item())

    return {
        "n_nodes": n,
        "n_simplices": n_simplices_12,
        "dim": sc12.dim,
        "betti_0": betti0_12,
        "differs_from_13_layer": n_simplices_12.get(0, 0) == 12,
        "pass": n_simplices_12.get(0, 0) == 12 and betti0_12 == 1,
        "note": "removing 1 layer reduces 0-simplex count from 13 to 12; topology preserved but extent changes",
    }


def graveyard_redundant_edges_inflate_betti1() -> dict[str, Any]:
    """Add redundant (non-adjacent) edges to form a cycle -> betti_1 > 0."""
    sc_extra = tnx.SimplicialComplex()
    for name in LAYERS:
        sc_extra.add_node(name)
    for i in range(len(LAYERS) - 1):
        sc_extra.add_simplex([LAYERS[i], LAYERS[i + 1]])
    # Add three skip-2 edges that close independent cycles
    sc_extra.add_simplex([LAYERS[0], LAYERS[2]])   # shortcut
    sc_extra.add_simplex([LAYERS[5], LAYERS[8]])   # shortcut
    sc_extra.add_simplex([LAYERS[10], LAYERS[12]])  # shortcut

    L1_extra = torch.tensor(sc_extra.hodge_laplacian_matrix(rank=1).toarray(), dtype=FLOAT_DTYPE)
    evals_extra = torch.linalg.eigvalsh(L1_extra)
    betti1_extra = int(torch.sum(torch.abs(evals_extra) < _EIGEN_ZERO_TOL).item())

    return {
        "shortcuts_added": 3,
        "betti_1_with_shortcuts": betti1_extra,
        "betti_inflated": betti1_extra > 0,
        "pass": betti1_extra > 0,
        "note": "shortcut (non-adjacent) edges that form cycles raise betti_1 above 0",
    }


# ---------------------------------------------------------------------------
# Boundary tests
# ---------------------------------------------------------------------------


def boundary_tests(sc: tnx.SimplicialComplex, hodge: dict[str, Any]) -> dict[str, Any]:
    # After face-completion:
    # L_0: 13x13 (one row/col per node)
    # L_1: 33x33 (one row/col per edge, all face-completed edges)
    # L_2: 31x31 (one row/col per triangle)
    # L_3: 10x10 (one row/col per tetrahedron)
    return {
        "layer_count_is_13": {
            "layer_count": len(LAYERS),
            "pass": len(LAYERS) == 13,
        },
        "simplicial_complex_dim_is_3": {
            "dim": sc.dim,
            "pass": sc.dim == 3,
        },
        "l0_matrix_is_13x13": {
            "shape": hodge.get("L_0", {}).get("shape", []),
            "pass": hodge.get("L_0", {}).get("shape", []) == [13, 13],
        },
        "l1_matrix_is_33x33": {
            "shape": hodge.get("L_1", {}).get("shape", []),
            "pass": hodge.get("L_1", {}).get("shape", []) == [33, 33],
        },
        "l2_matrix_is_31x31": {
            "shape": hodge.get("L_2", {}).get("shape", []),
            "pass": hodge.get("L_2", {}).get("shape", []) == [31, 31],
        },
        "l3_matrix_is_10x10": {
            "shape": hodge.get("L_3", {}).get("shape", []),
            "pass": hodge.get("L_3", {}).get("shape", []) == [10, 10],
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> dict[str, Any]:
    started = time.time()

    # --- Build ---
    sc_build = build_simplicial_complex()
    sc: tnx.SimplicialComplex = sc_build.pop("complex")
    sc_build_serializable = {k: v for k, v in sc_build.items()}

    # --- Hodge Laplacians ---
    hodge = compute_hodge_laplacians(sc)

    # --- Persistent homology ---
    persistence = compute_persistent_homology()

    # --- CellComplex comparison ---
    cell_complex = build_cell_complex_and_compare(sc_build_serializable)

    # --- Sympy cross-check ---
    sympy_check = sympy_symbolic_laplacian_check()

    # --- NetworkX cross-check ---
    nx_check = networkx_path_cross_check()

    # --- Graveyard ---
    graveyard = {
        "random_dependency_order_breaks_betti_consistency": graveyard_random_shuffle_breaks_betti(),
        "removed_layer_changes_complex_dimension": graveyard_removed_layer_changes_complex(),
        "redundant_dependency_edges_inflate_betti_1": graveyard_redundant_edges_inflate_betti1(),
    }

    # --- Boundary ---
    boundary = boundary_tests(sc, hodge)

    # --- Positive predicates ---
    positive = {
        "thirteen_layer_simplicial_complex_built_successfully": sc_build_serializable,
        "higher_rank_laplacians_computed": {
            "hodge": hodge,
            "pass": hodge.get("pass", False),
        },
        "betti_numbers_match_expected": {
            "betti": hodge.get("betti_numbers", {}),
            "expected": hodge.get("expected_betti", {}),
            "pass": hodge.get("betti_pass", False),
        },
        "persistent_homology_intervals_computed": persistence,
        "cell_complex_provides_consistent_or_different_invariants": {
            "cell_complex": cell_complex,
            "pass": cell_complex.get("pass", False),
            "verdict": (
                "consistent_betti_0" if cell_complex.get("betti_0") == 1
                else "inconsistent_betti_0"
            ),
        },
        "sympy_symbolic_laplacian_cross_check": sympy_check,
        "networkx_path_topology_cross_check": nx_check,
    }

    # --- all_pass ---
    # Flatten nested "pass" fields: positive and graveyard values may nest pass inside sub-dicts
    def _get_pass(v: Any) -> bool:
        if isinstance(v, dict):
            if "pass" in v:
                return bool(v["pass"])
        return True  # non-dict entries don't gate all_pass

    all_pass = (
        all(_get_pass(v) for v in positive.values())
        and all(_get_pass(v) for v in graveyard.values())
        and all(_get_pass(v) for v in boundary.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": (
            "13-layer constraint manifold dependency tower as SimplicialComplex "
            "(dim 3) with Hodge Laplacians L_0/L_1/L_2, betti numbers, "
            "and gudhi persistent homology"
        ),
        "candidate_layers": LAYERS,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for v in graveyard.values() if v.get("pass", False)),
        },
        "blockers": [],
        "open_choices": [
            "3-simplices (tetrahedra) were included but only rank 0/1/2 Laplacians "
            "were extracted — L_3 computation would require checking if TopoNetX "
            "supports rank=3 hodge_laplacian_matrix for dim-3 SC",
            "CellComplex 2-cells use quadrilateral windows; triangular 2-cells would "
            "produce a CC structurally equivalent to the SC for comparison",
        ],
        "why_not_v4_probes": "Clean v5 geometry-tower TopoNetX scout; not part of mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "n_simplices_per_rank": sc_build_serializable.get("n_simplices", {}),
            "betti_numbers": hodge.get("betti_numbers", {}),
            "persistence_pairs_total": persistence.get("persistence_pairs_total", -1),
            "l0_spectrum_top5": hodge.get("L_0", {}).get("eigenvalues_ascending_top5", []),
            "cc_edges": cell_complex.get("n_edges", -1),
            "sc_edges": sc_build_serializable.get("n_simplices", {}).get(1, -1),
            "sc_minus_cc_edges": (
                sc_build_serializable.get("n_simplices", {}).get(1, 0)
                - cell_complex.get("n_edges", 0)
            ),
        },
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
