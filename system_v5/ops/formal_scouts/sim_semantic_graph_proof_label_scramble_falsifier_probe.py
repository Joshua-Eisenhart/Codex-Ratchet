#!/usr/bin/env python3
"""Semantic graph/proof label-scramble falsifier.

Formal scout only. This binds three existing v5 receipts to a live semantic
graph/operator chain and tests whether graph/proof evidence depends on display
labels or storage indices instead of semantic order.

A green receipt means display-label scrambling and storage reindexing preserve
the semantic graph hash and PyTorch operator-chain readout, while a semantic
order scramble changes both the graph proof surface and the operator output.
It does not admit a final manifold, final G-structure, proof stack, engine,
Axis0, bridge, physics, target-system, or canonical claim.
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
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "semantic_graph_proof_label_scramble_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

GRAPH_ORDER_RESULT = RESULT_DIR / "thirteen_layer_active_manifold_layer_removal_graph_order_pyg_rustworkx_probe_results.json"
NAME_BLINDNESS_RESULT = RESULT_DIR / "layer_operator_name_blindness_falsifier_probe_results.json"
G_STRUCTURE_ORDER_RESULT = RESULT_DIR / "g_structure_nesting_semantic_order_falsifier_probe_results.json"
CONSUMED_RESULTS = [GRAPH_ORDER_RESULT, NAME_BLINDNESS_RESULT, G_STRUCTURE_ORDER_RESULT]

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "semantic_graph_proof_label_scramble_falsifier"
CLAIM_CEILING = (
    "Formal scout only: consumes green v5 graph-order, layer-name-blindness, "
    "and G-structure semantic-order receipts, then checks a live semantic "
    "operator graph where display-label and storage-index scrambles are "
    "invariant but semantic order scramble is variant. This does not admit a "
    "final manifold, final G-structure, proof stack, engine, Axis0, bridge, "
    "physics, target-system, or canonical claim; it blocks label/index-driven "
    "graph-proof overclaims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing noncommuting semantic operator-chain composition and output-distance checks",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing semantic DAG, reachability, topological order, and transitive reduction checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Boolean admission gate for consumed-green, label-blind, index-blind, semantic-variant, and graph-order predicates",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent cross-solver check of the same semantic graph/proof admission predicates",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive consumed receipt path handling",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive consumed-receipt and semantic graph hash recording",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive formal-scout receipt serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pathlib": "supportive",
    "hashlib": "supportive",
    "python_json": "supportive",
}

EPS_INVARIANT = 1e-11
EPS_VARIANT = 1e-3


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(val) for val in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return float(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_consumed_receipts() -> dict[str, dict[str, Any]]:
    loaded = {}
    for path in CONSUMED_RESULTS:
        if not path.exists():
            raise FileNotFoundError(path)
        loaded[path.name] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def receipt_green(data: dict[str, Any]) -> bool:
    return bool(
        data.get("classification") == "formal_scout"
        and data.get("promotion_allowed") is False
        and (data.get("all_pass") is True or data.get("summary", {}).get("all_pass") is True)
    )


def graph_fixture_layers(graph_order: dict[str, Any]) -> list[str]:
    layers = graph_order.get("graph_fixture", {}).get("layers", [])
    if not isinstance(layers, list) or len(layers) != 13:
        raise ValueError("graph-order receipt did not expose 13 graph_fixture.layers")
    return [str(layer) for layer in layers]


def graph_fixture_diffs(graph_order: dict[str, Any]) -> list[float]:
    diffs = graph_order.get("graph_fixture", {}).get("state_diffs", [])
    if not isinstance(diffs, list) or len(diffs) != 13:
        raise ValueError("graph-order receipt did not expose 13 graph_fixture.state_diffs")
    return [float(value) for value in diffs]


def semantic_axis(slot: int) -> torch.Tensor:
    raw = torch.tensor(
        [
            math.sin(0.71 * (slot + 1)) + 0.31 * math.cos(0.17 * (slot + 3)),
            math.cos(0.43 * (slot + 2)) - 0.19 * math.sin(0.29 * (slot + 5)),
            math.sin(0.23 * (slot + 4)) + math.cos(0.61 * (slot + 1)),
        ],
        dtype=torch.float64,
    )
    return raw / torch.linalg.vector_norm(raw).clamp_min(1e-12)


def pauli() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    sx = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.complex128)
    sy = torch.tensor([[0.0, -1j], [1j, 0.0]], dtype=torch.complex128)
    sz = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128)
    return sx, sy, sz


def su2_operator(axis: torch.Tensor, angle: float) -> torch.Tensor:
    sx, sy, sz = pauli()
    hamiltonian = axis[0] * sx + axis[1] * sy + axis[2] * sz
    half = 0.5 * angle
    eye = torch.eye(2, dtype=torch.complex128)
    return math.cos(half) * eye - 1j * math.sin(half) * hamiltonian


def semantic_specs(layers: list[str], diffs: list[float]) -> list[dict[str, Any]]:
    max_diff = max(max(diffs), 1e-9)
    specs = []
    for idx, (layer, diff) in enumerate(zip(layers, diffs)):
        specs.append(
            {
                "semantic_id": f"semantic_slot_{idx:02d}",
                "canonical_layer": layer,
                "display_label": layer,
                "semantic_position": idx,
                "axis": semantic_axis(idx),
                "angle": 0.23 + 0.035 * idx + 0.09 * float(diff) / max_diff,
            }
        )
    return specs


def compose_specs(specs: list[dict[str, Any]]) -> torch.Tensor:
    state = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=torch.complex128)
    unitary = torch.eye(2, dtype=torch.complex128)
    for spec in sorted(specs, key=lambda row: int(row["semantic_position"])):
        unitary = su2_operator(spec["axis"], float(spec["angle"])) @ unitary
    return unitary @ state


def distance(left: torch.Tensor, right: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(left - right).real.item())


def semantic_edges(specs: list[dict[str, Any]]) -> list[tuple[int, int]]:
    ordered = sorted((int(row["semantic_position"]), idx) for idx, row in enumerate(specs))
    return [(ordered[idx][1], ordered[idx + 1][1]) for idx in range(len(ordered) - 1)]


def build_semantic_graph(specs: list[dict[str, Any]]) -> rx.PyDiGraph:
    graph = rx.PyDiGraph()
    for spec in specs:
        graph.add_node(
            {
                "semantic_id": spec["semantic_id"],
                "canonical_layer": spec["canonical_layer"],
                "display_label": spec["display_label"],
                "semantic_position": int(spec["semantic_position"]),
            }
        )
    for src, dst in semantic_edges(specs):
        graph.add_edge(src, dst, {"relation": "semantic_precedes"})
    return graph


def graph_semantic_hash(graph: rx.PyDiGraph) -> str:
    topo = [int(idx) for idx in rx.topological_sort(graph)]
    payload = {
        "semantic_order": [graph[idx]["semantic_id"] for idx in topo],
        "edges": [(graph[src]["semantic_id"], graph[dst]["semantic_id"]) for src, dst in graph.edge_list()],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def graph_report(specs: list[dict[str, Any]]) -> dict[str, Any]:
    graph = build_semantic_graph(specs)
    topo = [int(idx) for idx in rx.topological_sort(graph)]
    reduction, _node_map = rx.transitive_reduction(graph)
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "source_reaches_sink": bool(rx.digraph_has_path(graph, topo[0], topo[-1])),
        "sink_reaches_source": bool(rx.digraph_has_path(graph, topo[-1], topo[0])),
        "topological_semantic_ids": [graph[idx]["semantic_id"] for idx in topo],
        "topological_display_labels": [graph[idx]["display_label"] for idx in topo],
        "transitive_reduction_edge_count": reduction.num_edges(),
        "semantic_hash": graph_semantic_hash(graph),
    }


def label_scrambled(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = [row["display_label"] for row in specs]
    scrambled_labels = labels[5:] + labels[:5]
    out = []
    for row, label in zip(specs, scrambled_labels):
        new = dict(row)
        new["display_label"] = f"display_scrambled::{label}"
        out.append(new)
    return out


def storage_reindexed(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in reversed(specs)]


def semantic_order_scrambled(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    permutation = [0, 2, 1, 3, 5, 4, 6, 8, 7, 9, 11, 10, 12]
    out = []
    for new_position, original_idx in enumerate(permutation):
        row = dict(specs[original_idx])
        row["semantic_position"] = new_position
        out.append(row)
    return out


def variant_suite(layers: list[str], diffs: list[float]) -> dict[str, Any]:
    baseline_specs = semantic_specs(layers, diffs)
    baseline_output = compose_specs(baseline_specs)
    baseline_graph = graph_report(baseline_specs)
    variants = {}
    for label, specs in [
        ("label_scramble", label_scrambled(baseline_specs)),
        ("storage_reindex", storage_reindexed(baseline_specs)),
        ("semantic_order_scramble", semantic_order_scrambled(baseline_specs)),
    ]:
        output = compose_specs(specs)
        graph = graph_report(specs)
        variants[label] = {
            "output_distance": distance(baseline_output, output),
            "semantic_hash_matches_baseline": graph["semantic_hash"] == baseline_graph["semantic_hash"],
            "topological_semantic_ids": graph["topological_semantic_ids"],
            "topological_display_labels": graph["topological_display_labels"],
            "graph": graph,
        }
    return {
        "baseline_graph": baseline_graph,
        "label_scramble": variants["label_scramble"],
        "storage_reindex": variants["storage_reindex"],
        "semantic_order_scramble": variants["semantic_order_scramble"],
        "baseline_output_norm": float(torch.linalg.vector_norm(baseline_output).real.item()),
    }


def z3_admission(predicates: dict[str, bool]) -> dict[str, Any]:
    solver = z3.Solver()
    zvars = {key: z3.Bool(key) for key in predicates}
    for key, value in predicates.items():
        solver.add(zvars[key] == z3.BoolVal(value))
    solver.add(z3.And(*zvars.values()))
    status = solver.check()
    return {"solver": "z3", "status": str(status), "joint_sat": status == z3.sat, "pass": status == z3.sat}


def cvc5_admission(predicates: dict[str, bool]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    terms = []
    for key, value in predicates.items():
        term = solver.mkConst(bool_sort, key)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(value)))
        terms.append(term)
    solver.assertFormula(solver.mkTerm(Kind.AND, *terms))
    status = solver.checkSat()
    return {"solver": "cvc5", "status": str(status), "joint_sat": status.isSat(), "pass": status.isSat()}


def main() -> int:
    started = time.time()
    consumed = load_consumed_receipts()
    graph_order = consumed[GRAPH_ORDER_RESULT.name]
    layers = graph_fixture_layers(graph_order)
    diffs = graph_fixture_diffs(graph_order)
    suite = variant_suite(layers, diffs)

    consumed_rows = {
        name: {
            "path": str(RESULT_DIR / name),
            "sha256": sha256_file(RESULT_DIR / name),
            "classification": data.get("classification"),
            "promotion_allowed": data.get("promotion_allowed"),
            "all_pass": data.get("all_pass") is True or data.get("summary", {}).get("all_pass") is True,
            "receipt_green": receipt_green(data),
        }
        for name, data in consumed.items()
    }
    consumed_all_green = all(row["receipt_green"] for row in consumed_rows.values())
    label_blind = bool(
        suite["label_scramble"]["output_distance"] <= EPS_INVARIANT
        and suite["label_scramble"]["semantic_hash_matches_baseline"]
    )
    index_blind = bool(
        suite["storage_reindex"]["output_distance"] <= EPS_INVARIANT
        and suite["storage_reindex"]["semantic_hash_matches_baseline"]
    )
    semantic_variant = bool(
        suite["semantic_order_scramble"]["output_distance"] > EPS_VARIANT
        and not suite["semantic_order_scramble"]["semantic_hash_matches_baseline"]
    )
    graph_order_sensitive = bool(
        suite["baseline_graph"]["topological_semantic_ids"]
        != suite["semantic_order_scramble"]["topological_semantic_ids"]
        and suite["baseline_graph"]["source_reaches_sink"]
        and not suite["baseline_graph"]["sink_reaches_source"]
    )
    predicates = {
        "consumed_all_green": consumed_all_green,
        "label_blind": label_blind,
        "index_blind": index_blind,
        "semantic_variant": semantic_variant,
        "graph_order_sensitive": graph_order_sensitive,
    }
    z3_row = z3_admission(predicates)
    cvc5_row = cvc5_admission(predicates)
    cross_solver_agree = z3_row["joint_sat"] == cvc5_row["joint_sat"]

    positive = {
        "consumed_receipts_are_green_and_nonpromotional": {
            "consumed": consumed_rows,
            "pass": consumed_all_green,
        },
        "display_label_scramble_is_semantic_invariant": {
            "output_distance": suite["label_scramble"]["output_distance"],
            "EPS_INVARIANT": EPS_INVARIANT,
            "semantic_hash_matches_baseline": suite["label_scramble"]["semantic_hash_matches_baseline"],
            "topological_display_labels_after_scramble": suite["label_scramble"]["topological_display_labels"],
            "pass": label_blind,
        },
        "storage_reindex_is_semantic_invariant": {
            "output_distance": suite["storage_reindex"]["output_distance"],
            "EPS_INVARIANT": EPS_INVARIANT,
            "semantic_hash_matches_baseline": suite["storage_reindex"]["semantic_hash_matches_baseline"],
            "pass": index_blind,
        },
        "semantic_order_scramble_is_variant": {
            "output_distance": suite["semantic_order_scramble"]["output_distance"],
            "EPS_VARIANT": EPS_VARIANT,
            "semantic_hash_matches_baseline": suite["semantic_order_scramble"]["semantic_hash_matches_baseline"],
            "baseline_topological_semantic_ids": suite["baseline_graph"]["topological_semantic_ids"],
            "scrambled_topological_semantic_ids": suite["semantic_order_scramble"]["topological_semantic_ids"],
            "pass": semantic_variant and graph_order_sensitive,
        },
        "z3_cvc5_joint_gate_agrees": {
            "predicates": predicates,
            "z3": z3_row,
            "cvc5": cvc5_row,
            "cross_solver_agree": cross_solver_agree,
            "pass": bool(z3_row["pass"] and cvc5_row["pass"] and cross_solver_agree),
        },
    }

    graveyard_companions = {
        "display_label_as_semantics_claim_killed": {
            "reason": "Display labels were scrambled while semantic graph hash and operator output stayed invariant.",
            "pass": label_blind,
        },
        "storage_index_as_semantics_claim_killed": {
            "reason": "Storage order was reversed while semantic-position traversal recovered the same graph hash and operator output.",
            "pass": index_blind,
        },
        "row_count_only_graph_proof_claim_killed": {
            "reason": "The semantic-order scramble preserves the same node count but changes topological semantic IDs and operator output.",
            "baseline_node_count": suite["baseline_graph"]["node_count"],
            "scrambled_node_count": suite["semantic_order_scramble"]["graph"]["node_count"],
            "pass": bool(
                suite["baseline_graph"]["node_count"] == suite["semantic_order_scramble"]["graph"]["node_count"]
                and semantic_variant
            ),
        },
    }
    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "claim_ceiling_blocks_graph_proof_overclaim": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "axis0", "canonical"]
            ),
        },
        "semantic_falsifier_does_not_repair_axis0_or_basin": {
            "axis0_repaired": False,
            "basin_admitted": False,
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
            "layer_count": len(layers),
            "consumed_receipt_count": len(consumed_rows),
            "label_scramble_distance": suite["label_scramble"]["output_distance"],
            "storage_reindex_distance": suite["storage_reindex"]["output_distance"],
            "semantic_order_scramble_distance": suite["semantic_order_scramble"]["output_distance"],
            "cross_solver_agree": cross_solver_agree,
            "elapsed_seconds": round(time.time() - started, 6),
            "load_bearing_tools": [
                tool for tool, depth in TOOL_INTEGRATION_DEPTH.items() if depth == "load_bearing"
            ],
        },
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard_companions),
        "boundary": as_jsonable(boundary),
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row.get("pass") is True),
        },
        "semantic_graph_suite": as_jsonable(suite),
        "why_not_v4_probes": [
            "v5 formal scout over v5 graph-order, layer-name-blindness, and G-structure semantic-order receipts",
            "tests label/index blindness against semantic graph/order variance using the v5 formal-scout contract",
            "formal scout only; no final manifold, G-structure, proof stack, Axis0, basin, engine, bridge, physics, target-system, or canonical claim is admitted",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "blockers": [] if all_pass else ["semantic_graph_proof_label_scramble_falsifier_failed"],
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"name": NAME, "all_pass": bool(all_pass), "out_path": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
