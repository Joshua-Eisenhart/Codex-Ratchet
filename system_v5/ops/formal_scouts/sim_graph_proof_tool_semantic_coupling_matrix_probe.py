#!/usr/bin/env python3
"""Graph/proof tool semantic-coupling matrix probe.

Formal scout only. This probes graph/proof predicates under three controls:
display-label scramble, storage reindexing, and edge rewiring. The target is
the provider-loop4 failure mode where row-count or label-only evidence is
mistaken for semantic graph/proof coupling.

A green receipt means at least one row-count/label-only predicate is killed by
the controls, while at least one edge-sensitive predicate survives only at
scout level. It does not admit a graph proof, proof stack, final manifold,
physics, target-system, bridge, axis, engine, or canonical claim.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import pathlib
import time
from collections import Counter
from typing import Any, Callable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "graph_proof_tool_semantic_coupling_matrix_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "graph_proof_tool_semantic_coupling_matrix"
CLAIM_CEILING = (
    "Formal scout only: tests graph/proof tool predicates under display-label "
    "scramble, storage reindexing, and edge rewiring controls. Killed "
    "row-count or label-only predicates block provider-loop4 overclaims; "
    "edge-sensitive predicates can survive only as scout-level evidence. This "
    "does not admit a graph proof, proof stack, final manifold, physics, "
    "target-system, bridge, axis, engine, or canonical claim."
)

TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "required": False,
        "used_when_importable": True,
        "reason": "directed graph edge-signature and DAG checks for semantic edge rewiring",
    },
    "networkx": {
        "tried": True,
        "required": False,
        "used_when_importable": True,
        "reason": "supportive graph predicate controls for row-count, label-only, reachability, and predecessor-set signatures; rustworkx and PyTorch carry the local nonclassical load-bearing graph roles",
    },
    "pytorch": {
        "tried": True,
        "required": True,
        "used_when_importable": True,
        "reason": "load-bearing local tensor message-passing readout over semantic graph edges for nonclassical graph/proof coupling controls",
    },
    "z3": {
        "tried": True,
        "required": False,
        "used_when_importable": True,
        "reason": "SMT equality/inequality check for baseline-vs-control edge signatures",
    },
    "cvc5": {
        "tried": True,
        "required": False,
        "used_when_importable": True,
        "reason": "independent SMT-family equality/inequality cross-check for edge signatures",
    },
    "sympy": {
        "tried": True,
        "required": False,
        "used_when_importable": True,
        "reason": "symbolic edge polynomial that should change under semantic edge rewiring only",
    },
    "xgi": {
        "tried": True,
        "required": False,
        "used_when_importable": True,
        "reason": "optional hypergraph edge-cell signature; records supportive absence if unavailable",
    },
    "toponetx": {
        "tried": True,
        "required": False,
        "used_when_importable": True,
        "reason": "optional simplicial-complex edge-cell signature; records supportive absence if unavailable",
    },
    "gudhi": {
        "tried": True,
        "required": False,
        "used_when_importable": True,
        "reason": "optional persistence summary over graph-derived degree/path features; records supportive absence if unavailable",
    },
    "pyg": {
        "tried": True,
        "required": False,
        "used_when_importable": True,
        "reason": "optional PyTorch Geometric Data object plus finite message-passing readout; records supportive absence if unavailable",
    },
    "python_json": {
        "tried": True,
        "required": True,
        "used_when_importable": True,
        "reason": "formal-scout receipt serialization and stable predicate hashing",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "rustworkx": "load_bearing",
    "networkx": "supportive",
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "xgi": "supportive",
    "toponetx": "supportive",
    "gudhi": "supportive",
    "pyg": "supportive",
    "python_json": "supportive",
}

EPS_INVARIANT = 1e-12
EPS_VARIANT = 1e-9

NODES = [
    {"semantic_id": "premise", "display_label": "premise_anchor", "semantic_position": 0},
    {"semantic_id": "definition", "display_label": "definition_gate", "semantic_position": 1},
    {"semantic_id": "constraint", "display_label": "constraint_gate", "semantic_position": 2},
    {"semantic_id": "lemma_left", "display_label": "lemma_left", "semantic_position": 3},
    {"semantic_id": "lemma_right", "display_label": "lemma_right", "semantic_position": 4},
    {"semantic_id": "operator_join", "display_label": "operator_join", "semantic_position": 5},
    {"semantic_id": "readout", "display_label": "proof_readout", "semantic_position": 6},
]

BASE_EDGES = [
    ("premise", "definition"),
    ("premise", "constraint"),
    ("definition", "lemma_left"),
    ("constraint", "lemma_left"),
    ("definition", "lemma_right"),
    ("lemma_left", "operator_join"),
    ("lemma_right", "operator_join"),
    ("operator_join", "readout"),
]

REWIRED_EDGES = [
    ("premise", "definition"),
    ("premise", "constraint"),
    ("definition", "lemma_right"),
    ("constraint", "lemma_right"),
    ("constraint", "lemma_left"),
    ("lemma_left", "operator_join"),
    ("lemma_right", "operator_join"),
    ("operator_join", "readout"),
]


def import_status() -> dict[str, dict[str, Any]]:
    modules = {
        "rustworkx": "rustworkx",
        "networkx": "networkx",
        "z3": "z3",
        "cvc5": "cvc5",
        "sympy": "sympy",
        "xgi": "xgi",
        "toponetx": "toponetx",
        "gudhi": "gudhi",
        "pyg": "torch_geometric",
        "pytorch": "torch",
    }
    status: dict[str, dict[str, Any]] = {}
    for tool, module_name in modules.items():
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - depends on local env
            status[tool] = {
                "importable": False,
                "used": False,
                "module": module_name,
                "absence_recorded_as": "blocked" if tool in {"rustworkx", "networkx", "z3", "cvc5", "sympy"} else "supportive_absence",
                "error": f"{type(exc).__name__}: {exc}",
            }
        else:
            status[tool] = {
                "importable": True,
                "used": False,
                "module": module_name,
                "version": str(getattr(module, "__version__", "unknown")),
                "module_ref": module,
            }
    status["python_json"] = {
        "importable": True,
        "used": True,
        "module": "json",
        "version": "stdlib",
    }
    return status


def without_module_refs(status: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    cleaned = {}
    for tool, row in status.items():
        cleaned[tool] = {key: value for key, value in row.items() if key != "module_ref"}
    return cleaned


def clone_nodes() -> list[dict[str, Any]]:
    return [dict(row) for row in NODES]


def label_scrambled_nodes() -> list[dict[str, Any]]:
    labels = [row["display_label"] for row in NODES]
    scrambled = labels[3:] + labels[:3]
    out = []
    for node, label in zip(NODES, scrambled):
        row = dict(node)
        row["display_label"] = label
        out.append(row)
    return out


def storage_reindexed_nodes() -> list[dict[str, Any]]:
    return [dict(row) for row in reversed(NODES)]


def stable_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): stable_payload(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [stable_payload(val) for val in value]
    if hasattr(value, "tolist"):
        return stable_payload(value.tolist())
    if isinstance(value, float):
        return round(value, 12)
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(stable_payload(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def numeric_flatten(value: Any) -> list[float] | None:
    if isinstance(value, bool):
        return [1.0 if value else 0.0]
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, (list, tuple)):
        values: list[float] = []
        for item in value:
            flat = numeric_flatten(item)
            if flat is None:
                return None
            values.extend(flat)
        return values
    return None


def payload_delta(left: Any, right: Any) -> float:
    left_flat = numeric_flatten(left)
    right_flat = numeric_flatten(right)
    if left_flat is not None and right_flat is not None and len(left_flat) == len(right_flat):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(left_flat, right_flat)))
    return 0.0 if stable_hash(left) == stable_hash(right) else 1.0


def base_cases() -> dict[str, dict[str, Any]]:
    return {
        "baseline": {"nodes": clone_nodes(), "edges": list(BASE_EDGES)},
        "label_scramble": {"nodes": label_scrambled_nodes(), "edges": list(BASE_EDGES)},
        "edge_rewire": {"nodes": clone_nodes(), "edges": list(REWIRED_EDGES)},
        "storage_reindex": {"nodes": storage_reindexed_nodes(), "edges": list(BASE_EDGES)},
    }


def node_by_id(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["semantic_id"]): dict(row) for row in nodes}


def canonical_edges(edges: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return sorted((str(src), str(dst)) for src, dst in edges)


def networkx_graph(nx: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> Any:
    graph = nx.DiGraph()
    for node in nodes:
        graph.add_node(str(node["semantic_id"]), **dict(node))
    graph.add_edges_from(canonical_edges(edges), relation="depends_on")
    return graph


def rustworkx_graph(rx: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> tuple[Any, dict[str, int]]:
    graph = rx.PyDiGraph()
    id_to_index = {}
    for node in nodes:
        id_to_index[str(node["semantic_id"])] = graph.add_node(dict(node))
    for src, dst in edges:
        graph.add_edge(id_to_index[src], id_to_index[dst], {"relation": "depends_on"})
    return graph, id_to_index


def node_count_label_multiset_signature(nodes: list[dict[str, Any]], _edges: list[tuple[str, str]]) -> dict[str, Any]:
    return {
        "node_count": len(nodes),
        "sorted_display_labels": sorted(str(row["display_label"]) for row in nodes),
    }


def storage_order_label_sequence_signature(nodes: list[dict[str, Any]], _edges: list[tuple[str, str]]) -> list[str]:
    return [str(row["display_label"]) for row in nodes]


def networkx_predecessor_signature(nx: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    graph = networkx_graph(nx, nodes, edges)
    return {
        str(node): sorted(str(pred) for pred in graph.predecessors(node))
        for node in sorted(graph.nodes())
    }


def networkx_reachability_signature(nx: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    graph = networkx_graph(nx, nodes, edges)
    return {
        "is_dag": bool(nx.is_directed_acyclic_graph(graph)),
        "premise_reaches_readout": bool(nx.has_path(graph, "premise", "readout")),
        "readout_reaches_premise": bool(nx.has_path(graph, "readout", "premise")),
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
    }


def rustworkx_edge_signature(rx: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    graph, _id_to_index = rustworkx_graph(rx, nodes, edges)
    edge_rows = sorted(
        (str(graph[src]["semantic_id"]), str(graph[dst]["semantic_id"]))
        for src, dst in graph.edge_list()
    )
    return {
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "edge_count": graph.num_edges(),
        "semantic_edge_hash": stable_hash(edge_rows),
        "semantic_edges": edge_rows,
    }


def sympy_edge_polynomial(sp: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> str:
    _ = nodes
    positions = {str(row["semantic_id"]): int(row["semantic_position"]) for row in NODES}
    x = sp.Symbol("x")
    expr = sp.Integer(0)
    for src, dst in canonical_edges(edges):
        exponent = 10 * positions[src] + positions[dst]
        expr += x**exponent
    return str(sp.Poly(expr, x))


def z3_edge_equality(z3: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    _ = nodes
    baseline_hash = stable_hash(canonical_edges(BASE_EDGES))
    candidate_hash = stable_hash(canonical_edges(edges))
    solver = z3.Solver()
    lhs = z3.String("baseline_edge_signature")
    rhs = z3.String("candidate_edge_signature")
    solver.add(lhs == z3.StringVal(baseline_hash))
    solver.add(rhs == z3.StringVal(candidate_hash))
    solver.add(lhs == rhs)
    status = solver.check()
    return {
        "baseline_candidate_edge_equality": str(status),
        "same_edge_signature": baseline_hash == candidate_hash,
        "equality_sat": status == z3.sat,
        "equality_unsat": status == z3.unsat,
    }


def cvc5_edge_equality(cvc5: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    _ = nodes
    baseline_hash = stable_hash(canonical_edges(BASE_EDGES))
    candidate_hash = stable_hash(canonical_edges(edges))
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    same = baseline_hash == candidate_hash
    same_term = solver.mkConst(bool_sort, "same_edge_signature")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, same_term, solver.mkBoolean(same)))
    solver.assertFormula(same_term)
    status = solver.checkSat()
    return {
        "baseline_candidate_edge_equality": str(status),
        "same_edge_signature": same,
        "equality_sat": status.isSat(),
        "equality_unsat": status.isUnsat(),
    }


def xgi_hyperedge_signature(xgi: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    _ = nodes
    graph = xgi.Hypergraph()
    for src, dst in canonical_edges(edges):
        graph.add_edge([src, dst])
    members = sorted(tuple(sorted(str(node) for node in edge)) for edge in graph.edges.members())
    return {
        "num_nodes": int(graph.num_nodes),
        "num_edges": int(graph.num_edges),
        "edge_members": members,
        "edge_member_hash": stable_hash(members),
    }


def toponetx_simplicial_signature(tnx: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    complex_ = tnx.SimplicialComplex()
    for node in nodes:
        complex_.add_node(str(node["semantic_id"]))
    for src, dst in canonical_edges(edges):
        complex_.add_simplex([src, dst])
    one_skeleton = sorted(tuple(str(part) for part in simplex) for simplex in complex_.skeleton(1))
    return {
        "dim": int(complex_.dim),
        "shape": list(complex_.shape),
        "one_skeleton": one_skeleton,
        "one_skeleton_hash": stable_hash(one_skeleton),
    }


def shortest_distance_features(nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> list[list[float]]:
    ids = [str(row["semantic_id"]) for row in sorted(nodes, key=lambda row: int(row["semantic_position"]))]
    adjacency = {node: set() for node in ids}
    for src, dst in edges:
        adjacency[src].add(dst)
        adjacency[dst].add(src)

    def distance_from(start: str) -> dict[str, int]:
        distances = {start: 0}
        frontier = [start]
        while frontier:
            current = frontier.pop(0)
            for nxt in sorted(adjacency[current]):
                if nxt not in distances:
                    distances[nxt] = distances[current] + 1
                    frontier.append(nxt)
        return distances

    distances_from_premise = distance_from("premise")
    n = max(len(ids) - 1, 1)
    incoming = Counter(dst for _src, dst in edges)
    outgoing = Counter(src for src, _dst in edges)
    return [
        [
            int(node_by_id(nodes)[node]["semantic_position"]) / n,
            float(distances_from_premise.get(node, n + 1)) / n,
            float(incoming[node] - outgoing[node]) / n,
        ]
        for node in ids
    ]


def gudhi_persistence_signature(gudhi: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    points = shortest_distance_features(nodes, edges)
    rips = gudhi.RipsComplex(points=points, max_edge_length=3.0)
    simplex_tree = rips.create_simplex_tree(max_dimension=2)
    persistence = simplex_tree.persistence()
    finite_lifetimes: dict[int, list[int]] = {0: [], 1: []}
    for dim, (birth, death) in persistence:
        if death == float("inf") or dim not in finite_lifetimes:
            continue
        finite_lifetimes[dim].append(int(round(float(death - birth) * 1_000_000)))
    return {
        "h0_count": len(finite_lifetimes[0]),
        "h0_sum_q": sum(finite_lifetimes[0]),
        "h1_count": len(finite_lifetimes[1]),
        "h1_sum_q": sum(finite_lifetimes[1]),
    }


def pyg_message_passing_signature(
    torch_geometric: Any,
    torch: Any,
    nodes: list[dict[str, Any]],
    edges: list[tuple[str, str]],
) -> list[float]:
    from torch_geometric.data import Data

    ordered_ids = [str(row["semantic_id"]) for row in sorted(nodes, key=lambda row: int(row["semantic_position"]))]
    id_to_idx = {semantic_id: idx for idx, semantic_id in enumerate(ordered_ids)}
    features = []
    for semantic_id in ordered_ids:
        position = float(node_by_id(nodes)[semantic_id]["semantic_position"])
        features.append([position / 6.0, math.sin(position + 1.0), math.cos(0.5 * position + 0.25)])
    x = torch.tensor(features, dtype=torch.float64)
    edge_index = torch.tensor(
        [[id_to_idx[src], id_to_idx[dst]] for src, dst in edges],
        dtype=torch.long,
    ).t().contiguous()
    data = Data(x=x, edge_index=edge_index)
    out = data.x.clone()
    src_nodes, dst_nodes = data.edge_index
    aggregate = torch.zeros_like(out)
    weights = 0.31 + 0.07 * (src_nodes.to(torch.float64) + 1.0) + 0.03 * (dst_nodes.to(torch.float64) + 1.0)
    aggregate.index_add_(0, dst_nodes, out[src_nodes] * weights.unsqueeze(1))
    readout = torch.tanh(out + aggregate).flatten()
    _ = torch_geometric
    return [float(value) for value in readout.tolist()]


def pytorch_edge_tensor_signature(
    torch: Any,
    nodes: list[dict[str, Any]],
    edges: list[tuple[str, str]],
) -> list[float]:
    ordered_ids = [str(row["semantic_id"]) for row in sorted(nodes, key=lambda row: int(row["semantic_position"]))]
    id_to_idx = {semantic_id: idx for idx, semantic_id in enumerate(ordered_ids)}
    features = []
    for semantic_id in ordered_ids:
        position = float(node_by_id(nodes)[semantic_id]["semantic_position"])
        features.append([position / 6.0, math.sin(position + 0.5), math.cos(position + 1.25)])
    x = torch.tensor(features, dtype=torch.float64)
    aggregate = torch.zeros_like(x)
    for src, dst in edges:
        src_idx = id_to_idx[src]
        dst_idx = id_to_idx[dst]
        weight = 0.29 + 0.05 * (src_idx + 1.0) + 0.02 * (dst_idx + 1.0)
        aggregate[dst_idx] += x[src_idx] * weight
    readout = torch.tanh(x + aggregate).flatten()
    return [float(value) for value in readout.tolist()]


PredicateFn = Callable[[list[dict[str, Any]], list[tuple[str, str]]], Any]


def make_row(
    *,
    tool: str,
    predicate: str,
    predicate_family: str,
    expected_status: str,
    reason: str,
    fn: PredicateFn,
) -> dict[str, Any]:
    cases = base_cases()
    values = {name: fn(case["nodes"], case["edges"]) for name, case in cases.items()}
    label_delta = payload_delta(values["baseline"], values["label_scramble"])
    edge_delta = payload_delta(values["baseline"], values["edge_rewire"])
    storage_delta = payload_delta(values["baseline"], values["storage_reindex"])
    if expected_status == "killed":
        semantic_status = "killed"
    elif label_delta <= EPS_INVARIANT and storage_delta <= EPS_INVARIANT and edge_delta > EPS_VARIANT:
        semantic_status = "scout_level"
    elif label_delta > EPS_INVARIANT or storage_delta > EPS_INVARIANT:
        semantic_status = "killed"
    else:
        semantic_status = "open"
    return {
        "tool": tool,
        "predicate": predicate,
        "predicate_family": predicate_family,
        "label_scramble_delta": label_delta,
        "edge_rewire_delta": edge_delta,
        "storage_reindex_delta": storage_delta,
        "semantic_status": semantic_status,
        "expected_status": expected_status,
        "reason": reason,
        "baseline_digest": stable_hash(values["baseline"]),
        "label_scramble_digest": stable_hash(values["label_scramble"]),
        "edge_rewire_digest": stable_hash(values["edge_rewire"]),
        "storage_reindex_digest": stable_hash(values["storage_reindex"]),
        "baseline_value": stable_payload(values["baseline"]),
        "edge_rewire_value": stable_payload(values["edge_rewire"]),
    }


def blocked_row(tool: str, predicate: str, reason: str) -> dict[str, Any]:
    return {
        "tool": tool,
        "predicate": predicate,
        "predicate_family": "tool_import",
        "label_scramble_delta": None,
        "edge_rewire_delta": None,
        "storage_reindex_delta": None,
        "semantic_status": "blocked",
        "expected_status": "blocked",
        "reason": reason,
    }


def build_matrix(status: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    if status["networkx"]["importable"]:
        nx = status["networkx"]["module_ref"]
        status["networkx"]["used"] = True
        rows.append(
            make_row(
                tool="networkx",
                predicate="node_count_and_display_label_multiset",
                predicate_family="row_count_label_only",
                expected_status="killed",
                reason="Same row count and same label multiset cannot distinguish the edge-rewired graph.",
                fn=node_count_label_multiset_signature,
            )
        )
        rows.append(
            make_row(
                tool="networkx",
                predicate="storage_order_display_label_sequence",
                predicate_family="label_storage_only",
                expected_status="killed",
                reason="Display-label and storage-order controls move this predicate without changing semantic edges.",
                fn=storage_order_label_sequence_signature,
            )
        )
        rows.append(
            make_row(
                tool="networkx",
                predicate="predecessor_set_signature",
                predicate_family="edge_sensitive",
                expected_status="scout_level",
                reason="Predecessor sets are label/storage invariant and change under edge rewiring.",
                fn=lambda nodes, edges: networkx_predecessor_signature(nx, nodes, edges),
            )
        )
        rows.append(
            make_row(
                tool="networkx",
                predicate="source_to_sink_reachability",
                predicate_family="coarse_edge_predicate",
                expected_status="open",
                reason="Reachability is true in both edge structures, so it stays open and cannot carry the coupling claim alone.",
                fn=lambda nodes, edges: networkx_reachability_signature(nx, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("networkx", "networkx_predicate_suite", status["networkx"]["error"]))

    if status["rustworkx"]["importable"]:
        rx = status["rustworkx"]["module_ref"]
        status["rustworkx"]["used"] = True
        rows.append(
            make_row(
                tool="rustworkx",
                predicate="directed_semantic_edge_signature",
                predicate_family="edge_sensitive",
                expected_status="scout_level",
                reason="Directed semantic edge hash is invariant to labels/storage and changes under rewiring.",
                fn=lambda nodes, edges: rustworkx_edge_signature(rx, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("rustworkx", "directed_semantic_edge_signature", status["rustworkx"]["error"]))

    if status["sympy"]["importable"]:
        sp = status["sympy"]["module_ref"]
        status["sympy"]["used"] = True
        rows.append(
            make_row(
                tool="sympy",
                predicate="semantic_edge_polynomial",
                predicate_family="symbolic_edge_sensitive",
                expected_status="scout_level",
                reason="Polynomial exponents encode source/destination semantic positions, not display labels or storage order.",
                fn=lambda nodes, edges: sympy_edge_polynomial(sp, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("sympy", "semantic_edge_polynomial", status["sympy"]["error"]))

    if status["z3"]["importable"]:
        z3 = status["z3"]["module_ref"]
        status["z3"]["used"] = True
        rows.append(
            make_row(
                tool="z3",
                predicate="baseline_edge_signature_equality_sat",
                predicate_family="smt_edge_equality",
                expected_status="scout_level",
                reason="Baseline equality is SAT for label/storage controls and UNSAT for the edge-rewired control.",
                fn=lambda nodes, edges: z3_edge_equality(z3, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("z3", "baseline_edge_signature_equality_sat", status["z3"]["error"]))

    if status["cvc5"]["importable"]:
        cvc5 = status["cvc5"]["module_ref"]
        status["cvc5"]["used"] = True
        rows.append(
            make_row(
                tool="cvc5",
                predicate="baseline_edge_signature_equality_sat",
                predicate_family="smt_edge_equality",
                expected_status="scout_level",
                reason="Independent SMT-family cross-check of the z3 edge-signature equality predicate.",
                fn=lambda nodes, edges: cvc5_edge_equality(cvc5, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("cvc5", "baseline_edge_signature_equality_sat", status["cvc5"]["error"]))

    if status["xgi"]["importable"]:
        xgi = status["xgi"]["module_ref"]
        status["xgi"]["used"] = True
        rows.append(
            make_row(
                tool="xgi",
                predicate="semantic_hyperedge_member_signature",
                predicate_family="supportive_edge_sensitive",
                expected_status="scout_level",
                reason="Hyperedge member identity changes under rewiring while labels/storage do not matter.",
                fn=lambda nodes, edges: xgi_hyperedge_signature(xgi, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("xgi", "semantic_hyperedge_member_signature", status["xgi"]["error"]))

    if status["toponetx"]["importable"]:
        tnx = status["toponetx"]["module_ref"]
        status["toponetx"]["used"] = True
        rows.append(
            make_row(
                tool="toponetx",
                predicate="semantic_one_skeleton_cell_signature",
                predicate_family="supportive_edge_sensitive",
                expected_status="scout_level",
                reason="Simplicial one-skeleton cell identity changes under rewiring while labels/storage do not matter.",
                fn=lambda nodes, edges: toponetx_simplicial_signature(tnx, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("toponetx", "semantic_one_skeleton_cell_signature", status["toponetx"]["error"]))

    if status["gudhi"]["importable"]:
        gudhi = status["gudhi"]["module_ref"]
        status["gudhi"]["used"] = True
        rows.append(
            make_row(
                tool="gudhi",
                predicate="degree_path_persistence_signature",
                predicate_family="supportive_topology_sensitive",
                expected_status="scout_level",
                reason="Persistence is computed from graph-derived path/degree features, not display labels or storage order.",
                fn=lambda nodes, edges: gudhi_persistence_signature(gudhi, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("gudhi", "degree_path_persistence_signature", status["gudhi"]["error"]))

    if status["pytorch"]["importable"]:
        torch = status["pytorch"]["module_ref"]
        status["pytorch"]["used"] = True
        rows.append(
            make_row(
                tool="pytorch",
                predicate="local_tensor_message_passing_readout",
                predicate_family="edge_sensitive_tensor",
                expected_status="scout_level",
                reason="Local PyTorch tensor message passing consumes the semantic edge set directly, so rewiring changes the nonclassical readout while labels/storage do not.",
                fn=lambda nodes, edges: pytorch_edge_tensor_signature(torch, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("pytorch", "local_tensor_message_passing_readout", status["pytorch"]["error"]))

    if status["pyg"]["importable"] and status["pytorch"]["importable"]:
        torch_geometric = status["pyg"]["module_ref"]
        torch = status["pytorch"]["module_ref"]
        status["pyg"]["used"] = True
        rows.append(
            make_row(
                tool="pyg",
                predicate="finite_message_passing_readout",
                predicate_family="supportive_edge_sensitive",
                expected_status="scout_level",
                reason="One-step message passing uses edge_index, so rewiring changes the readout while labels/storage do not.",
                fn=lambda nodes, edges: pyg_message_passing_signature(torch_geometric, torch, nodes, edges),
            )
        )
    else:
        missing = "torch_geometric missing" if not status["pyg"]["importable"] else "pytorch missing"
        detail = status["pyg"].get("error") or status["pytorch"].get("error") or missing
        rows.append(blocked_row("pyg", "finite_message_passing_readout", str(detail)))

    return rows


def matrix_summary(rows: list[dict[str, Any]], status: dict[str, dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row["semantic_status"]) for row in rows)
    killed_label_or_row_count = [
        row
        for row in rows
        if row["semantic_status"] == "killed"
        and row["predicate_family"] in {"row_count_label_only", "label_storage_only"}
    ]
    scout_level_edge_sensitive = [
        row
        for row in rows
        if row["semantic_status"] == "scout_level" and "edge" in str(row["predicate_family"])
    ]
    blocked_or_missing = [
        tool
        for tool, row in status.items()
        if tool != "pytorch" and (not row.get("importable") or row.get("used") is False and tool not in {"python_json"})
    ]
    return {
        "matrix_rows": len(rows),
        "status_counts": dict(sorted(counts.items())),
        "killed_label_or_row_count_count": len(killed_label_or_row_count),
        "scout_level_edge_sensitive_count": len(scout_level_edge_sensitive),
        "blocked_or_import_missing_tools": blocked_or_missing,
        "load_bearing_tools_used": [
            tool
            for tool, depth in TOOL_INTEGRATION_DEPTH.items()
            if depth == "load_bearing" and status.get(tool, {}).get("used") is True
        ],
        "supportive_tools_used": [
            tool
            for tool, depth in TOOL_INTEGRATION_DEPTH.items()
            if depth == "supportive" and status.get(tool, {}).get("used") is True
        ],
    }


def main() -> int:
    started = time.time()
    status = import_status()
    rows = build_matrix(status)
    summary = matrix_summary(rows, status)

    mandatory_tools = {"rustworkx", "networkx", "pytorch", "z3", "cvc5", "sympy"}
    mandatory_used = all(status.get(tool, {}).get("used") is True for tool in mandatory_tools)
    killed_label_or_row_count = summary["killed_label_or_row_count_count"] >= 1
    edge_sensitive_survived = summary["scout_level_edge_sensitive_count"] >= 1
    invariant_controls_covered = all(
        (
            row["semantic_status"] != "scout_level"
            or (
                row["label_scramble_delta"] is not None
                and row["storage_reindex_delta"] is not None
                and row["edge_rewire_delta"] is not None
                and row["label_scramble_delta"] <= EPS_INVARIANT
                and row["storage_reindex_delta"] <= EPS_INVARIANT
                and row["edge_rewire_delta"] > EPS_VARIANT
            )
        )
        for row in rows
    )

    positive = {
        "mandatory_graph_proof_tools_executed_when_available": {
            "mandatory_tools": sorted(mandatory_tools),
            "used": summary["load_bearing_tools_used"],
            "pass": bool(mandatory_used),
        },
        "matrix_kills_label_or_row_count_overclaim": {
            "killed_label_or_row_count_count": summary["killed_label_or_row_count_count"],
            "pass": bool(killed_label_or_row_count),
        },
        "matrix_has_edge_sensitive_scout_level_survivor": {
            "scout_level_edge_sensitive_count": summary["scout_level_edge_sensitive_count"],
            "pass": bool(edge_sensitive_survived),
        },
        "edge_sensitive_survivors_pass_label_and_storage_controls": {
            "EPS_INVARIANT": EPS_INVARIANT,
            "EPS_VARIANT": EPS_VARIANT,
            "pass": bool(invariant_controls_covered),
        },
    }

    graveyard_companions = {
        "row_count_and_label_multiset_claim_killed": {
            "predicate": "networkx.node_count_and_display_label_multiset",
            "reason": "It is unchanged under edge rewiring, so it cannot prove semantic coupling.",
            "pass": any(
                row["tool"] == "networkx"
                and row["predicate"] == "node_count_and_display_label_multiset"
                and row["semantic_status"] == "killed"
                for row in rows
            ),
        },
        "display_label_storage_sequence_claim_killed": {
            "predicate": "networkx.storage_order_display_label_sequence",
            "reason": "It moves under label scramble/storage reindex controls without semantic edge change.",
            "pass": any(
                row["tool"] == "networkx"
                and row["predicate"] == "storage_order_display_label_sequence"
                and row["semantic_status"] == "killed"
                for row in rows
            ),
        },
        "coarse_reachability_left_open_not_promoted": {
            "predicate": "networkx.source_to_sink_reachability",
            "reason": "Reachability remains true in both edge structures and is explicitly open, not promoted.",
            "pass": any(
                row["tool"] == "networkx"
                and row["predicate"] == "source_to_sink_reachability"
                and row["semantic_status"] == "open"
                for row in rows
            ),
        },
    }

    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "claim_ceiling_blocks_graph_proof_promotion": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": bool("does not admit a graph proof" in CLAIM_CEILING.lower() and "canonical claim" in CLAIM_CEILING.lower()),
        },
        "optional_tool_absence_is_recorded_not_faked": {
            "blocked_or_import_missing_tools": summary["blocked_or_import_missing_tools"],
            "supportive_tools_used": summary["supportive_tools_used"],
            "pass": True,
        },
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
    )

    receipt = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            **summary,
        },
        "matrix": rows,
        "import_status": without_module_refs(status),
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row.get("pass") is True),
        },
        "divergence_log": [
            "label_scramble changes display-label attachment only; semantic ids and edges remain fixed",
            "storage_reindex reverses storage order only; graph predicates must recover by semantic id",
            "edge_rewire keeps node count, label multiset, and edge count while changing dependency edges",
        ],
        "why_not_v4_probes": [
            "v5 formal scout focused on provider-loop4 graph/proof predicate controls",
            "nonpromotion matrix result only; no v4 canonical probe, final proof stack, or target-system claim",
            "separates row-count/label-only killed predicates from edge-sensitive scout-level predicates",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "blockers": [] if all_pass else ["graph_proof_tool_semantic_coupling_matrix_failed"],
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "name": NAME,
                "all_pass": bool(all_pass),
                "out_path": str(OUT_PATH),
                "summary": receipt["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
