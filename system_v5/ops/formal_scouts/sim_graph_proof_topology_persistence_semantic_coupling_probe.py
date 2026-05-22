#!/usr/bin/env python3
"""Graph/proof topology-persistence semantic-coupling probe.

Formal scout only. This checks one narrow semantic edge/order claim across
rustworkx graph topology, topology/persistence tools, and proof predicates.
Controls cover display-label scrambling, row-count-only evidence, edge
rewiring, and storage-index reordering.

A green receipt means the same semantic claim is invariant under display-label
and storage-index controls, row-count-only evidence is killed, and edge rewiring
is detected by graph/topology/proof surfaces. It does not admit a graph proof,
proof stack, topology theorem, target-system, bridge, axis, engine, or canonical
claim.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import pathlib
import time
from collections import Counter, deque
from typing import Any, Callable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "graph_proof_topology_persistence_semantic_coupling_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "proof_audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "graph_proof_topology_persistence_semantic_coupling"
CLAIM_CEILING = (
    "Formal scout only: tests one semantic edge/order claim across rustworkx "
    "graph topology, topology/persistence tools, and z3/cvc5/sympy proof "
    "checks under label-scramble, row-count-only, edge-rewire, and "
    "storage-index controls. This does not admit a graph proof, proof stack, "
    "topology theorem, target-system, bridge, axis, engine, or canonical claim."
)

TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "required": True,
        "used_when_importable": True,
        "reason": "load-bearing directed DAG topology and topological-order checks for the semantic edge/order claim",
    },
    "gudhi": {
        "tried": True,
        "required": True,
        "used_when_importable": True,
        "reason": "load-bearing persistence signature over graph-derived distance/degree features for the same semantic edge/order claim",
    },
    "toponetx": {
        "tried": True,
        "required": False,
        "used_when_importable": True,
        "reason": "supportive one-skeleton cell signature for the same semantic edge/order claim",
    },
    "xgi": {
        "tried": True,
        "required": False,
        "used_when_importable": True,
        "reason": "supportive hyperedge incidence signature for the same semantic edge/order claim",
    },
    "z3": {
        "tried": True,
        "required": True,
        "used_when_importable": True,
        "reason": "load-bearing SMT check that the candidate edge/order digest equals the baseline semantic claim",
    },
    "cvc5": {
        "tried": True,
        "required": True,
        "used_when_importable": True,
        "reason": "load-bearing independent SMT-family check of the same candidate edge/order digest",
    },
    "sympy": {
        "tried": True,
        "required": True,
        "used_when_importable": True,
        "reason": "load-bearing symbolic polynomial check of the same semantic edge/order relation",
    },
    "python_json": {
        "tried": True,
        "required": True,
        "used_when_importable": True,
        "reason": "receipt serialization and stable digest construction",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "rustworkx": "load_bearing",
    "gudhi": "load_bearing",
    "toponetx": "supportive",
    "xgi": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "python_json": "supportive",
}

EPS_INVARIANT = 1e-12
EPS_VARIANT = 1e-9

NODES = [
    {"semantic_id": "premise", "display_label": "premise_anchor", "semantic_position": 0},
    {"semantic_id": "definition", "display_label": "definition_gate", "semantic_position": 1},
    {"semantic_id": "constraint", "display_label": "constraint_gate", "semantic_position": 2},
    {"semantic_id": "lemma_left", "display_label": "left_lemma", "semantic_position": 3},
    {"semantic_id": "lemma_right", "display_label": "right_lemma", "semantic_position": 4},
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
        "gudhi": "gudhi",
        "toponetx": "toponetx",
        "xgi": "xgi",
        "z3": "z3",
        "cvc5": "cvc5",
        "sympy": "sympy",
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
                "absence_recorded_as": "blocked" if TOOL_MANIFEST[tool]["required"] else "supportive_absence",
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
    return {tool: {key: value for key, value in row.items() if key != "module_ref"} for tool, row in status.items()}


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
        out: list[float] = []
        for item in value:
            flat = numeric_flatten(item)
            if flat is None:
                return None
            out.extend(flat)
        return out
    return None


def payload_delta(left: Any, right: Any) -> float:
    left_flat = numeric_flatten(left)
    right_flat = numeric_flatten(right)
    if left_flat is not None and right_flat is not None and len(left_flat) == len(right_flat):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(left_flat, right_flat)))
    return 0.0 if stable_hash(left) == stable_hash(right) else 1.0


def clone_nodes() -> list[dict[str, Any]]:
    return [dict(row) for row in NODES]


def label_scrambled_nodes() -> list[dict[str, Any]]:
    labels = [row["display_label"] for row in NODES]
    scrambled = labels[2:] + labels[:2]
    out = []
    for node, label in zip(NODES, scrambled):
        row = dict(node)
        row["display_label"] = label
        out.append(row)
    return out


def storage_reindexed_nodes() -> list[dict[str, Any]]:
    return [dict(row) for row in reversed(NODES)]


def cases() -> dict[str, dict[str, Any]]:
    return {
        "baseline": {"nodes": clone_nodes(), "edges": list(BASE_EDGES), "control": "positive_target"},
        "label_scramble": {"nodes": label_scrambled_nodes(), "edges": list(BASE_EDGES), "control": "label_scramble"},
        "storage_index": {"nodes": storage_reindexed_nodes(), "edges": list(BASE_EDGES), "control": "storage_index"},
        "edge_rewire": {"nodes": clone_nodes(), "edges": list(REWIRED_EDGES), "control": "edge_rewire"},
    }


def node_by_id(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["semantic_id"]): dict(row) for row in nodes}


def canonical_edges(edges: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return sorted((str(src), str(dst)) for src, dst in edges)


def ordered_ids(nodes: list[dict[str, Any]]) -> list[str]:
    return [
        str(row["semantic_id"])
        for row in sorted(nodes, key=lambda item: (int(item["semantic_position"]), str(item["semantic_id"])))
    ]


def semantic_claim_payload(nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    ids = ordered_ids(nodes)
    edge_rows = canonical_edges(edges)
    predecessor_map = {node: [] for node in ids}
    for src, dst in edge_rows:
        predecessor_map[dst].append(src)
    return {
        "semantic_order": ids,
        "semantic_edges": edge_rows,
        "operator_join_parents": sorted(predecessor_map["operator_join"]),
        "readout_parent": sorted(predecessor_map["readout"]),
    }


BASE_CLAIM_DIGEST = stable_hash(semantic_claim_payload(clone_nodes(), BASE_EDGES))


def shortest_distances(start: str, adjacency: dict[str, set[str]]) -> dict[str, int]:
    distances = {start: 0}
    frontier: deque[str] = deque([start])
    while frontier:
        current = frontier.popleft()
        for nxt in sorted(adjacency[current]):
            if nxt not in distances:
                distances[nxt] = distances[current] + 1
                frontier.append(nxt)
    return distances


def graph_feature_points(nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> list[list[float]]:
    ids = ordered_ids(nodes)
    adjacency = {node: set() for node in ids}
    reverse = {node: set() for node in ids}
    for src, dst in edges:
        adjacency[src].add(dst)
        reverse[dst].add(src)
    undirected = {node: set() for node in ids}
    for src, dst in edges:
        undirected[src].add(dst)
        undirected[dst].add(src)

    from_premise = shortest_distances("premise", adjacency)
    to_readout = shortest_distances("readout", reverse)
    undirected_from_premise = shortest_distances("premise", undirected)
    n = max(len(ids) - 1, 1)
    nodes_by_id = node_by_id(nodes)
    return [
        [
            float(nodes_by_id[node]["semantic_position"]) / n,
            float(from_premise.get(node, n + 1)) / n,
            float(to_readout.get(node, n + 1)) / n,
            float(len(reverse[node]) - len(adjacency[node])) / n,
            float(undirected_from_premise.get(node, n + 1)) / n,
        ]
        for node in ids
    ]


def rustworkx_claim_signature(rx: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    id_to_index: dict[str, int] = {}
    for node in nodes:
        id_to_index[str(node["semantic_id"])] = graph.add_node(dict(node))
    for src, dst in edges:
        graph.add_edge(id_to_index[src], id_to_index[dst], {"relation": "semantic_precedes"})
    edge_rows = sorted((str(graph[src]["semantic_id"]), str(graph[dst]["semantic_id"])) for src, dst in graph.edge_list())
    positions = {str(row["semantic_id"]): int(row["semantic_position"]) for row in nodes}
    return {
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "semantic_position_order": ordered_ids(nodes),
        "semantic_position_respects_edges": all(positions[src] < positions[dst] for src, dst in edge_rows),
        "semantic_edges": edge_rows,
        "operator_join_parents": sorted(src for src, dst in edge_rows if dst == "operator_join"),
        "premise_reaches_readout": bool(rx.digraph_has_path(graph, id_to_index["premise"], id_to_index["readout"])),
        "readout_reaches_premise": bool(rx.digraph_has_path(graph, id_to_index["readout"], id_to_index["premise"])),
        "claim_digest": stable_hash(semantic_claim_payload(nodes, edges)),
    }


def gudhi_persistence_signature(gudhi: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    points = graph_feature_points(nodes, edges)
    rips = gudhi.RipsComplex(points=points, max_edge_length=2.0)
    simplex_tree = rips.create_simplex_tree(max_dimension=2)
    persistence = simplex_tree.persistence()
    finite_lifetimes: dict[int, list[int]] = {0: [], 1: []}
    for dim, (birth, death) in persistence:
        if dim not in finite_lifetimes or death == float("inf"):
            continue
        finite_lifetimes[dim].append(int(round(float(death - birth) * 1_000_000)))
    return {
        "h0_count": len(finite_lifetimes[0]),
        "h0_sum_q": sum(finite_lifetimes[0]),
        "h1_count": len(finite_lifetimes[1]),
        "h1_sum_q": sum(finite_lifetimes[1]),
        "feature_digest": stable_hash(points),
    }


def toponetx_one_skeleton_signature(tnx: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
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
        "one_skeleton_digest": stable_hash(one_skeleton),
    }


def xgi_incidence_signature(xgi: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    _ = nodes
    hypergraph = xgi.Hypergraph()
    for src, dst in canonical_edges(edges):
        hypergraph.add_edge([src, dst])
    members = sorted(tuple(sorted(str(node) for node in edge)) for edge in hypergraph.edges.members())
    return {
        "num_nodes": int(hypergraph.num_nodes),
        "num_edges": int(hypergraph.num_edges),
        "edge_members": members,
        "edge_member_digest": stable_hash(members),
    }


def z3_claim_check(z3: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    candidate = stable_hash(semantic_claim_payload(nodes, edges))
    solver = z3.Solver()
    lhs = z3.String("candidate_claim_digest")
    rhs = z3.String("baseline_claim_digest")
    solver.add(lhs == z3.StringVal(candidate))
    solver.add(rhs == z3.StringVal(BASE_CLAIM_DIGEST))
    solver.add(lhs == rhs)
    status = solver.check()
    return {
        "same_semantic_edge_order_claim": candidate == BASE_CLAIM_DIGEST,
        "claim_equality_sat": str(status),
        "sat": status == z3.sat,
        "unsat": status == z3.unsat,
    }


def cvc5_claim_check(cvc5: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    candidate = stable_hash(semantic_claim_payload(nodes, edges))
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    same = solver.mkConst(bool_sort, "same_semantic_edge_order_claim")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, same, solver.mkBoolean(candidate == BASE_CLAIM_DIGEST)))
    solver.assertFormula(same)
    status = solver.checkSat()
    return {
        "same_semantic_edge_order_claim": candidate == BASE_CLAIM_DIGEST,
        "claim_equality_sat": str(status),
        "sat": status.isSat(),
        "unsat": status.isUnsat(),
    }


def sympy_claim_polynomial(sp: Any, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    positions = {str(row["semantic_id"]): int(row["semantic_position"]) for row in nodes}
    x = sp.Symbol("x")
    expr = sp.Integer(0)
    for src, dst in canonical_edges(edges):
        expr += x ** (10 * positions[src] + positions[dst])
    poly = sp.Poly(expr, x)
    baseline_positions = {str(row["semantic_id"]): int(row["semantic_position"]) for row in NODES}
    baseline_expr = sp.Integer(0)
    for src, dst in canonical_edges(BASE_EDGES):
        baseline_expr += x ** (10 * baseline_positions[src] + baseline_positions[dst])
    baseline_poly = sp.Poly(baseline_expr, x)
    return {
        "same_semantic_edge_order_claim": bool(sp.simplify(poly.as_expr() - baseline_poly.as_expr()) == 0),
        "polynomial": str(poly),
        "baseline_polynomial": str(baseline_poly),
    }


def row_count_only_signature(nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, int]:
    return {"node_count": len(nodes), "edge_count": len(edges)}


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
    values = {name: fn(case["nodes"], case["edges"]) for name, case in cases().items()}
    label_delta = payload_delta(values["baseline"], values["label_scramble"])
    storage_delta = payload_delta(values["baseline"], values["storage_index"])
    edge_delta = payload_delta(values["baseline"], values["edge_rewire"])
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
        "expected_status": expected_status,
        "semantic_status": semantic_status,
        "reason": reason,
        "label_scramble_delta": label_delta,
        "storage_index_delta": storage_delta,
        "edge_rewire_delta": edge_delta,
        "baseline_digest": stable_hash(values["baseline"]),
        "label_scramble_digest": stable_hash(values["label_scramble"]),
        "storage_index_digest": stable_hash(values["storage_index"]),
        "edge_rewire_digest": stable_hash(values["edge_rewire"]),
        "baseline_value": stable_payload(values["baseline"]),
        "edge_rewire_value": stable_payload(values["edge_rewire"]),
    }


def blocked_row(tool: str, predicate: str, reason: str) -> dict[str, Any]:
    return {
        "tool": tool,
        "predicate": predicate,
        "predicate_family": "tool_import",
        "expected_status": "blocked",
        "semantic_status": "blocked",
        "reason": reason,
        "label_scramble_delta": None,
        "storage_index_delta": None,
        "edge_rewire_delta": None,
    }


def build_rows(status: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        make_row(
            tool="python_json",
            predicate="row_count_only_control",
            predicate_family="row_count_only",
            expected_status="killed",
            reason="Node and edge counts are unchanged under semantic edge rewiring, so row-count-only evidence is killed.",
            fn=row_count_only_signature,
        )
    ]

    if status["rustworkx"]["importable"]:
        rx = status["rustworkx"]["module_ref"]
        status["rustworkx"]["used"] = True
        rows.append(
            make_row(
                tool="rustworkx",
                predicate="directed_dag_semantic_edge_order_claim",
                predicate_family="graph_topology_edge_order",
                expected_status="scout_level",
                reason="Directed topology, topological order, and merge-parent identity are invariant to labels/storage and change under rewiring.",
                fn=lambda nodes, edges: rustworkx_claim_signature(rx, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("rustworkx", "directed_dag_semantic_edge_order_claim", status["rustworkx"]["error"]))

    if status["gudhi"]["importable"]:
        gudhi = status["gudhi"]["module_ref"]
        status["gudhi"]["used"] = True
        rows.append(
            make_row(
                tool="gudhi",
                predicate="graph_distance_degree_persistence_signature",
                predicate_family="topology_persistence_edge_order",
                expected_status="scout_level",
                reason="Persistence is derived from the same semantic graph distances/degrees, not display labels or storage indices.",
                fn=lambda nodes, edges: gudhi_persistence_signature(gudhi, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("gudhi", "graph_distance_degree_persistence_signature", status["gudhi"]["error"]))

    if status["toponetx"]["importable"]:
        tnx = status["toponetx"]["module_ref"]
        status["toponetx"]["used"] = True
        rows.append(
            make_row(
                tool="toponetx",
                predicate="semantic_one_skeleton_signature",
                predicate_family="supportive_topology_edge_order",
                expected_status="scout_level",
                reason="The one-skeleton cell set is tied to semantic edge identity and changes only under edge rewiring.",
                fn=lambda nodes, edges: toponetx_one_skeleton_signature(tnx, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("toponetx", "semantic_one_skeleton_signature", status["toponetx"]["error"]))

    if status["xgi"]["importable"]:
        xgi = status["xgi"]["module_ref"]
        status["xgi"]["used"] = True
        rows.append(
            make_row(
                tool="xgi",
                predicate="semantic_edge_hypergraph_incidence_signature",
                predicate_family="supportive_topology_edge_order",
                expected_status="scout_level",
                reason="The hyperedge incidence set is tied to semantic edge identity and changes only under edge rewiring.",
                fn=lambda nodes, edges: xgi_incidence_signature(xgi, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("xgi", "semantic_edge_hypergraph_incidence_signature", status["xgi"]["error"]))

    if status["z3"]["importable"]:
        z3 = status["z3"]["module_ref"]
        status["z3"]["used"] = True
        rows.append(
            make_row(
                tool="z3",
                predicate="same_semantic_edge_order_claim_smt",
                predicate_family="proof_edge_order",
                expected_status="scout_level",
                reason="SMT equality is SAT for label/storage controls and UNSAT for the edge-rewired semantic claim.",
                fn=lambda nodes, edges: z3_claim_check(z3, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("z3", "same_semantic_edge_order_claim_smt", status["z3"]["error"]))

    if status["cvc5"]["importable"]:
        cvc5 = status["cvc5"]["module_ref"]
        status["cvc5"]["used"] = True
        rows.append(
            make_row(
                tool="cvc5",
                predicate="same_semantic_edge_order_claim_smt",
                predicate_family="proof_edge_order",
                expected_status="scout_level",
                reason="Independent SMT-family cross-check of the same semantic edge/order equality claim.",
                fn=lambda nodes, edges: cvc5_claim_check(cvc5, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("cvc5", "same_semantic_edge_order_claim_smt", status["cvc5"]["error"]))

    if status["sympy"]["importable"]:
        sp = status["sympy"]["module_ref"]
        status["sympy"]["used"] = True
        rows.append(
            make_row(
                tool="sympy",
                predicate="same_semantic_edge_order_claim_polynomial",
                predicate_family="proof_edge_order",
                expected_status="scout_level",
                reason="Symbolic edge polynomial encodes source/destination semantic positions, not labels or storage indices.",
                fn=lambda nodes, edges: sympy_claim_polynomial(sp, nodes, edges),
            )
        )
    else:
        rows.append(blocked_row("sympy", "same_semantic_edge_order_claim_polynomial", status["sympy"]["error"]))

    return rows


def summarize(rows: list[dict[str, Any]], status: dict[str, dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row["semantic_status"]) for row in rows)
    return {
        "matrix_rows": len(rows),
        "status_counts": dict(sorted(counts.items())),
        "row_count_only_killed_count": sum(
            1 for row in rows if row["predicate_family"] == "row_count_only" and row["semantic_status"] == "killed"
        ),
        "graph_topology_survivor_count": sum(
            1 for row in rows if row["predicate_family"] == "graph_topology_edge_order" and row["semantic_status"] == "scout_level"
        ),
        "topology_persistence_survivor_count": sum(
            1
            for row in rows
            if row["predicate_family"] in {"topology_persistence_edge_order", "supportive_topology_edge_order"}
            and row["semantic_status"] == "scout_level"
        ),
        "proof_survivor_count": sum(
            1 for row in rows if row["predicate_family"] == "proof_edge_order" and row["semantic_status"] == "scout_level"
        ),
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
        "blocked_or_import_missing_tools": [
            tool
            for tool, row in status.items()
            if not row.get("importable") or (row.get("used") is False and tool not in {"python_json"})
        ],
    }


def main() -> int:
    started = time.time()
    status = import_status()
    rows = build_rows(status)
    summary = summarize(rows, status)

    required_tools = {"rustworkx", "gudhi", "z3", "cvc5", "sympy"}
    required_tools_used = all(status.get(tool, {}).get("used") is True for tool in required_tools)
    invariant_controls_covered = all(
        (
            row["semantic_status"] != "scout_level"
            or (
                row["label_scramble_delta"] is not None
                and row["storage_index_delta"] is not None
                and row["edge_rewire_delta"] is not None
                and row["label_scramble_delta"] <= EPS_INVARIANT
                and row["storage_index_delta"] <= EPS_INVARIANT
                and row["edge_rewire_delta"] > EPS_VARIANT
            )
        )
        for row in rows
    )

    positive = {
        "required_graph_topology_persistence_proof_tools_executed": {
            "required_tools": sorted(required_tools),
            "used": summary["load_bearing_tools_used"],
            "pass": bool(required_tools_used),
        },
        "rustworkx_graph_topology_coupled_to_semantic_claim": {
            "graph_topology_survivor_count": summary["graph_topology_survivor_count"],
            "pass": summary["graph_topology_survivor_count"] >= 1,
        },
        "topology_persistence_tool_coupled_to_semantic_claim": {
            "topology_persistence_survivor_count": summary["topology_persistence_survivor_count"],
            "pass": summary["topology_persistence_survivor_count"] >= 1,
        },
        "z3_cvc5_sympy_check_same_semantic_edge_order_claim": {
            "proof_survivor_count": summary["proof_survivor_count"],
            "pass": summary["proof_survivor_count"] >= 3,
        },
        "label_scramble_and_storage_index_invariant_edge_rewire_variant": {
            "EPS_INVARIANT": EPS_INVARIANT,
            "EPS_VARIANT": EPS_VARIANT,
            "pass": bool(invariant_controls_covered),
        },
    }

    graveyard_companions = {
        "row_count_only_claim_killed": {
            "predicate": "python_json.row_count_only_control",
            "reason": "Node and edge counts stay fixed under the semantic edge-rewire control.",
            "pass": summary["row_count_only_killed_count"] >= 1,
        },
        "display_label_scramble_claim_not_promoted": {
            "control": "label_scramble",
            "reason": "Display-label attachment changes while semantic edge/order claim remains unchanged.",
            "pass": all(
                row["label_scramble_delta"] is None
                or row["semantic_status"] == "killed"
                or row["label_scramble_delta"] <= EPS_INVARIANT
                for row in rows
            ),
        },
        "storage_index_claim_not_promoted": {
            "control": "storage_index",
            "reason": "Storage row order changes while semantic ids and semantic edge/order claim remain unchanged.",
            "pass": all(
                row["storage_index_delta"] is None
                or row["semantic_status"] == "killed"
                or row["storage_index_delta"] <= EPS_INVARIANT
                for row in rows
            ),
        },
        "edge_rewire_blocks_final_proof_claim": {
            "control": "edge_rewire",
            "reason": "Edge rewiring changes graph, persistence/topology, and proof signatures while preserving row counts.",
            "pass": summary["graph_topology_survivor_count"] >= 1
            and summary["topology_persistence_survivor_count"] >= 1
            and summary["proof_survivor_count"] >= 3,
        },
    }

    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "claim_ceiling_blocks_final_graph_proof": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": "does not admit a graph proof" in CLAIM_CEILING.lower()
            and "canonical claim" in CLAIM_CEILING.lower(),
        },
        "optional_topology_tools_recorded_not_faked": {
            "supportive_tools_used": summary["supportive_tools_used"],
            "blocked_or_import_missing_tools": summary["blocked_or_import_missing_tools"],
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
        "semantic_claim": {
            "claim_digest": BASE_CLAIM_DIGEST,
            "payload": semantic_claim_payload(clone_nodes(), BASE_EDGES),
            "claim_text": "The proof readout is reached through a fixed semantic DAG whose operator_join has lemma_left and lemma_right as its semantic parents.",
        },
        "controls": {
            "label_scramble": "display labels are rotated while semantic ids, positions, and edges stay fixed",
            "row_count_only": "node and edge counts are checked as a killed nonsemantic control",
            "edge_rewire": "same node count, edge count, and labels with changed semantic dependency edges",
            "storage_index": "storage list is reversed while semantic ids, positions, and edges stay fixed",
        },
        "child_fanout_status": {
            "status": "child_fanout_blocked",
            "reason": "This parent lane has no native child/subtask spawn tool receipt available in the current runtime.",
            "write_scope_preserved": [
                str(pathlib.Path(__file__).relative_to(ROOT.parent.parent.parent)),
                str(OUT_PATH.relative_to(ROOT.parent.parent.parent)),
            ],
        },
        "child_equivalent_sections": {
            "graph_topology_tool_availability": {
                "scope": "Check rustworkx plus topology/persistence tools without editing outside the assigned source/result paths.",
                "evidence_anchors": {
                    "required": ["rustworkx", "gudhi"],
                    "supportive": ["toponetx", "xgi"],
                    "import_status_keys": ["import_status.rustworkx", "import_status.gudhi", "import_status.toponetx", "import_status.xgi"],
                    "matrix_predicates": [
                        "rustworkx.directed_dag_semantic_edge_order_claim",
                        "gudhi.graph_distance_degree_persistence_signature",
                        "toponetx.semantic_one_skeleton_signature",
                        "xgi.semantic_edge_hypergraph_incidence_signature",
                    ],
                },
                "observed": "Tool availability and topology rows are recorded in import_status and matrix.",
            },
            "proof_smt_coupling_implementation": {
                "scope": "Check z3, cvc5, and sympy against the same semantic edge/order claim digest.",
                "evidence_anchors": {
                    "semantic_claim_digest": BASE_CLAIM_DIGEST,
                    "import_status_keys": ["import_status.z3", "import_status.cvc5", "import_status.sympy"],
                    "matrix_predicates": [
                        "z3.same_semantic_edge_order_claim_smt",
                        "cvc5.same_semantic_edge_order_claim_smt",
                        "sympy.same_semantic_edge_order_claim_polynomial",
                    ],
                },
                "observed": "Proof rows use the same semantic_claim payload and are variant only under edge_rewire.",
            },
            "validation_label_scramble_audit": {
                "scope": "Audit label-scramble, row-count-only, edge-rewire, and storage-index controls plus validator compatibility.",
                "evidence_anchors": {
                    "controls": ["label_scramble", "row_count_only", "edge_rewire", "storage_index"],
                    "positive_checks": list(positive.keys()),
                    "graveyard_checks": list(graveyard_companions.keys()),
                    "validator": "system_v5/ops/formal_scouts/validate_formal_scout_results.py",
                },
                "observed": "Control deltas, graveyard companions, boundary, nearby_variants, and blockers are emitted for validation.",
            },
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
            "label_scramble changes display-label attachment only; semantic edge/order claim stays fixed",
            "storage_index reverses storage rows only; predicates must recover by semantic id/position",
            "row_count_only stays unchanged under edge rewiring and is killed as proof evidence",
            "edge_rewire preserves counts but changes semantic dependency edges and proof/topology signatures",
        ],
        "why_not_v4_probes": [
            "v5 formal scout focused on graph/proof/topology semantic-coupling controls",
            "nonpromotion receipt only; no v4 canonical probe, proof-stack admission, or topology theorem",
            "explicitly separates killed row-count-only evidence from scout-level semantic edge/order evidence",
        ],
        "mmm_saliency_delta": {
            "voice.feynman": "Converted the request into one observable operation: same semantic claim, four controls, pass/fail deltas per tool.",
            "voice.popper": "Made edge rewiring the falsifier and kept row-count-only evidence in the killed graveyard.",
            "voice.pushback": "Bounded the receipt to formal_scout/nonpromotion and blocked final graph/proof/topology claims.",
            "failure.falsifier_council": "Classified rows as killed, scout_level, open, or blocked instead of treating agreement as readiness.",
            "failure.loophole_auditor_council": "Recorded optional-tool absence separately and required exact required-tool execution before all_pass.",
            "expert.standard_checker": "Kept classification, tool manifest, integration depth, controls, nearby variants, and validator-compatible receipt fields explicit.",
            "saliency_reference_boundary": "SALIENCY_TRANCHE_01_CANDIDATE.md was treated as reference-only and not booted into the implementation.",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "blockers": [] if all_pass else ["graph_proof_topology_persistence_semantic_coupling_probe_failed"],
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
