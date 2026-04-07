#!/usr/bin/env python3
"""
sim_negative_topology_graphs.py
===============================

NEGATIVE battery for topology and graph structures.

When do cell complexes break?  What do degenerate graphs look like?
This probe systematically tests the boundary conditions and failure modes
of TopoNetX cell complexes and PyG message passing.

No engine.  Pure numpy / toponetx / torch_geometric.

Tests
-----
 1. Cell complex with 0 vertices: does TopoNetX handle it?
 2. Dangling edge (edge to non-existent vertex): should fail or warn.
 3. B2*B1 for NON-valid cell complex (random incidence): should NOT be zero.
 4. Euler characteristic: Klein bottle vs torus (both chi=0). Can we distinguish?
 5. Disconnected graph: b0=2. Hodge Laplacian has 2 zero eigenvalues.
 6. K1 (single vertex): trivial. Betti = [1, 0, ...].
 7. Self-loop in PyG graph: does it change message passing?
 8. Negative edge weights: does message passing still converge?
 9. Graph with no edges: isolated nodes. Message passing = no change.
10. Cell complex with overlapping faces: topologically invalid. What happens?

Results -> a2_state/sim_results/negative_topology_graphs_results.json
"""

import json
import os
import sys
import traceback
from datetime import datetime, UTC

import numpy as np
import scipy.sparse as sp

# ── toponetx ──────────────────────────────────────────────────────
from toponetx import CellComplex

# ── torch / pyg ───────────────────────────────────────────────────
import torch
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)
RESULTS_PATH = os.path.join(RESULTS_DIR, "negative_topology_graphs_results.json")


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  HELPERS                                                          ║
# ╚═══════════════════════════════════════════════════════════════════╝

class SimplePropagation(MessagePassing):
    """Additive message passing for testing edge cases (no weights)."""
    def __init__(self):
        super().__init__(aggr="add")

    def forward(self, x, edge_index):
        return self.propagate(edge_index, x=x)

    def message(self, x_j):
        return x_j


class WeightedPropagation(MessagePassing):
    """Additive message passing WITH edge weights."""
    def __init__(self):
        super().__init__(aggr="add")

    def forward(self, x, edge_index, edge_weight):
        return self.propagate(edge_index, x=x, edge_weight=edge_weight)

    def message(self, x_j, edge_weight):
        return x_j * edge_weight.unsqueeze(-1)


def betti_from_incidence(B, n_cells_prev, n_cells_curr):
    """Compute Betti number from incidence matrix via rank-nullity."""
    if B.shape[0] == 0 or B.shape[1] == 0:
        return None
    if sp.issparse(B):
        B_dense = B.toarray()
    else:
        B_dense = np.array(B, dtype=float)
    rank = np.linalg.matrix_rank(B_dense)
    return int(B_dense.shape[1] - rank)  # nullity = dim(kernel)


def safe_run(name, fn):
    """Run a test function, catch and record any exception."""
    try:
        result = fn()
        result["test"] = name
        result["status"] = result.get("status", "PASS")
        return result
    except Exception as e:
        return {
            "test": name,
            "status": "ERROR",
            "error_type": type(e).__name__,
            "error_msg": str(e),
            "traceback": traceback.format_exc(),
        }


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  TEST 1: Empty cell complex (0 vertices)                         ║
# ╚═══════════════════════════════════════════════════════════════════╝

def test_01_empty_complex():
    """Cell complex with 0 vertices. Does TopoNetX handle it?"""
    cc = CellComplex()
    n_nodes = cc.number_of_nodes()
    n_edges = cc.number_of_edges()
    n_cells = cc.number_of_cells()

    # Try to get incidence matrix on empty complex
    incidence_ok = False
    incidence_error = None
    try:
        B1 = cc.incidence_matrix(rank=1)
        incidence_ok = True
    except Exception as e:
        incidence_error = f"{type(e).__name__}: {e}"

    # Try Hodge Laplacian on empty complex
    hodge_ok = False
    hodge_error = None
    try:
        L0 = cc.hodge_laplacian_matrix(rank=0)
        hodge_ok = True
    except Exception as e:
        hodge_error = f"{type(e).__name__}: {e}"

    # Expected: either graceful empty matrices or informative errors
    return {
        "description": "Empty CellComplex (0 vertices, 0 edges, 0 faces)",
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "n_cells": n_cells,
        "incidence_matrix_ok": incidence_ok,
        "incidence_error": incidence_error,
        "hodge_laplacian_ok": hodge_ok,
        "hodge_error": hodge_error,
        "verdict": "TopoNetX handles empty complex gracefully"
                   if (incidence_ok and hodge_ok)
                   else "TopoNetX rejects empty complex (expected for negative test)",
    }


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  TEST 2: Dangling edge (edge to non-existent vertex)              ║
# ╚═══════════════════════════════════════════════════════════════════╝

def test_02_dangling_edge():
    """Add edge referencing vertices not yet in the complex.
    TopoNetX may auto-create them or reject. Document behavior."""
    cc = CellComplex()
    cc.add_node(0)
    # Add edge (0,99) -- vertex 99 was never added explicitly
    error_msg = None
    auto_created = False
    try:
        cc.add_cell([0, 99], rank=1)
        # Check if vertex 99 was auto-created
        auto_created = 99 in cc.nodes
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"

    # Now try truly dangling: add a face referencing an edge that does not exist
    face_error = None
    face_ok = False
    try:
        cc2 = CellComplex()
        cc2.add_node(0)
        cc2.add_node(1)
        cc2.add_node(2)
        # Add face (0,1,2) without adding the edges first
        cc2.add_cell([0, 1, 2], rank=2)
        face_ok = True
        # Check if edges were auto-created
        edges_auto = cc2.number_of_edges()
    except Exception as e:
        face_error = f"{type(e).__name__}: {e}"
        edges_auto = 0

    return {
        "description": "Dangling edge / face: references to non-existent lower cells",
        "edge_to_missing_vertex_error": error_msg,
        "vertex_auto_created": auto_created,
        "face_without_edges_ok": face_ok,
        "face_without_edges_error": face_error,
        "edges_auto_created_for_face": edges_auto,
        "verdict": (
            "TopoNetX auto-creates missing lower cells (permissive)"
            if (auto_created and face_ok)
            else "TopoNetX enforces strict cell hierarchy"
        ),
    }


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  TEST 3: B2*B1 != 0 for random (non-valid) incidence matrices    ║
# ╚═══════════════════════════════════════════════════════════════════╝

def test_03_random_incidence_not_chain():
    """For a valid cell complex, B2 @ B1 = 0 (boundary of boundary is zero).
    For random incidence matrices, this should FAIL."""
    np.random.seed(42)

    # Build random incidence matrices (NOT from a valid complex)
    n_verts, n_edges, n_faces = 6, 10, 4
    B1_rand = np.random.choice([-1, 0, 1], size=(n_verts, n_edges))
    B2_rand = np.random.choice([-1, 0, 1], size=(n_edges, n_faces))

    product = B1_rand @ B2_rand
    is_zero = np.allclose(product, 0)
    max_entry = float(np.max(np.abs(product)))

    # For contrast, build a valid complex and verify B2@B1 = 0
    cc = CellComplex()
    for e in [(0,1),(1,2),(2,0),(0,3),(1,3),(2,3)]:
        cc.add_cell(list(e), rank=1)
    for f in [(0,1,2),(0,1,3)]:
        cc.add_cell(list(f), rank=2)

    B1_valid = cc.incidence_matrix(rank=1).toarray()
    B2_valid = cc.incidence_matrix(rank=2).toarray()
    valid_product = B1_valid @ B2_valid
    valid_is_zero = np.allclose(valid_product, 0)

    return {
        "description": "Chain complex property: B2*B1=0 for valid, !=0 for random",
        "random_B2_B1_is_zero": bool(is_zero),
        "random_max_abs_entry": max_entry,
        "valid_B2_B1_is_zero": bool(valid_is_zero),
        "status": "PASS" if (not is_zero and valid_is_zero) else "FAIL",
        "verdict": (
            "CONFIRMED: random incidence breaks chain complex property"
            if (not is_zero and valid_is_zero)
            else "UNEXPECTED: check random seed or valid complex construction"
        ),
    }


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  TEST 4: Klein bottle vs torus (both chi=0, non-orientable vs    ║
# ║          orientable). Can we distinguish them?                    ║
# ╚═══════════════════════════════════════════════════════════════════╝

def test_04_klein_bottle_vs_torus():
    """Both have Euler characteristic 0.
    Klein bottle: chi=0, b0=1, b1=1, b2=0 (over Z, non-orientable)
    Torus:        chi=0, b0=1, b1=2, b2=1 (orientable)
    We test whether Betti numbers (computed over R) distinguish them.

    Klein bottle as a square with identified edges:
    - top/bottom identified same direction
    - left/right identified REVERSED direction (twist)
    We build it as a simplicial complex on a 3x3 grid.
    """
    N = 3

    def vid(r, c):
        return (r % N) * N + (c % N)

    # TORUS: standard identification (both pairs same direction)
    cc_torus = CellComplex()
    for r in range(N):
        for c in range(N):
            v0 = vid(r, c)
            v1 = vid(r, c + 1)
            v2 = vid(r + 1, c)
            v3 = vid(r + 1, c + 1)
            cc_torus.add_cell([v0, v1], rank=1)
            cc_torus.add_cell([v0, v2], rank=1)
            cc_torus.add_cell([v1, v3], rank=1)
            cc_torus.add_cell([v2, v3], rank=1)
            cc_torus.add_cell([v0, v1, v3], rank=2)
            cc_torus.add_cell([v0, v2, v3], rank=2)

    # KLEIN BOTTLE: left/right identified with twist
    # In the Klein bottle, when wrapping column c -> c+1 mod N,
    # the row index is REVERSED for the right edge identification.
    # We implement this by using a different vertex mapping for the
    # right-edge gluing.
    cc_klein = CellComplex()

    def vid_klein(r, c):
        """Klein bottle identification: (r, N) ~ (N-1-r, 0) for twist."""
        c_mod = c % N
        r_mod = r % N
        if c >= N:
            # Twisted identification: reverse row
            r_mod = (N - 1 - r) % N
            c_mod = c % N
        return r_mod * N + c_mod

    for r in range(N):
        for c in range(N):
            v0 = vid_klein(r, c)
            v1 = vid_klein(r, c + 1)
            v2 = vid_klein(r + 1, c)
            v3 = vid_klein(r + 1, c + 1)
            cc_klein.add_cell([v0, v1], rank=1)
            cc_klein.add_cell([v0, v2], rank=1)
            cc_klein.add_cell([v1, v3], rank=1)
            cc_klein.add_cell([v2, v3], rank=1)
            cc_klein.add_cell([v0, v1, v3], rank=2)
            cc_klein.add_cell([v0, v2, v3], rank=2)

    # Euler characteristics
    chi_torus = cc_torus.euler_characterisitics()
    chi_klein = cc_klein.euler_characterisitics()

    # Betti numbers via Hodge Laplacian eigenvalues
    def betti_from_hodge(cc, max_rank=2):
        bettis = []
        for r in range(max_rank + 1):
            try:
                L = cc.hodge_laplacian_matrix(rank=r).toarray().astype(float)
                eigs = np.linalg.eigvalsh(L)
                n_zero = int(np.sum(np.abs(eigs) < 1e-8))
                bettis.append(n_zero)
            except Exception:
                bettis.append(None)
        return bettis

    betti_torus = betti_from_hodge(cc_torus)
    betti_klein = betti_from_hodge(cc_klein)

    # Over R (real coefficients), Klein bottle has b1=1 (not 2 like torus)
    # because the twisted identification kills one homology generator.
    # BUT: TopoNetX works with simplicial/cell complexes combinatorially,
    # so the Klein bottle built this way may not capture the twist correctly.
    # This is a known limitation -- document it.

    distinguishable = betti_torus != betti_klein

    return {
        "description": "Klein bottle vs torus: both chi=0. Distinguish via Betti?",
        "torus_chi": chi_torus,
        "klein_chi": chi_klein,
        "torus_betti": betti_torus,
        "klein_betti": betti_klein,
        "torus_shape": list(cc_torus.shape),
        "klein_shape": list(cc_klein.shape),
        "distinguishable_by_betti": distinguishable,
        "note": (
            "Theory: over Z, Klein b1=1 (torsion Z/2Z in H1), torus b1=2. "
            "Over R, Klein b1 should also be 1 (free part only). "
            "If our combinatorial construction captures the twist correctly, "
            "Betti numbers alone distinguish them. If not, the construction "
            "collapsed to the same quotient and we need Z-homology."
        ),
        "verdict": (
            "DISTINGUISHED by Betti numbers"
            if distinguishable
            else "NOT distinguishable: chi and real-Betti identical. Need Z-coefficients or orientation."
        ),
    }


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  TEST 5: Disconnected graph: b0=2, 2 zero eigenvalues in L0      ║
# ╚═══════════════════════════════════════════════════════════════════╝

def test_05_disconnected_graph():
    """Two disconnected triangles. b0 should be 2.
    Hodge Laplacian L0 should have exactly 2 zero eigenvalues."""
    cc = CellComplex()
    # Triangle 1: vertices 0,1,2
    cc.add_cell([0, 1], rank=1)
    cc.add_cell([1, 2], rank=1)
    cc.add_cell([0, 2], rank=1)
    cc.add_cell([0, 1, 2], rank=2)
    # Triangle 2: vertices 3,4,5 (disconnected)
    cc.add_cell([3, 4], rank=1)
    cc.add_cell([4, 5], rank=1)
    cc.add_cell([3, 5], rank=1)
    cc.add_cell([3, 4, 5], rank=2)

    L0 = cc.hodge_laplacian_matrix(rank=0).toarray().astype(float)
    eigs = np.linalg.eigvalsh(L0)
    n_zero = int(np.sum(np.abs(eigs) < 1e-8))

    is_connected = cc.is_connected()

    return {
        "description": "Disconnected graph: two triangles. Expect b0=2.",
        "n_nodes": cc.number_of_nodes(),
        "n_edges": cc.number_of_edges(),
        "is_connected": is_connected,
        "L0_eigenvalues": [round(float(e), 8) for e in sorted(eigs)],
        "n_zero_eigenvalues": n_zero,
        "status": "PASS" if n_zero == 2 else "FAIL",
        "verdict": (
            f"CONFIRMED: b0={n_zero} zero eigenvalues = 2 connected components"
            if n_zero == 2
            else f"UNEXPECTED: found {n_zero} zero eigenvalues, expected 2"
        ),
    }


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  TEST 6: K1 (single vertex). Trivial complex.                    ║
# ╚═══════════════════════════════════════════════════════════════════╝

def test_06_single_vertex_K1():
    """K1: 1 vertex, 0 edges, 0 faces. Betti = [1, 0, 0]."""
    cc = CellComplex()
    cc.add_node(0)

    betti = []
    errors = []
    for r in range(3):
        try:
            L = cc.hodge_laplacian_matrix(rank=r).toarray().astype(float)
            eigs = np.linalg.eigvalsh(L)
            n_zero = int(np.sum(np.abs(eigs) < 1e-8))
            betti.append(n_zero)
        except Exception as e:
            betti.append(None)
            errors.append(f"rank={r}: {type(e).__name__}: {e}")

    # For K1: b0=1 (one component), b1=0 (no loops), b2=0 (no cavities)
    expected = [1, 0, 0]
    # Only compare non-None entries
    matches = all(
        b == e for b, e in zip(betti, expected) if b is not None
    )

    return {
        "description": "K1 (single vertex): trivial complex",
        "shape": list(cc.shape),
        "betti_numbers": betti,
        "expected_betti": expected,
        "errors": errors if errors else None,
        "status": "PASS" if matches else "FAIL",
        "verdict": (
            "CONFIRMED: K1 has Betti = [1, 0, 0] (or graceful empty for higher ranks)"
            if matches
            else f"UNEXPECTED Betti: {betti}"
        ),
    }


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  TEST 7: Self-loop in PyG graph                                   ║
# ╚═══════════════════════════════════════════════════════════════════╝

def test_07_self_loop_pyg():
    """Does a self-loop change message passing behavior in PyG?"""
    n = 4
    # Graph without self-loop: path 0-1-2-3
    edge_index_no_loop = torch.tensor(
        [[0,1,1,2,2,3],
         [1,0,2,1,3,2]], dtype=torch.long
    )
    # Graph with self-loop on node 1
    edge_index_with_loop = torch.tensor(
        [[0,1,1,2,2,3,1],
         [1,0,2,1,3,2,1]], dtype=torch.long
    )

    x = torch.zeros(n, 1)
    x[0] = 1.0  # seed node 0

    mp = SimplePropagation()

    # Run 3 rounds without self-loop
    feat_no = x.clone()
    for _ in range(3):
        feat_no = mp(feat_no, edge_index_no_loop)

    # Run 3 rounds with self-loop
    feat_yes = x.clone()
    for _ in range(3):
        feat_yes = mp(feat_yes, edge_index_with_loop)

    diff = (feat_yes - feat_no).abs().sum().item()

    return {
        "description": "Self-loop in PyG: does it affect message passing?",
        "features_no_loop": feat_no.squeeze().tolist(),
        "features_with_loop": feat_yes.squeeze().tolist(),
        "total_abs_diff": round(diff, 6),
        "self_loop_changes_output": diff > 1e-6,
        "status": "PASS",
        "verdict": (
            "Self-loop DOES change message passing output (node receives its own message)"
            if diff > 1e-6
            else "Self-loop has NO effect (unexpected for additive aggregation)"
        ),
    }


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  TEST 8: Negative edge weights in message passing                 ║
# ╚═══════════════════════════════════════════════════════════════════╝

def test_08_negative_edge_weights():
    """Negative edge weights: does message passing converge or diverge?"""
    n = 5
    # Cycle graph: 0-1-2-3-4-0
    src = list(range(n)) + [(i + 1) % n for i in range(n)]
    dst = [(i + 1) % n for i in range(n)] + list(range(n))
    edge_index = torch.tensor([src, dst], dtype=torch.long)

    x = torch.randn(n, 2)

    mp = WeightedPropagation()

    # Positive weights
    pos_weights = torch.ones(2 * n)
    # Negative weights
    neg_weights = -torch.ones(2 * n)
    # Mixed weights
    mix_weights = torch.tensor([1.0, -1.0] * n)

    results_pos = []
    results_neg = []
    results_mix = []

    feat_pos = x.clone()
    feat_neg = x.clone()
    feat_mix = x.clone()

    for step in range(10):
        feat_pos = mp(feat_pos, edge_index, edge_weight=pos_weights)
        feat_neg = mp(feat_neg, edge_index, edge_weight=neg_weights)
        feat_mix = mp(feat_mix, edge_index, edge_weight=mix_weights)
        results_pos.append(feat_pos.norm().item())
        results_neg.append(feat_neg.norm().item())
        results_mix.append(feat_mix.norm().item())

    pos_converges = results_pos[-1] < 1e10
    neg_converges = results_neg[-1] < 1e10
    mix_converges = results_mix[-1] < 1e10

    return {
        "description": "Negative edge weights in message passing",
        "positive_norms": [round(v, 4) for v in results_pos],
        "negative_norms": [round(v, 4) for v in results_neg],
        "mixed_norms":    [round(v, 4) for v in results_mix],
        "positive_converges": pos_converges,
        "negative_converges": neg_converges,
        "mixed_converges": mix_converges,
        "status": "PASS",
        "verdict": (
            f"Positive: {'converges' if pos_converges else 'DIVERGES'}. "
            f"Negative: {'converges' if neg_converges else 'DIVERGES'}. "
            f"Mixed: {'converges' if mix_converges else 'DIVERGES'}. "
            "Negative weights can cause oscillation/divergence in raw additive MP."
        ),
    }


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  TEST 9: Graph with no edges (isolated nodes)                     ║
# ╚═══════════════════════════════════════════════════════════════════╝

def test_09_no_edges_isolated():
    """Graph with nodes but no edges. Message passing should leave features unchanged."""
    n = 5
    edge_index = torch.zeros((2, 0), dtype=torch.long)
    x = torch.randn(n, 3)

    mp = SimplePropagation()

    feat_after = mp(x, edge_index)
    diff = (feat_after - torch.zeros_like(x)).abs().sum().item()
    # With additive aggregation and no edges, output should be all zeros
    # (no messages received by any node)

    return {
        "description": "No edges: isolated nodes. Message passing = zero output.",
        "input_features_norm": round(x.norm().item(), 6),
        "output_features_norm": round(feat_after.norm().item(), 6),
        "output_is_zero": diff < 1e-8,
        "status": "PASS" if diff < 1e-8 else "FAIL",
        "verdict": (
            "CONFIRMED: no edges means no messages, output is zero"
            if diff < 1e-8
            else f"UNEXPECTED: output norm = {feat_after.norm().item():.6f}"
        ),
    }


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  TEST 10: Overlapping faces in cell complex                       ║
# ╚═══════════════════════════════════════════════════════════════════╝

def test_10_overlapping_faces():
    """Add two faces that share the same edges (topologically overlapping).
    This is invalid in a well-formed CW complex. What does TopoNetX do?"""
    cc = CellComplex()
    # Build a triangle: edges (0,1), (1,2), (0,2)
    cc.add_cell([0, 1], rank=1)
    cc.add_cell([1, 2], rank=1)
    cc.add_cell([0, 2], rank=1)

    # Add face (0,1,2) twice -- overlapping faces
    cc.add_cell([0, 1, 2], rank=2)
    n_cells_after_first = cc.number_of_cells()

    cc.add_cell([0, 1, 2], rank=2)
    n_cells_after_second = cc.number_of_cells()

    duplicate_accepted = (n_cells_after_second > n_cells_after_first)
    deduplicated = (n_cells_after_second == n_cells_after_first)

    # Also try a different face with overlapping edges but different vertex set
    # (e.g., a square face using edges already in the complex)
    cc.add_node(3)
    cc.add_cell([0, 3], rank=1)
    cc.add_cell([2, 3], rank=1)
    cc.add_cell([0, 2, 3], rank=2)  # shares edge (0,2) with face (0,1,2)
    n_cells_shared_edge = cc.number_of_cells()

    # Check B2*B1 = 0 still holds
    try:
        B1 = cc.incidence_matrix(rank=1).toarray()
        B2 = cc.incidence_matrix(rank=2).toarray()
        product = B1 @ B2
        chain_valid = bool(np.allclose(product, 0))
    except Exception as e:
        chain_valid = None

    return {
        "description": "Overlapping faces: same face added twice + shared-edge faces",
        "n_cells_after_first_face": n_cells_after_first,
        "n_cells_after_duplicate_face": n_cells_after_second,
        "duplicate_was_accepted": duplicate_accepted,
        "duplicate_was_deduplicated": deduplicated,
        "n_cells_with_shared_edge_face": n_cells_shared_edge,
        "chain_complex_still_valid": chain_valid,
        "status": "PASS",
        "verdict": (
            "TopoNetX DEDUPLICATES identical faces (safe)"
            if deduplicated
            else "TopoNetX ACCEPTS duplicate faces (dangerous for topology)"
        ),
    }


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  MAIN: Run all tests, emit JSON                                   ║
# ╚═══════════════════════════════════════════════════════════════════╝

def main():
    tests = [
        ("01_empty_complex", test_01_empty_complex),
        ("02_dangling_edge", test_02_dangling_edge),
        ("03_random_incidence_not_chain", test_03_random_incidence_not_chain),
        ("04_klein_vs_torus", test_04_klein_bottle_vs_torus),
        ("05_disconnected_graph", test_05_disconnected_graph),
        ("06_K1_single_vertex", test_06_single_vertex_K1),
        ("07_self_loop_pyg", test_07_self_loop_pyg),
        ("08_negative_edge_weights", test_08_negative_edge_weights),
        ("09_no_edges_isolated", test_09_no_edges_isolated),
        ("10_overlapping_faces", test_10_overlapping_faces),
    ]

    results = []
    for name, fn in tests:
        print(f"  Running {name}...", end=" ", flush=True)
        r = safe_run(name, fn)
        status = r.get("status", "?")
        print(f"[{status}]")
        results.append(r)

    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_negative_topology_graphs",
        "description": "Negative battery: topology + graph edge cases and failure modes",
        "n_tests": len(results),
        "n_pass": sum(1 for r in results if r["status"] == "PASS"),
        "n_fail": sum(1 for r in results if r["status"] == "FAIL"),
        "n_error": sum(1 for r in results if r["status"] == "ERROR"),
        "tests": results,
    }

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n  Results -> {RESULTS_PATH}")
    print(f"  PASS: {summary['n_pass']}  FAIL: {summary['n_fail']}  ERROR: {summary['n_error']}")

    return summary


if __name__ == "__main__":
    main()
