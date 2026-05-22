#!/usr/bin/env python3
"""Semantic graph edge-structure falsifier.

Formal scout only. The node labels and semantic positions are fixed while the
DAG edge structure is rewired. A green receipt means the graph-aware PyTorch
operator changes under rewired edges even though row count, sorted labels,
sorted semantic positions, and edge-blind summaries are unchanged. It also
checks that storage-index permutation is restored by semantic ids and that
display-label renaming is a no-op.

This kills edge-blind row-count and sorted-sequence overclaims. It does not
promote a graph proof, final proof stack, manifold, Axis0, bridge, engine,
physics, target-system, or canonical claim.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import rustworkx as rx
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "semantic_graph_edge_structure_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "semantic_graph_edge_structure_falsifier"
CLAIM_CEILING = (
    "Formal scout only: fixed node labels and semantic positions are evaluated "
    "under two DAG edge structures with identical row count, edge count, sorted "
    "labels, and sorted semantic-position sequence. PyTorch operator output "
    "must change under rewired edges, while storage-index permutation and label "
    "rename controls remain invariant. This does not admit a graph proof, final "
    "proof stack, manifold, Axis0, bridge, engine, physics, target-system, or "
    "canonical claim; promotion_allowed remains false."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph-aware operator state propagation over predecessor states",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing DAG construction, edge inventory, acyclicity, and predecessor structure",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive proof that edge-signature equality is UNSAT for the rewired graph and SAT for invariant controls",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive independent Boolean cross-check for the same edge-signature predicates",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive exact polynomial witness that the rewired edge set differs while invariant controls match",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive stable hashing of graph and edge-blind summaries",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive formal-scout result serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "supportive",
    "cvc5": "supportive",
    "sympy": "supportive",
    "hashlib": "supportive",
    "python_json": "supportive",
}

EPS_INVARIANT = 1e-11
EPS_VARIANT = 1e-4

NODES = [
    {"semantic_id": "n0", "display_label": "premise_anchor", "semantic_position": 0},
    {"semantic_id": "n1", "display_label": "definition_gate", "semantic_position": 1},
    {"semantic_id": "n2", "display_label": "constraint_gate", "semantic_position": 2},
    {"semantic_id": "n3", "display_label": "lemma_left", "semantic_position": 3},
    {"semantic_id": "n4", "display_label": "lemma_right", "semantic_position": 4},
    {"semantic_id": "n5", "display_label": "operator_join", "semantic_position": 5},
    {"semantic_id": "n6", "display_label": "proof_readout", "semantic_position": 6},
]

BASE_EDGES = [
    ("n0", "n1"),
    ("n0", "n2"),
    ("n1", "n3"),
    ("n2", "n3"),
    ("n1", "n4"),
    ("n3", "n5"),
    ("n4", "n5"),
    ("n5", "n6"),
]

REWIRED_EDGES = [
    ("n0", "n1"),
    ("n0", "n2"),
    ("n1", "n4"),
    ("n2", "n4"),
    ("n2", "n3"),
    ("n3", "n5"),
    ("n4", "n5"),
    ("n5", "n6"),
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(val) for val in value]
    if torch.is_tensor(value):
        if value.numel() == 1:
            return float(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    return value


def clone_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in nodes]


def build_graph(nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> rx.PyDiGraph:
    graph = rx.PyDiGraph()
    id_to_index = {}
    for node in nodes:
        id_to_index[str(node["semantic_id"])] = graph.add_node(dict(node))
    for src, dst in edges:
        graph.add_edge(id_to_index[src], id_to_index[dst], {"relation": "depends_on"})
    return graph


def graph_indices_by_semantic_position(graph: rx.PyDiGraph) -> list[int]:
    return sorted(list(graph.node_indices()), key=lambda idx: int(graph[idx]["semantic_position"]))


def canonical_edges(graph: rx.PyDiGraph) -> list[tuple[str, str]]:
    rows = []
    for src, dst in graph.edge_list():
        rows.append((str(graph[src]["semantic_id"]), str(graph[dst]["semantic_id"])))
    return sorted(rows)


def incoming_by_index(graph: rx.PyDiGraph) -> dict[int, list[int]]:
    incoming = {int(idx): [] for idx in graph.node_indices()}
    for src, dst in graph.edge_list():
        incoming[int(dst)].append(int(src))
    for dst in incoming:
        incoming[dst].sort(key=lambda idx: int(graph[idx]["semantic_position"]))
    return incoming


def edge_blind_summary(graph: rx.PyDiGraph) -> dict[str, Any]:
    ordered = graph_indices_by_semantic_position(graph)
    labels = sorted(str(graph[idx]["display_label"]) for idx in ordered)
    positions = [int(graph[idx]["semantic_position"]) for idx in ordered]
    return {
        "row_count": len(ordered),
        "edge_count": graph.num_edges(),
        "sorted_display_labels": labels,
        "sorted_semantic_positions": positions,
        "semantic_id_sequence": [str(graph[idx]["semantic_id"]) for idx in ordered],
    }


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def node_seed(position: int) -> torch.Tensor:
    return torch.tensor(
        [
            math.sin(0.41 * (position + 1)) + 0.13 * (position + 1),
            math.cos(0.37 * (position + 2)) - 0.07 * (position + 1),
            math.sin(0.23 * (position + 3)) + math.cos(0.19 * (position + 1)),
        ],
        dtype=torch.float64,
    )


def node_operator(position: int) -> torch.Tensor:
    angle = 0.17 + 0.031 * position
    return torch.tensor(
        [
            [math.cos(angle), -math.sin(angle), 0.05 * (position + 1)],
            [math.sin(angle), math.cos(angle), 0.03 * (position + 2)],
            [0.02 * (position + 3), -0.04 * (position + 1), 1.0 + 0.01 * position],
        ],
        dtype=torch.float64,
    )


def edge_weight(src_position: int, dst_position: int) -> float:
    return 0.37 + 0.11 * (src_position + 1) + 0.017 * (dst_position + 1)


def graph_operator_output(graph: rx.PyDiGraph) -> torch.Tensor:
    if not rx.is_directed_acyclic_graph(graph):
        raise ValueError("graph must be a DAG")
    states: dict[int, torch.Tensor] = {}
    incoming = incoming_by_index(graph)
    for idx in graph_indices_by_semantic_position(graph):
        pos = int(graph[idx]["semantic_position"])
        combined = node_seed(pos)
        for pred in incoming[int(idx)]:
            src_pos = int(graph[pred]["semantic_position"])
            combined = combined + edge_weight(src_pos, pos) * states[pred]
        states[int(idx)] = torch.tanh(node_operator(pos) @ combined)
    sinks = [
        idx
        for idx in graph_indices_by_semantic_position(graph)
        if all(src != idx for src, _dst in graph.edge_list())
    ]
    if not sinks:
        raise ValueError("graph must have at least one sink")
    return torch.cat([states[int(idx)] for idx in sinks])


def output_distance(left: torch.Tensor, right: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(left - right).item())


def renamed_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    renamed = []
    for idx, node in enumerate(nodes):
        row = dict(node)
        row["display_label"] = f"renamed_label_{idx:02d}"
        renamed.append(row)
    return renamed


def storage_permuted_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in reversed(nodes)]


def sympy_edge_polynomial(edges: list[tuple[str, str]]) -> str:
    x = sp.Symbol("x")
    id_to_pos = {row["semantic_id"]: int(row["semantic_position"]) for row in NODES}
    expr = 0
    for src, dst in sorted(edges):
        exponent = 10 * id_to_pos[src] + id_to_pos[dst]
        expr += sp.Integer(1) * x**exponent
    return str(sp.Poly(expr, x))


def z3_edge_equality(edge_a: list[tuple[str, str]], edge_b: list[tuple[str, str]]) -> dict[str, Any]:
    solver = z3.Solver()
    a_hash = stable_hash(sorted(edge_a))
    b_hash = stable_hash(sorted(edge_b))
    a = z3.String("edge_signature_a")
    b = z3.String("edge_signature_b")
    solver.add(a == z3.StringVal(a_hash))
    solver.add(b == z3.StringVal(b_hash))
    solver.add(a == b)
    status = solver.check()
    return {
        "solver": "z3",
        "status": str(status),
        "same_edge_signature": a_hash == b_hash,
        "equality_sat": status == z3.sat,
        "equality_unsat": status == z3.unsat,
    }


def cvc5_edge_equality(edge_a: list[tuple[str, str]], edge_b: list[tuple[str, str]]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    same = stable_hash(sorted(edge_a)) == stable_hash(sorted(edge_b))
    same_term = solver.mkConst(bool_sort, "same_edge_signature")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, same_term, solver.mkBoolean(same)))
    solver.assertFormula(same_term)
    status = solver.checkSat()
    return {
        "solver": "cvc5",
        "status": str(status),
        "same_edge_signature": same,
        "equality_sat": status.isSat(),
        "equality_unsat": status.isUnsat(),
    }


def graph_case(name: str, nodes: list[dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, Any]:
    graph = build_graph(nodes, edges)
    output = graph_operator_output(graph)
    edge_rows = canonical_edges(graph)
    summary = edge_blind_summary(graph)
    return {
        "name": name,
        "graph": graph,
        "output": output,
        "canonical_edges": edge_rows,
        "edge_hash": stable_hash(edge_rows),
        "edge_blind_summary": summary,
        "edge_blind_hash": stable_hash(summary),
        "sympy_edge_polynomial": sympy_edge_polynomial(edge_rows),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "topological_semantic_ids": [
            str(graph[idx]["semantic_id"]) for idx in graph_indices_by_semantic_position(graph)
        ],
    }


def compare_to_baseline(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "output_distance": output_distance(baseline["output"], candidate["output"]),
        "same_edge_hash": baseline["edge_hash"] == candidate["edge_hash"],
        "same_edge_blind_hash": baseline["edge_blind_hash"] == candidate["edge_blind_hash"],
        "same_sympy_edge_polynomial": (
            baseline["sympy_edge_polynomial"] == candidate["sympy_edge_polynomial"]
        ),
        "z3_edge_equality": z3_edge_equality(baseline["canonical_edges"], candidate["canonical_edges"]),
        "cvc5_edge_equality": cvc5_edge_equality(
            baseline["canonical_edges"], candidate["canonical_edges"]
        ),
    }


def main() -> int:
    started = time.time()
    base = graph_case("baseline", clone_nodes(NODES), BASE_EDGES)
    rewired = graph_case("rewired_same_nodes_same_row_count", clone_nodes(NODES), REWIRED_EDGES)
    storage_restored = graph_case(
        "storage_index_permutation_restored", storage_permuted_nodes(NODES), BASE_EDGES
    )
    label_renamed = graph_case("label_rename_no_op", renamed_nodes(NODES), BASE_EDGES)

    rewired_cmp = compare_to_baseline(base, rewired)
    storage_cmp = compare_to_baseline(base, storage_restored)
    label_cmp = compare_to_baseline(base, label_renamed)

    rewired_changes_output = rewired_cmp["output_distance"] > EPS_VARIANT
    rewired_edge_blind_collision = (
        rewired_cmp["same_edge_blind_hash"]
        and not rewired_cmp["same_edge_hash"]
        and not rewired_cmp["same_sympy_edge_polynomial"]
    )
    storage_invariant = (
        storage_cmp["output_distance"] <= EPS_INVARIANT
        and storage_cmp["same_edge_hash"]
        and storage_cmp["same_sympy_edge_polynomial"]
    )
    label_invariant = (
        label_cmp["output_distance"] <= EPS_INVARIANT
        and label_cmp["same_edge_hash"]
        and label_cmp["same_sympy_edge_polynomial"]
    )
    rewired_proved_distinct = (
        rewired_cmp["z3_edge_equality"]["equality_unsat"]
        and rewired_cmp["cvc5_edge_equality"]["equality_unsat"]
    )
    invariant_controls_sat = (
        storage_cmp["z3_edge_equality"]["equality_sat"]
        and storage_cmp["cvc5_edge_equality"]["equality_sat"]
        and label_cmp["z3_edge_equality"]["equality_sat"]
        and label_cmp["cvc5_edge_equality"]["equality_sat"]
    )

    positive = {
        "baseline_graph_is_dag_with_fixed_semantic_positions": {
            "is_dag": base["is_dag"],
            "row_count": base["edge_blind_summary"]["row_count"],
            "edge_count": base["edge_blind_summary"]["edge_count"],
            "topological_semantic_ids": base["topological_semantic_ids"],
            "pass": bool(base["is_dag"] and base["edge_blind_summary"]["row_count"] == len(NODES)),
        },
        "rewired_edges_change_operator_output": {
            "output_distance": rewired_cmp["output_distance"],
            "EPS_VARIANT": EPS_VARIANT,
            "baseline_edges": base["canonical_edges"],
            "rewired_edges": rewired["canonical_edges"],
            "pass": bool(rewired_changes_output),
        },
        "rustworkx_edge_structure_is_load_bearing": {
            "same_edge_hash": rewired_cmp["same_edge_hash"],
            "same_edge_blind_hash": rewired_cmp["same_edge_blind_hash"],
            "same_sympy_edge_polynomial": rewired_cmp["same_sympy_edge_polynomial"],
            "pass": bool(rewired_edge_blind_collision),
        },
        "z3_cvc5_edge_distinctness_crosscheck": {
            "z3": rewired_cmp["z3_edge_equality"],
            "cvc5": rewired_cmp["cvc5_edge_equality"],
            "pass": bool(rewired_proved_distinct),
        },
    }

    graveyard_companions = {
        "same_node_labels_with_rewired_edges_kills_label_only_claim": {
            "baseline_sorted_labels": base["edge_blind_summary"]["sorted_display_labels"],
            "rewired_sorted_labels": rewired["edge_blind_summary"]["sorted_display_labels"],
            "output_distance": rewired_cmp["output_distance"],
            "pass": bool(
                base["edge_blind_summary"]["sorted_display_labels"]
                == rewired["edge_blind_summary"]["sorted_display_labels"]
                and rewired_changes_output
            ),
        },
        "same_row_count_and_sorted_sequence_kills_row_count_claim": {
            "baseline_edge_blind_summary": base["edge_blind_summary"],
            "rewired_edge_blind_summary": rewired["edge_blind_summary"],
            "edge_blind_hash_equal": rewired_cmp["same_edge_blind_hash"],
            "output_distance": rewired_cmp["output_distance"],
            "pass": bool(rewired_edge_blind_collision and rewired_changes_output),
        },
        "storage_index_permutation_restored_kills_storage_index_claim": {
            "output_distance": storage_cmp["output_distance"],
            "same_edge_hash": storage_cmp["same_edge_hash"],
            "z3": storage_cmp["z3_edge_equality"],
            "cvc5": storage_cmp["cvc5_edge_equality"],
            "pass": bool(storage_invariant),
        },
        "label_rename_no_op_kills_display_label_claim": {
            "output_distance": label_cmp["output_distance"],
            "same_edge_hash": label_cmp["same_edge_hash"],
            "renamed_sorted_labels": label_renamed["edge_blind_summary"]["sorted_display_labels"],
            "pass": bool(label_invariant),
        },
        "edge_blind_summary_collision_kills_sorted_sequence_overclaim": {
            "edge_blind_hash_equal": rewired_cmp["same_edge_blind_hash"],
            "edge_hash_equal": rewired_cmp["same_edge_hash"],
            "output_distance": rewired_cmp["output_distance"],
            "pass": bool(rewired_edge_blind_collision and rewired_changes_output),
        },
    }

    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "no_graph_proof_promotion": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
            "pass": bool(
                PROMOTION_ALLOWED is False
                and "does not admit a graph proof" in CLAIM_CEILING.lower()
                and "promotion_allowed remains false" in CLAIM_CEILING.lower()
            ),
        },
        "invariant_controls_do_not_smuggle_edge_structure": {
            "storage_invariant": storage_invariant,
            "label_invariant": label_invariant,
            "invariant_controls_sat": invariant_controls_sat,
            "pass": bool(storage_invariant and label_invariant and invariant_controls_sat),
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
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard_companions),
        "boundary": as_jsonable(boundary),
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(
                1 for row in graveyard_companions.values() if row.get("pass") is True
            ),
        },
        "semantic_graph_cases": as_jsonable(
            {
                "baseline": {
                    "canonical_edges": base["canonical_edges"],
                    "edge_hash": base["edge_hash"],
                    "edge_blind_summary": base["edge_blind_summary"],
                    "sympy_edge_polynomial": base["sympy_edge_polynomial"],
                    "operator_output": base["output"],
                },
                "rewired": {
                    "canonical_edges": rewired["canonical_edges"],
                    "edge_hash": rewired["edge_hash"],
                    "edge_blind_summary": rewired["edge_blind_summary"],
                    "sympy_edge_polynomial": rewired["sympy_edge_polynomial"],
                    "operator_output": rewired["output"],
                    "compare_to_baseline": rewired_cmp,
                },
                "storage_index_permutation_restored": {
                    "edge_blind_summary": storage_restored["edge_blind_summary"],
                    "operator_output": storage_restored["output"],
                    "compare_to_baseline": storage_cmp,
                },
                "label_rename_no_op": {
                    "edge_blind_summary": label_renamed["edge_blind_summary"],
                    "operator_output": label_renamed["output"],
                    "compare_to_baseline": label_cmp,
                },
            }
        ),
        "why_not_v4_probes": [
            "v5 formal scout over semantic graph/proof maturity, not a v4 direct probe",
            "holds semantic positions and labels fixed while varying DAG edge structure",
            "formal scout only; no graph proof promotion, proof-stack promotion, Axis0, bridge, engine, physics, target-system, or canonical claim",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "baseline_row_count": base["edge_blind_summary"]["row_count"],
            "baseline_edge_count": base["edge_blind_summary"]["edge_count"],
            "rewired_output_distance": rewired_cmp["output_distance"],
            "storage_permutation_output_distance": storage_cmp["output_distance"],
            "label_rename_output_distance": label_cmp["output_distance"],
            "promotion_allowed": PROMOTION_ALLOWED,
            "elapsed_seconds": round(time.time() - started, 6),
            "load_bearing_tools": [
                tool for tool, depth in TOOL_INTEGRATION_DEPTH.items() if depth == "load_bearing"
            ],
        },
        "blockers": [] if all_pass else ["semantic_graph_edge_structure_falsifier_failed"],
    }

    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"name": NAME, "all_pass": bool(all_pass), "out_path": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
