#!/usr/bin/env python3
"""
sim_pure_lego_topology_graphs.py
================================

Pure topology + graph lego blocks.  No engine.  Rate-limited before -- built now.

Constructs cell complexes from scratch, verifies algebraic topology invariants,
then mirrors the same structures as PyG graphs with message passing.

Libraries: numpy, scipy, toponetx, torch, torch_geometric.

Blocks built
------------
1. Cell complexes: circle (S1), sphere (S2), torus (T2), nested tori.
2. Incidence matrices B1, B2 and chain-complex identity B1 @ B2 = 0.
3. Betti numbers via rank-nullity on incidence matrices.
4. Hodge Laplacians L0, L1 with eigenvalue verification of Betti numbers.
5. Discrete calculus: gradient (vert -> edge), curl (edge -> face), curl(grad)=0.
6. PyG Data objects for the same structures; node/edge counts match.
7. Message passing: seed one node, propagate 10 rounds, measure spread.

Results written to a2_state/sim_results/pure_lego_topology_graphs_results.json
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

# ── toponetx ──────────────────────────────────────────────────────
from toponetx import CellComplex

# ── torch / pyg ───────────────────────────────────────────────────
import torch
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
classification = "classical_baseline"  # auto-backfill

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)
RESULTS_PATH = os.path.join(RESULTS_DIR, "pure_lego_topology_graphs_results.json")


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  1. CELL COMPLEX BUILDERS                                        ║
# ╚═══════════════════════════════════════════════════════════════════╝

def build_circle() -> CellComplex:
    """S1 as a polygon: 4 vertices, 4 edges, 0 faces."""
    cc = CellComplex()
    n = 4
    for i in range(n):
        cc.add_cell([i, (i + 1) % n], rank=1)
    return cc


def build_sphere() -> CellComplex:
    """
    S2 via a tetrahedron shell: 4 vertices, 6 edges, 4 triangular faces.
    Euler chi = 4 - 6 + 4 = 2.
    """
    cc = CellComplex()
    verts = [0, 1, 2, 3]
    edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    faces = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
    for e in edges:
        cc.add_cell(list(e), rank=1)
    for f in faces:
        cc.add_cell(list(f), rank=2)
    return cc


def build_torus() -> CellComplex:
    """
    Torus via 3x3 grid with opposite-edge identification.
    9 vertices, 18 edges (after identification), 9 faces.
    Euler chi = 9 - 18 + 9 = 0.
    """
    cc = CellComplex()
    N = 3

    def vid(r, c):
        return (r % N) * N + (c % N)

    # Add all edges first (horizontal + vertical)
    edge_set = set()
    for r in range(N):
        for c in range(N):
            # horizontal edge to right neighbor (with wrap)
            e1 = tuple(sorted([vid(r, c), vid(r, c + 1)]))
            edge_set.add(e1)
            # vertical edge to bottom neighbor (with wrap)
            e2 = tuple(sorted([vid(r, c), vid(r + 1, c)]))
            edge_set.add(e2)

    for e in edge_set:
        cc.add_cell(list(e), rank=1)

    # Add square faces as two triangles each
    for r in range(N):
        for c in range(N):
            v00 = vid(r, c)
            v10 = vid(r + 1, c)
            v01 = vid(r, c + 1)
            v11 = vid(r + 1, c + 1)
            # upper triangle
            tri1 = [v00, v01, v11]
            # lower triangle
            tri2 = [v00, v10, v11]
            # Need diagonal edge for triangles
            diag = tuple(sorted([v00, v11]))
            if diag not in edge_set:
                cc.add_cell(list(diag), rank=1)
                edge_set.add(diag)
            try:
                cc.add_cell(tri1, rank=2)
            except ValueError:
                # add missing edges and retry
                for pair in [(tri1[0], tri1[1]), (tri1[1], tri1[2]), (tri1[0], tri1[2])]:
                    ep = tuple(sorted(pair))
                    if ep not in edge_set:
                        cc.add_cell(list(ep), rank=1)
                        edge_set.add(ep)
                cc.add_cell(tri1, rank=2)
            try:
                cc.add_cell(tri2, rank=2)
            except ValueError:
                for pair in [(tri2[0], tri2[1]), (tri2[1], tri2[2]), (tri2[0], tri2[2])]:
                    ep = tuple(sorted(pair))
                    if ep not in edge_set:
                        cc.add_cell(list(ep), rank=1)
                        edge_set.add(ep)
                cc.add_cell(tri2, rank=2)

    return cc


def build_nested_tori() -> tuple:
    """Two disjoint tori (no shared vertices)."""
    t1 = build_torus()
    t2_raw = build_torus()

    # Build second torus with offset vertex ids
    offset = max(n for n in t1.nodes) + 1
    t2 = CellComplex()
    for e in t2_raw.edges:
        t2.add_cell([e[0] + offset, e[1] + offset], rank=1)
    for c in t2_raw.cells:
        t2.add_cell([v + offset for v in c], rank=2)

    # Merge into one complex
    merged = CellComplex()
    for e in t1.edges:
        merged.add_cell(list(e), rank=1)
    for c in t1.cells:
        merged.add_cell(list(c), rank=2)
    for e in t2.edges:
        merged.add_cell(list(e), rank=1)
    for c in t2.cells:
        merged.add_cell(list(c), rank=2)

    return merged, offset


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  2. INCIDENCE MATRICES & CHAIN COMPLEX                           ║
# ╚═══════════════════════════════════════════════════════════════════╝

def get_incidence(cc: CellComplex):
    """Return B1 (nodes x edges) and B2 (edges x faces) as dense arrays."""
    B1 = cc.incidence_matrix(1).toarray().astype(float)
    n_cells = len(list(cc.cells))
    if n_cells > 0:
        B2 = cc.incidence_matrix(2).toarray().astype(float)
    else:
        B2 = np.zeros((B1.shape[1], 0))
    return B1, B2


def verify_chain_complex(B1, B2):
    """B1 @ B2 must be zero (boundary of boundary = 0)."""
    if B2.shape[1] == 0:
        return True, 0.0
    product = B1 @ B2
    max_err = float(np.max(np.abs(product)))
    return max_err < 1e-10, max_err


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  3. BETTI NUMBERS (rank-nullity)                                  ║
# ╚═══════════════════════════════════════════════════════════════════╝

def compute_betti_rank_nullity(B1, B2):
    """
    b0 = dim(ker B1^T)        = V - rank(B1)
    b1 = dim(ker B2^T) - rank(B1)  = nullity(B2^T) - rank(B1)
         (equiv: E - rank(B1) - rank(B2))
    b2 = dim(ker ...) = F - rank(B2)
    """
    tol = 1e-8
    rank_B1 = np.linalg.matrix_rank(B1, tol=tol)
    rank_B2 = np.linalg.matrix_rank(B2, tol=tol)
    V = B1.shape[0]
    E = B1.shape[1]
    F = B2.shape[1]

    b0 = V - rank_B1
    b1 = E - rank_B1 - rank_B2
    b2 = F - rank_B2

    return [int(b0), int(b1), int(b2)], {"V": V, "E": E, "F": F,
                                           "rank_B1": int(rank_B1),
                                           "rank_B2": int(rank_B2)}


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  4. HODGE LAPLACIANS & EIGENVALUE BETTI CHECK                    ║
# ╚═══════════════════════════════════════════════════════════════════╝

def hodge_laplacians(cc: CellComplex):
    """Compute L0 and L1 from TopoNetX, return dense arrays."""
    L0 = cc.hodge_laplacian_matrix(0).toarray().astype(float)
    L1 = cc.hodge_laplacian_matrix(1).toarray().astype(float)
    return L0, L1


def count_zero_eigenvalues(M, tol=1e-8):
    """Count eigenvalues within tol of zero."""
    evals = np.linalg.eigvalsh(M)
    return int(np.sum(np.abs(evals) < tol)), evals.tolist()


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  5. DISCRETE CALCULUS                                             ║
# ╚═══════════════════════════════════════════════════════════════════╝

def discrete_gradient(B1, vertex_signal):
    """grad: vertex -> edge  =  B1^T @ signal."""
    return B1.T @ vertex_signal


def discrete_curl(B2, edge_signal):
    """curl: edge -> face  =  B2^T @ signal."""
    if B2.shape[1] == 0:
        return np.array([])
    return B2.T @ edge_signal


def verify_curl_grad_zero(B1, B2, vertex_signal):
    """curl(grad(f)) = B2^T @ B1^T @ f = (B1 @ B2)^T @ f = 0."""
    grad = discrete_gradient(B1, vertex_signal)
    curl_of_grad = discrete_curl(B2, grad)
    if len(curl_of_grad) == 0:
        return True, 0.0
    max_err = float(np.max(np.abs(curl_of_grad)))
    return max_err < 1e-10, max_err


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  6. PyG GRAPH CONSTRUCTION                                       ║
# ╚═══════════════════════════════════════════════════════════════════╝

def cell_complex_to_pyg(cc: CellComplex) -> Data:
    """Convert a CellComplex to a PyG Data object (1-skeleton graph)."""
    node_list = sorted(cc.nodes)
    node_map = {n: i for i, n in enumerate(node_list)}

    src, dst = [], []
    for e in cc.edges:
        u, v = e
        i, j = node_map[u], node_map[v]
        src.extend([i, j])
        dst.extend([j, i])

    edge_index = torch.tensor([src, dst], dtype=torch.long)
    x = torch.zeros(len(node_list), 1)
    return Data(x=x, edge_index=edge_index, num_nodes=len(node_list))


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  7. MESSAGE PASSING                                               ║
# ╚═══════════════════════════════════════════════════════════════════╝

class SumPropagation(MessagePassing):
    """Simple sum-aggregation message passing."""

    def __init__(self):
        super().__init__(aggr="add")

    def forward(self, x, edge_index):
        return self.propagate(edge_index, x=x)

    def message(self, x_j):
        return x_j


def run_message_passing(data: Data, seed_node: int = 0, rounds: int = 10):
    """Seed one node with signal=1.0, propagate for `rounds` steps.
    Returns per-round stats: fraction of nodes reached, max signal."""
    mp = SumPropagation()
    x = data.x.clone()
    x[seed_node, 0] = 1.0

    history = []
    for r in range(rounds):
        x = mp(x, data.edge_index)
        reached = int((x[:, 0] > 1e-12).sum().item())
        history.append({
            "round": r + 1,
            "nodes_reached": reached,
            "fraction_reached": round(reached / data.num_nodes, 4),
            "max_signal": round(float(x[:, 0].max().item()), 6),
            "total_signal": round(float(x[:, 0].sum().item()), 6),
        })
    return history


# ╔═══════════════════════════════════════════════════════════════════╗
# ║  MAIN DRIVER                                                     ║
# ╚═══════════════════════════════════════════════════════════════════╝

def analyse_complex(name, cc, expected_betti):
    """Run full analysis pipeline on one cell complex."""
    result = {"name": name}

    # -- counts --
    V = len(list(cc.nodes))
    E = len(list(cc.edges))
    F = len(list(cc.cells))
    euler = V - E + F
    result["counts"] = {"V": V, "E": E, "F": F, "euler_chi": euler}

    # -- incidence --
    B1, B2 = get_incidence(cc)
    chain_ok, chain_err = verify_chain_complex(B1, B2)
    result["incidence"] = {
        "B1_shape": list(B1.shape),
        "B2_shape": list(B2.shape),
        "B1_B2_zero": chain_ok,
        "B1_B2_max_error": chain_err,
    }

    # -- Betti (rank-nullity) --
    betti, rank_info = compute_betti_rank_nullity(B1, B2)
    betti_match = betti == expected_betti
    result["betti"] = {
        "computed": betti,
        "expected": expected_betti,
        "match": betti_match,
        "rank_info": rank_info,
    }

    # -- Hodge Laplacians --
    L0, L1 = hodge_laplacians(cc)
    b0_hodge, L0_evals = count_zero_eigenvalues(L0)
    b1_hodge, L1_evals = count_zero_eigenvalues(L1)
    result["hodge"] = {
        "L0_shape": list(L0.shape),
        "L1_shape": list(L1.shape),
        "L0_zero_evals": b0_hodge,
        "L1_zero_evals": b1_hodge,
        "b0_hodge_matches": b0_hodge == expected_betti[0],
        "b1_hodge_matches": b1_hodge == expected_betti[1],
        "L0_spectrum_sample": [round(x, 8) for x in sorted(L0_evals)[:6]],
        "L1_spectrum_sample": [round(x, 8) for x in sorted(L1_evals)[:6]],
    }

    # -- Discrete calculus --
    vertex_signal = np.random.RandomState(42).randn(V)
    cg_ok, cg_err = verify_curl_grad_zero(B1, B2, vertex_signal)
    grad = discrete_gradient(B1, vertex_signal)
    result["discrete_calculus"] = {
        "curl_grad_zero": cg_ok,
        "curl_grad_max_error": cg_err,
        "gradient_norm": round(float(np.linalg.norm(grad)), 6),
    }

    # -- PyG graph --
    data = cell_complex_to_pyg(cc)
    pyg_nodes = data.num_nodes
    pyg_edges = data.edge_index.shape[1] // 2  # undirected
    result["pyg_graph"] = {
        "num_nodes": pyg_nodes,
        "num_edges_undirected": pyg_edges,
        "nodes_match_V": pyg_nodes == V,
        "edges_match_E": pyg_edges == E,
    }

    # -- Message passing --
    mp_history = run_message_passing(data, seed_node=0, rounds=10)
    result["message_passing"] = {
        "seed_node": 0,
        "rounds": 10,
        "final_fraction_reached": mp_history[-1]["fraction_reached"],
        "history": mp_history,
    }

    return result


def main():
    results = {
        "probe": "sim_pure_lego_topology_graphs",
        "timestamp": datetime.now(UTC).isoformat(),
        "description": "Topology + graph lego: cell complexes, Betti, Hodge, "
                       "discrete calculus, PyG message passing. No engine.",
        "complexes": {},
        "verdicts": {},
    }

    builders = [
        ("circle_S1", build_circle, [1, 1, 0]),
        ("sphere_S2", build_sphere, [1, 0, 1]),
        ("torus_T2", build_torus, [1, 2, 1]),
    ]

    all_pass = True
    for name, builder, expected_betti in builders:
        cc = builder()
        analysis = analyse_complex(name, cc, expected_betti)
        results["complexes"][name] = analysis

        # Verdict per complex
        ok = (
            analysis["incidence"]["B1_B2_zero"]
            and analysis["betti"]["match"]
            and analysis["hodge"]["b0_hodge_matches"]
            and analysis["hodge"]["b1_hodge_matches"]
            and analysis["discrete_calculus"]["curl_grad_zero"]
            and analysis["pyg_graph"]["nodes_match_V"]
            and analysis["pyg_graph"]["edges_match_E"]
        )
        results["verdicts"][name] = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False

    # -- Nested tori --
    merged, offset = build_nested_tori()
    nested_analysis = analyse_complex("nested_tori", merged, [2, 4, 2])
    results["complexes"]["nested_tori"] = nested_analysis
    nested_ok = (
        nested_analysis["incidence"]["B1_B2_zero"]
        and nested_analysis["betti"]["match"]
        and nested_analysis["discrete_calculus"]["curl_grad_zero"]
        and nested_analysis["pyg_graph"]["nodes_match_V"]
        and nested_analysis["pyg_graph"]["edges_match_E"]
    )
    results["verdicts"]["nested_tori"] = "PASS" if nested_ok else "FAIL"
    if not nested_ok:
        all_pass = False

    results["overall_verdict"] = "ALL PASS" if all_pass else "SOME FAIL"

    # ── write ────────────────────────────────────────────────────
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    # ── console summary ──────────────────────────────────────────
    print("=" * 72)
    print("  PURE LEGO TOPOLOGY + GRAPH RESULTS")
    print("=" * 72)
    for name, verdict in results["verdicts"].items():
        tag = "PASS" if verdict == "PASS" else "FAIL"
        c = results["complexes"][name]
        counts = c["counts"]
        betti = c["betti"]["computed"]
        mp_final = c["message_passing"]["final_fraction_reached"]
        print(f"  [{tag}] {name:16s}  V={counts['V']}  E={counts['E']}  "
              f"F={counts['F']}  chi={counts['euler_chi']}  "
              f"betti={betti}  mp_spread={mp_final}")
    print("-" * 72)
    print(f"  OVERALL: {results['overall_verdict']}")
    print(f"  Results -> {RESULTS_PATH}")
    print("=" * 72)


if __name__ == "__main__":
    main()
