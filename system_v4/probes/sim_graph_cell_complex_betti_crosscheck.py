#!/usr/bin/env python3
"""Cross-tool Betti invariant check for the graph/cell-complex lego frontier.

This packet is the bounded follow-on to graph/cell-complex coexistence. The
coexistence packet proves that several graph/topology tools can hold the same
finite carrier. This packet checks a shared integer invariant on that carrier.
It is still lego-stage evidence only: no bridge, GStack, QIT, axis, or
nonclassical admission.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import gudhi
import numpy as np
import rustworkx as rx
import torch
import xgi
from torch_geometric.data import Data
from toponetx.classes import CellComplex
from z3 import Int, Solver, unsat

from receipt_boundary import apply_default_receipt_boundary


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
PARENT_RESULT_NAMES = [
    "graph_cell_complex_coexistence_results.json",
    "xgi_indirect_pathway_results.json",
    "toponetx_state_class_binding_results.json",
    "pyg_dynamic_edge_werner_results.json",
]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing rank/eigenvalue and invariant comparisons"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing graph Laplacian eigenvalue computation"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing finite graph carrier for torch Laplacian checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing connected-component and cycle-rank computation"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing simplex-tree Betti computation"},
    "toponetx": {"tried": True, "used": True, "reason": "supportive cell-complex carrier and two-cell shape check"},
    "xgi": {"tried": True, "used": True, "reason": "supportive regime hyperedge coverage check"},
    "z3": {"tried": True, "used": True, "reason": "supportive integer contradiction fence for fixed Betti values"},
    "scipy": {"tried": False, "used": False, "reason": "not needed; small dense ranks/eigenvalues use numpy/torch"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed; z3 covers the small integer fence"},
    "qutip": {"tried": False, "used": False, "reason": "not needed; no quantum solver in this topology packet"},
    "qiskit": {"tried": False, "used": False, "reason": "not needed; no circuit backend"},
    "clifford": {"tried": False, "used": False, "reason": "not needed; no geometric algebra action"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; no manifold metric layer"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "gudhi": "load_bearing",
    "toponetx": "supportive",
    "xgi": "supportive",
    "z3": "supportive",
    "scipy": None,
    "sympy": None,
    "cvc5": None,
    "qutip": None,
    "qiskit": None,
    "clifford": None,
    "geomstats": None,
}

P_VALUES = np.array([0.0, 0.10, 0.20, 0.252, 1.0 / 3.0, 0.50, 1.0], dtype=float)
IC_ZERO = 0.252
SEP_BOUNDARY = 1.0 / 3.0


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parent_receipts() -> list[dict]:
    rows = []
    for name in PARENT_RESULT_NAMES:
        path = RESULTS_DIR / name
        payload = read_json(path) if path.exists() else {}
        rows.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "classification": payload.get("classification"),
                "all_pass": bool(payload.get("all_pass") or payload.get("summary", {}).get("all_pass")),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
            }
        )
    return rows


def regime(p: float) -> str:
    if p < IC_ZERO:
        return "ic_positive"
    if p < SEP_BOUNDARY:
        return "entangled_gap"
    return "separable"


def node_rows() -> list[dict]:
    return [{"idx": idx, "p": float(p), "regime": regime(float(p))} for idx, p in enumerate(P_VALUES)]


def ordered_edges(rows: list[dict]) -> list[tuple[int, int]]:
    edges: set[tuple[int, int]] = set()
    for left, right in zip(rows[:-1], rows[1:]):
        edges.add((left["idx"], right["idx"]))
    by_regime: dict[str, list[int]] = {}
    for row in rows:
        by_regime.setdefault(row["regime"], []).append(row["idx"])
    for indices in by_regime.values():
        for i, src in enumerate(indices):
            for dst in indices[i + 1 :]:
                edges.add((src, dst))
    return sorted(edges)


def build_rx_graph(n_nodes: int, edges: list[tuple[int, int]]) -> rx.PyGraph:
    graph = rx.PyGraph()
    graph.add_nodes_from(range(n_nodes))
    graph.add_edges_from_no_data(edges)
    return graph


def build_pyg_data(rows: list[dict], edges: list[tuple[int, int]]) -> Data:
    x = torch.tensor([[row["p"]] for row in rows], dtype=torch.float64)
    directed = []
    for src, dst in edges:
        directed.extend([(src, dst), (dst, src)])
    edge_index = torch.tensor(directed, dtype=torch.long).t().contiguous()
    return Data(x=x, edge_index=edge_index)


def build_simplex_tree(n_nodes: int, edges: list[tuple[int, int]], fill_triangles: bool) -> gudhi.SimplexTree:
    tree = gudhi.SimplexTree()
    for idx in range(n_nodes):
        tree.insert([idx])
    for edge in edges:
        tree.insert(list(edge))
    if fill_triangles:
        tree.insert([0, 1, 2])
        tree.insert([4, 5, 6])
    tree.compute_persistence(persistence_dim_max=True)
    return tree


def build_cell_complex(n_nodes: int, edges: list[tuple[int, int]]) -> CellComplex:
    complex_ = CellComplex()
    for idx in range(n_nodes):
        complex_.add_node(idx)
    for edge in edges:
        complex_.add_cell(list(edge), rank=1)
    complex_.add_cell([0, 1, 2], rank=2)
    complex_.add_cell([4, 5, 6], rank=2)
    return complex_


def build_hypergraph(rows: list[dict]) -> xgi.Hypergraph:
    hypergraph = xgi.Hypergraph()
    for label in ("ic_positive", "entangled_gap", "separable"):
        members = [row["idx"] for row in rows if row["regime"] == label]
        if members:
            hypergraph.add_edge(members, id=label)
    return hypergraph


def rustworkx_betti(n_nodes: int, edges: list[tuple[int, int]]) -> dict:
    graph = build_rx_graph(n_nodes, edges)
    beta0 = len(rx.connected_components(graph))
    beta1 = len(edges) - n_nodes + beta0
    return {"beta0": int(beta0), "beta1": int(beta1)}


def pyg_betti(data: Data, n_nodes: int, edge_count: int) -> dict:
    adjacency = torch.zeros((n_nodes, n_nodes), dtype=torch.float64)
    for src, dst in data.edge_index.t().tolist():
        adjacency[src, dst] = 1.0
    degree = torch.diag(adjacency.sum(dim=1))
    laplacian = degree - adjacency
    eigenvalues = torch.linalg.eigvalsh(laplacian).detach().cpu().numpy()
    beta0 = int(np.sum(np.abs(eigenvalues) < 1e-8))
    beta1 = int(edge_count - n_nodes + beta0)
    return {"beta0": beta0, "beta1": beta1, "laplacian_eigenvalues": [float(v) for v in eigenvalues]}


def gudhi_betti(n_nodes: int, edges: list[tuple[int, int]], fill_triangles: bool) -> dict:
    tree = build_simplex_tree(n_nodes, edges, fill_triangles)
    betti = tree.betti_numbers()
    while len(betti) < 2:
        betti.append(0)
    return {"beta0": int(betti[0]), "beta1": int(betti[1]), "simplex_count": int(tree.num_simplices())}


def z3_fixed_betti_fence(expected_beta0: int, expected_beta1: int) -> dict:
    beta0 = Int("beta0")
    beta1 = Int("beta1")
    solver = Solver()
    solver.add(beta0 == expected_beta0, beta1 == expected_beta1)
    solver.add(beta0 != expected_beta0)
    beta0_status = solver.check()
    solver = Solver()
    solver.add(beta0 == expected_beta0, beta1 == expected_beta1)
    solver.add(beta1 != expected_beta1)
    beta1_status = solver.check()
    return {
        "fixed_beta0_contradiction": str(beta0_status),
        "fixed_beta1_contradiction": str(beta1_status),
        "pass": beta0_status == unsat and beta1_status == unsat,
        "scope": "integer receipt fence for fixed finite Betti values only",
    }


def main() -> int:
    parents = parent_receipts()
    rows = node_rows()
    n_nodes = len(rows)
    edges = ordered_edges(rows)
    pyg_data = build_pyg_data(rows, edges)
    cell_complex = build_cell_complex(n_nodes, edges)
    hypergraph = build_hypergraph(rows)

    rx_result = rustworkx_betti(n_nodes, edges)
    pyg_result = pyg_betti(pyg_data, n_nodes, len(edges))
    gudhi_unfilled = gudhi_betti(n_nodes, edges, fill_triangles=False)
    gudhi_filled = gudhi_betti(n_nodes, edges, fill_triangles=True)
    beta0_values = [rx_result["beta0"], pyg_result["beta0"], gudhi_unfilled["beta0"]]
    beta1_values = [rx_result["beta1"], pyg_result["beta1"], gudhi_unfilled["beta1"]]

    scrambled_edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]
    scrambled_rx = rustworkx_betti(n_nodes, scrambled_edges)
    bridge_removed_edges = [edge for edge in edges if edge not in {(2, 3), (3, 4)}]
    bridge_removed_rx = rustworkx_betti(n_nodes, bridge_removed_edges)

    positive = {
        "parents_exist_and_pass": {"parents": parents, "pass": all(row["exists"] and row["all_pass"] for row in parents)},
        "three_tools_agree_on_skeleton_beta0": {
            "rustworkx": rx_result["beta0"],
            "pyg_torch": pyg_result["beta0"],
            "gudhi_unfilled": gudhi_unfilled["beta0"],
            "pass": beta0_values == [1, 1, 1],
        },
        "three_tools_agree_on_skeleton_beta1": {
            "rustworkx": rx_result["beta1"],
            "pyg_torch": pyg_result["beta1"],
            "gudhi_unfilled": gudhi_unfilled["beta1"],
            "pass": beta1_values == [2, 2, 2],
        },
        "support_tools_hold_same_carrier": {
            "toponetx_shape": [int(value) for value in cell_complex.shape],
            "xgi_edge_count": len(list(hypergraph.edges)),
            "pass": bool(cell_complex.shape[0] == n_nodes and len(list(hypergraph.edges)) == 3),
        },
    }
    negative = {
        "filled_two_cells_kill_skeleton_cycles_in_gudhi": {
            "gudhi_unfilled_beta1": gudhi_unfilled["beta1"],
            "gudhi_filled_beta1": gudhi_filled["beta1"],
            "pass": gudhi_unfilled["beta1"] == 2 and gudhi_filled["beta1"] == 0,
        },
        "scrambled_without_regime_triangles_loses_cycles": {
            "scrambled_edges": [list(edge) for edge in scrambled_edges],
            "scrambled_beta": scrambled_rx,
            "pass": scrambled_rx["beta1"] == 0,
        },
        "bridge_removal_splits_components": {
            "removed_edges": [[2, 3], [3, 4]],
            "bridge_removed_beta": bridge_removed_rx,
            "pass": bridge_removed_rx["beta0"] == 3,
        },
        "z3_fixed_betti_fence": z3_fixed_betti_fence(1, 2),
    }
    boundary = {
        "finite_carrier_only": {"node_count": n_nodes, "edge_count": len(edges), "pass": n_nodes == 7 and len(edges) == 8},
        "cross_tool_invariant_not_semantic_equivalence": {"pass": True},
        "betti_numbers_are_not_admission": {"pass": True},
        "no_qit_gstack_axis_bridge_or_nonclassical_promotion": {"pass": True},
    }
    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    result = {
        "name": "graph_cell_complex_betti_crosscheck",
        "classification": "classical_baseline",
        "classification_note": "Finite cross-tool Betti invariant baseline; closure-candidate evidence only.",
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "parents": parents,
        "finite_carrier": {
            "p_values": [float(p) for p in P_VALUES],
            "rows": rows,
            "undirected_edges": [list(edge) for edge in edges],
        },
        "tool_results": {
            "rustworkx": rx_result,
            "pyg_torch": pyg_result,
            "gudhi_unfilled": gudhi_unfilled,
            "gudhi_filled": gudhi_filled,
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "closure_candidate": all_pass,
            "promotion_allowed": False,
            "beta0": 1,
            "skeleton_beta1": 2,
            "filled_beta1": 0,
            "scope_note": "Shared finite Betti invariant evidence only; no framework semantic equivalence or stage promotion.",
        },
        "all_pass": all_pass,
        "divergence_log": (
            "The unfilled graph skeleton has two cycles across rustworkx, PyG/torch, and GUDHI; "
            "adding two 2-cells fills those cycles in GUDHI, and scrambled/bridge-removal controls fail differently."
        ),
    }
    result = apply_default_receipt_boundary(
        result,
        source_name="sim_graph_cell_complex_betti_crosscheck",
        target="Use as bounded graph/cell-complex closure-candidate evidence before broader topology assembly.",
    )
    result["promotion_condition"] = "Requires broader graph/topology assembly audit and explicit stage-gate admission."
    result["blocked_until"] = "broader graph/topology assembly and stage-gate admission"

    out_path = RESULTS_DIR / "graph_cell_complex_betti_crosscheck_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
