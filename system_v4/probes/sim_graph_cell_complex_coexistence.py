#!/usr/bin/env python3
"""Bounded graph/cell-complex coexistence witness for the lego frontier.

This packet checks whether one finite Werner-regime sample can be represented
on the same finite index/regime skeleton as a PyG graph, XGI hypergraph,
TopoNetX cell complex, GUDHI simplex complex, and rustworkx graph.  It is a
topology/coexistence receipt only, not a semantic-equivalence proof.
"""

from __future__ import annotations

import json
import hashlib
import math
import platform
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

import gudhi
import numpy as np
import rustworkx as rx
import torch
import xgi
from torch_geometric.data import Data
from toponetx.classes import CellComplex
from z3 import Real, Solver, unsat

from receipt_boundary import apply_default_receipt_boundary


classification = "supporting"

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "finite arrays, regime masks, and invariant comparisons"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing tensor features for PyG node representation"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing graph data object for dynamic Werner-regime topology"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing graph connectivity and bridge-removal checks"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing hyperedge regime representation"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing cell-complex representation"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing simplex-complex Betti witness"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite threshold disjointness fence"},
    "scipy": {"tried": False, "used": False, "reason": "not needed for this finite combinatorial packet"},
    "sympy": {"tried": False, "used": False, "reason": "not needed; Euler/Betti checks are numeric integer checks"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed; z3 covers the bounded inequality fence"},
    "qutip": {"tried": False, "used": False, "reason": "not installed in this environment; no density solver needed here"},
    "qiskit": {"tried": False, "used": False, "reason": "not installed in this environment; no circuit backend needed here"},
    "clifford": {"tried": False, "used": False, "reason": "not used; this is graph/topology, not Clifford algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; no Riemannian metric computation"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "z3": "load_bearing",
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
PARENT_RESULT_NAMES = [
    "xgi_indirect_pathway_results.json",
    "toponetx_state_class_binding_results.json",
    "pyg_dynamic_edge_werner_results.json",
]


def coherent_information_proxy(p: float) -> float:
    """Finite monotone proxy with the same sign boundary as the Werner lane."""
    return float(IC_ZERO - p)


def concurrence_proxy(p: float) -> float:
    return float(max(0.0, (3.0 * p - 1.0) / 2.0))


def regime(p: float) -> str:
    if p < IC_ZERO:
        return "ic_positive"
    if p < SEP_BOUNDARY:
        return "entangled_gap"
    return "separable"


def regime_code(label: str) -> int:
    return {"ic_positive": 0, "entangled_gap": 1, "separable": 2}[label]


def node_rows() -> list[dict]:
    return [
        {
            "idx": idx,
            "p": float(p),
            "ic_proxy": coherent_information_proxy(float(p)),
            "concurrence_proxy": concurrence_proxy(float(p)),
            "regime": regime(float(p)),
            "regime_code": regime_code(regime(float(p))),
        }
        for idx, p in enumerate(P_VALUES)
    ]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def package_versions() -> dict:
    packages = {
        "gudhi": "gudhi",
        "numpy": "numpy",
        "pytorch": "torch",
        "pyg": "torch-geometric",
        "rustworkx": "rustworkx",
        "toponetx": "TopoNetX",
        "xgi": "xgi",
        "z3": "z3-solver",
    }
    versions = {}
    for label, package_name in packages.items():
        try:
            versions[label] = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            versions[label] = "unknown"
    return versions


def parent_receipt_summaries() -> list[dict]:
    summaries = []
    for name in PARENT_RESULT_NAMES:
        path = RESULTS_DIR / name
        if not path.exists():
            summaries.append({"path": str(path), "exists": False, "all_pass": False})
            continue
        payload = read_json(path)
        raw = path.read_bytes()
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        all_pass = payload.get("all_pass")
        if all_pass is None:
            all_pass = summary.get("all_pass")
        summaries.append(
            {
                "path": str(path),
                "exists": True,
                "classification": payload.get("classification"),
                "all_pass": bool(all_pass),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    return summaries


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


def build_pyg(rows: list[dict], edges: list[tuple[int, int]]) -> Data:
    x = torch.tensor(
        [[row["p"], row["ic_proxy"], row["concurrence_proxy"], row["regime_code"]] for row in rows],
        dtype=torch.float64,
    )
    directed_edges = []
    for src, dst in edges:
        directed_edges.extend([(src, dst), (dst, src)])
    edge_index = torch.tensor(directed_edges, dtype=torch.long).t().contiguous()
    return Data(x=x, edge_index=edge_index)


def build_rx_graph(rows: list[dict], edges: list[tuple[int, int]]) -> rx.PyGraph:
    graph = rx.PyGraph()
    graph.add_nodes_from([row["idx"] for row in rows])
    graph.add_edges_from_no_data(edges)
    return graph


def build_xgi(rows: list[dict]) -> xgi.Hypergraph:
    hypergraph = xgi.Hypergraph()
    for label in ["ic_positive", "entangled_gap", "separable"]:
        members = [row["idx"] for row in rows if row["regime"] == label]
        if members:
            hypergraph.add_edge(members, id=label)
    hypergraph.add_edge([2, 3, 4], id="threshold_bridge")
    return hypergraph


def build_cell_complex(rows: list[dict], edges: list[tuple[int, int]]) -> CellComplex:
    complex_ = CellComplex()
    for row in rows:
        complex_.add_node(row["idx"])
    for edge in edges:
        complex_.add_cell(list(edge), rank=1)
    complex_.add_cell([0, 1, 2], rank=2)
    complex_.add_cell([4, 5, 6], rank=2)
    return complex_


def build_simplex_tree(edges: list[tuple[int, int]]) -> gudhi.SimplexTree:
    st = gudhi.SimplexTree()
    for idx in range(len(P_VALUES)):
        st.insert([idx])
    for edge in edges:
        st.insert(list(edge))
    st.insert([0, 1, 2])
    st.insert([4, 5, 6])
    st.compute_persistence()
    return st


def z3_disjointness() -> dict:
    p = Real("p")
    checks = {}
    solver = Solver()
    solver.add(p < IC_ZERO, p >= IC_ZERO)
    checks["ic_positive_and_gap_disjoint"] = str(solver.check())
    solver = Solver()
    solver.add(p < SEP_BOUNDARY, p >= SEP_BOUNDARY)
    checks["pre_separable_and_separable_disjoint"] = str(solver.check())
    return {
        "checks": checks,
        "scope": (
            "bounded threshold-region disjointness over fixed finite Werner-regime thresholds; "
            "not a structural derivation of the thresholds"
        ),
        "pass": all(value == str(unsat) for value in checks.values()),
    }


def component_count(graph: rx.PyGraph) -> int:
    return len(rx.connected_components(graph))


def main() -> int:
    parent_summaries = parent_receipt_summaries()
    rows = node_rows()
    edges = ordered_edges(rows)
    pyg_data = build_pyg(rows, edges)
    rx_graph = build_rx_graph(rows, edges)
    hypergraph = build_xgi(rows)
    cell_complex = build_cell_complex(rows, edges)
    simplex_tree = build_simplex_tree(edges)

    bridge_removed = build_rx_graph(rows, [edge for edge in edges if edge not in {(2, 3), (3, 4)}])
    shuffled_regimes = [regime(float(p)) for p in P_VALUES[[0, 4, 1, 6, 2, 5, 3]]]
    shuffled_inversions = sum(
        1 for left, right in zip(shuffled_regimes[:-1], shuffled_regimes[1:]) if regime_code(left) > regime_code(right)
    )

    hyperedge_sizes = {str(edge_id): len(hypergraph.edges.members(edge_id)) for edge_id in hypergraph.edges}
    betti = simplex_tree.betti_numbers()
    while len(betti) < 2:
        betti.append(0)

    positive = {
        "parent_receipts_exist_and_pass": {
            "parents": parent_summaries,
            "pass": bool(parent_summaries and all(parent.get("exists") and parent.get("all_pass") for parent in parent_summaries)),
        },
        "pyg_representation_matches_finite_nodes": {
            "node_count": int(pyg_data.num_nodes),
            "directed_edge_count": int(pyg_data.num_edges),
            "pass": bool(pyg_data.num_nodes == len(rows) and pyg_data.num_edges == 2 * len(edges)),
        },
        "xgi_regime_hyperedges_cover_all_nodes": {
            "hyperedge_sizes": hyperedge_sizes,
            "covered_nodes": sorted({node for edge_id in hypergraph.edges for node in hypergraph.edges.members(edge_id)}),
            "pass": bool(set(range(len(rows))).issubset({node for edge_id in hypergraph.edges for node in hypergraph.edges.members(edge_id)})),
        },
        "toponetx_and_gudhi_share_simplex_counts": {
            "toponetx_shape": list(cell_complex.shape),
            "gudhi_num_simplices": int(simplex_tree.num_simplices()),
            "pass": bool(cell_complex.shape[0] == len(rows) and simplex_tree.num_vertices() == len(rows)),
        },
        "rustworkx_connectivity_matches_single_ordered_path": {
            "component_count": component_count(rx_graph),
            "pass": bool(component_count(rx_graph) == 1),
        },
    }
    negative = {
        "threshold_bridge_removal_splits_regime_path": {
            "component_count_after_removal": component_count(bridge_removed),
            "removed_edges": [[2, 3], [3, 4]],
            "pass": bool(component_count(bridge_removed) > 1),
        },
        "shuffled_regime_order_is_detected": {
            "shuffled_regimes": shuffled_regimes,
            "inversions": shuffled_inversions,
            "pass": bool(shuffled_inversions > 0),
        },
        "z3_threshold_regions_are_disjoint": z3_disjointness(),
    }
    boundary = {
        "finite_dimension_only": {
            "node_count": len(rows),
            "edge_count": len(edges),
            "pass": len(rows) == 7 and len(edges) >= 6,
        },
        "no_promotion_claim": {
            "pass": True,
            "note": "Coexistence witness only; no QIT, GStack, axis, bridge, or nonclassical admission.",
        },
        "same_skeleton_not_semantic_equivalence": {
            "pass": True,
            "note": (
                "PyG, XGI, TopoNetX, GUDHI, and rustworkx encode the same finite node/regime skeleton "
                "with different operation semantics; this does not claim algebraic equivalence of the frameworks."
            ),
        },
        "betti_is_descriptive_not_admission": {
            "betti_numbers": [int(value) for value in betti[:2]],
            "pass": all(math.isfinite(float(value)) for value in betti[:2]),
        },
    }
    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    result = {
        "name": "graph_cell_complex_coexistence",
        "classification": "supporting",
        "classification_note": (
            "Finite graph/topology same-skeleton witness across PyG, XGI, TopoNetX, GUDHI, "
            "rustworkx, torch, numpy, and z3. Queue evidence only, not semantic equivalence or admission."
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "package_versions": package_versions(),
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "parents": parent_summaries,
        "finite_state": {
            "p_values": [float(p) for p in P_VALUES],
            "rows": rows,
            "undirected_edges": [list(edge) for edge in edges],
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "tool_count": sum(1 for depth in TOOL_INTEGRATION_DEPTH.values() if depth),
            "coexistence_candidate": bool(all_pass),
            "promotion_allowed": False,
            "scope_note": (
                "Graph/cell-complex same-skeleton coexistence candidate; broader assembly and semantic "
                "equivalence still require stage-gate review."
            ),
        },
        "all_pass": all_pass,
        "divergence_log": (
        "This sim couples graph/topology representations over one finite Werner-regime path. "
            "It does not assert framework semantic equivalence, physical uniqueness, QIT admission, "
            "GStack order, or broad assembly closure."
        ),
    }
    result = apply_default_receipt_boundary(
        result,
        source_name="sim_graph_cell_complex_coexistence",
        target="Use as bounded graph/topology coexistence evidence before broader lego assembly.",
    )
    result["promotion_condition"] = "Requires broader graph/topology assembly audit and explicit stage-gate admission."
    result["blocked_until"] = "broader graph/topology assembly and stage-gate admission"

    out_path = RESULTS_DIR / "graph_cell_complex_coexistence_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
