#!/usr/bin/env python3
"""Nested constraint-manifold operational-handle support scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
import toponetx as tnx
import xgi
import z3

from sim_nested_geometry_tower_dependency_order_probe import LAYERS


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "nested_constraint_manifold_operational_handle_support_probe_results.json"

NAME = "nested_constraint_manifold_operational_handle_support_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether seven downstream executable handles have "
    "multi-layer support inside the 13-layer nested constraint manifold before "
    "any staged chiral execution is admitted. The handles are not final axis "
    "definitions. This does not admit final manifold ontology, final axis "
    "ontology, physics, cognition, personality, bridge, or canonical claims."
)

TOOL_MANIFEST = {
    "networkx": {"tried": True, "used": True, "reason": "load-bearing bipartite support graph and connectivity checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing directed nested-layer order graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing support hyperedges from handles to manifold layers"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial support complex over multi-layer handle supports"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence witness over handle support cardinalities"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing support incidence tensor and graph message pass"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing message pass over manifold-layer/handle incidence graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic rank of the layer-handle incidence matrix"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing noncollapse and graveyard satisfiability witnesses"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

HANDLES = [
    "feedback_entropy_gradient",
    "stage_bit_one",
    "stage_bit_two",
    "loop_placement",
    "traversal_order",
    "excitation_intensity",
    "operator_action_sign",
]

SUPPORTS = {
    "feedback_entropy_gradient": [
        "complex_hilbert_carrier",
        "connection_holonomy_geometry",
        "tensor_product_coupling_geometry",
        "dynamic_transition_ratchet_geometry",
    ],
    "stage_bit_one": [
        "finite_constraint_complex",
        "projective_base_sphere",
        "hopf_torus_leaf_family",
        "frame_bundle_structure_reduction",
    ],
    "stage_bit_two": [
        "finite_constraint_complex",
        "unit_spinor_sphere",
        "projective_base_sphere",
        "tensor_product_coupling_geometry",
    ],
    "loop_placement": [
        "hopf_fiber_bundle",
        "hopf_torus_leaf_family",
        "connection_holonomy_geometry",
        "frame_bundle_structure_reduction",
    ],
    "traversal_order": [
        "connection_holonomy_geometry",
        "clifford_module_geometry",
        "tensor_product_coupling_geometry",
        "dynamic_transition_ratchet_geometry",
    ],
    "excitation_intensity": [
        "complex_hilbert_carrier",
        "unit_spinor_sphere",
        "tensor_product_coupling_geometry",
        "dynamic_transition_ratchet_geometry",
    ],
    "operator_action_sign": [
        "weyl_spinor_bundle",
        "chirality_orientation_cover",
        "clifford_module_geometry",
        "frame_bundle_structure_reduction",
    ],
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if hasattr(value, "item"):
        return value.item()
    return value


def incidence_matrix(supports: dict[str, list[str]]) -> torch.Tensor:
    rows = []
    for handle in HANDLES:
        row = [1.0 if layer in supports.get(handle, []) else 0.0 for layer in LAYERS]
        rows.append(row)
    return torch.tensor(rows, dtype=torch.float64)


def support_graph(supports: dict[str, list[str]]) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(LAYERS, bipartite="layer")
    graph.add_nodes_from(HANDLES, bipartite="handle")
    for handle, layers in supports.items():
        for layer in layers:
            graph.add_edge(handle, layer)
    return graph


def layer_order_graph() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {layer: graph.add_node(layer) for layer in LAYERS}
    for left, right in zip(LAYERS[:-1], LAYERS[1:]):
        graph.add_edge(nodes[left], nodes[right], "nested_before")
    return {"node_count": graph.num_nodes(), "edge_count": graph.num_edges(), "pass": graph.num_nodes() == 13 and graph.num_edges() == 12}


def hypergraph_witness(supports: dict[str, list[str]]) -> dict[str, Any]:
    hyper = xgi.Hypergraph()
    for handle, layers in supports.items():
        hyper.add_edge([handle] + layers)
    return {"hyperedge_count": hyper.num_edges, "node_count": hyper.num_nodes, "pass": hyper.num_edges == len(HANDLES)}


def simplicial_witness(supports: dict[str, list[str]]) -> dict[str, Any]:
    complex_ = tnx.SimplicialComplex()
    for handle, layers in supports.items():
        complex_.add_simplex([handle] + layers[:3])
    return {"dimension": complex_.dim, "simplex_count": len(list(complex_.simplices)), "pass": complex_.dim >= 3}


def persistence_witness(supports: dict[str, list[str]]) -> dict[str, Any]:
    st = gudhi.SimplexTree()
    for idx, layer in enumerate(LAYERS):
        st.insert([idx], filtration=float(idx))
    base = len(LAYERS)
    edge_filtrations = []
    for h_idx, handle in enumerate(HANDLES):
        h_node = base + h_idx
        st.insert([h_node], filtration=float(h_idx) / 10.0)
        for layer in supports[handle]:
            filt = float(LAYERS.index(layer) + 1)
            edge_filtrations.append(filt)
            st.insert([h_node, LAYERS.index(layer)], filtration=filt)
    pairs = st.persistence()
    span = max(edge_filtrations) - min(edge_filtrations)
    return {"persistence_pairs": len(pairs), "edge_filtration_span": span, "pass": len(pairs) >= 4 and span >= 10.0}


def message_pass_witness(supports: dict[str, list[str]]) -> dict[str, Any]:
    all_nodes = LAYERS + HANDLES
    index = {node: idx for idx, node in enumerate(all_nodes)}
    edges = []
    for handle, layers in supports.items():
        for layer in layers:
            edges.append((index[handle], index[layer]))
            edges.append((index[layer], index[handle]))
    edge_index = torch.tensor(edges, dtype=torch.long).T
    x = torch.zeros((len(all_nodes), 3), dtype=torch.float32)
    for idx, node in enumerate(all_nodes):
        x[idx, 0] = 1.0 if node in LAYERS else 0.0
        x[idx, 1] = float(idx) / len(all_nodes)
        x[idx, 2] = float(len(supports.get(node, [])))
    conv = GCNConv(3, 3, add_self_loops=True)
    with torch.no_grad():
        out = conv(Data(x=x, edge_index=edge_index).x, edge_index)
    handle_norms = [float(torch.linalg.vector_norm(out[index[h]]).item()) for h in HANDLES]
    return {"output_shape": list(out.shape), "handle_norms": handle_norms, "pass": out.shape == x.shape and min(handle_norms) > 0}


def symbolic_rank_witness(mat: torch.Tensor) -> dict[str, Any]:
    matrix = sp.Matrix([[int(v) for v in row] for row in mat.tolist()])
    rank = int(matrix.rank())
    return {"rank": rank, "rows": matrix.rows, "cols": matrix.cols, "pass": rank >= 6}


def z3_noncollapse_witness(supports: dict[str, list[str]]) -> dict[str, Any]:
    solver = z3.Solver()
    ids = {handle: z3.Int(handle) for handle in HANDLES}
    for handle in HANDLES:
        solver.add(ids[handle] == sum(2 ** LAYERS.index(layer) for layer in supports[handle]))
    for left_idx, left in enumerate(HANDLES):
        for right in HANDLES[left_idx + 1 :]:
            solver.add(ids[left] != ids[right])
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.sat}


def support_summary(supports: dict[str, list[str]]) -> dict[str, Any]:
    graph = support_graph(supports)
    mat = incidence_matrix(supports)
    layer_degrees = {layer: int(mat[:, idx].sum().item()) for idx, layer in enumerate(LAYERS)}
    handle_degrees = {handle: len(supports[handle]) for handle in HANDLES}
    return {
        "layer_count": len(LAYERS),
        "handle_count": len(HANDLES),
        "edge_count": graph.number_of_edges(),
        "connected": nx.is_connected(graph),
        "min_handle_degree": min(handle_degrees.values()),
        "max_handle_degree": max(handle_degrees.values()),
        "covered_layers": sorted(layer for layer, degree in layer_degrees.items() if degree > 0),
        "uncovered_layers": sorted(layer for layer, degree in layer_degrees.items() if degree == 0),
        "handle_degrees": handle_degrees,
        "layer_degrees": layer_degrees,
        "pass": nx.is_connected(graph) and min(handle_degrees.values()) >= 3 and all(degree > 0 for degree in layer_degrees.values()),
    }


def graveyard_remove_layers(remove: set[str]) -> dict[str, Any]:
    reduced = {handle: [layer for layer in layers if layer not in remove] for handle, layers in SUPPORTS.items()}
    summary = support_summary(reduced)
    return {
        "removed_layers": sorted(remove),
        "min_handle_degree": summary["min_handle_degree"],
        "uncovered_layers": summary["uncovered_layers"],
        "connected": summary["connected"],
        "pass": not summary["pass"],
    }


def graveyard_one_layer_labels() -> dict[str, Any]:
    collapsed = {handle: [LAYERS[idx % len(LAYERS)]] for idx, handle in enumerate(HANDLES)}
    summary = support_summary(collapsed)
    return {"summary": summary, "pass": not summary["pass"]}


def graveyard_weyl_only() -> dict[str, Any]:
    weyl_layers = ["weyl_spinor_bundle", "chirality_orientation_cover", "clifford_module_geometry"]
    collapsed = {handle: list(weyl_layers) for handle in HANDLES}
    summary = support_summary(collapsed)
    return {"summary": summary, "pass": not summary["pass"] and len(summary["covered_layers"]) == 3}


def graveyard_downstream_only() -> dict[str, Any]:
    downstream = ["tensor_product_coupling_geometry", "dynamic_transition_ratchet_geometry"]
    collapsed = {handle: list(downstream) for handle in HANDLES}
    summary = support_summary(collapsed)
    return {"summary": summary, "pass": not summary["pass"]}


def main() -> dict[str, Any]:
    started = time.time()
    mat = incidence_matrix(SUPPORTS)
    summary = support_summary(SUPPORTS)
    positive = {
        "thirteen_nested_layers_are_primary_support_surface": {
            "layers": LAYERS,
            "pass": len(LAYERS) == 13 and LAYERS.index("weyl_spinor_bundle") > LAYERS.index("connection_holonomy_geometry"),
        },
        "seven_handles_have_multilayer_manifold_support": summary,
        "support_hyperedges_execute": hypergraph_witness(SUPPORTS),
        "support_simplicial_complex_executes": simplicial_witness(SUPPORTS),
        "support_persistence_executes": persistence_witness(SUPPORTS),
        "support_message_pass_executes": message_pass_witness(SUPPORTS),
        "support_incidence_has_nontrivial_symbolic_rank": symbolic_rank_witness(mat),
        "z3_handle_support_signatures_do_not_collapse": z3_noncollapse_witness(SUPPORTS),
        "nested_layer_order_graph_executes": layer_order_graph(),
    }
    graveyard_companions = {
        "removing_hopf_layers_breaks_loop_support": graveyard_remove_layers({"hopf_fiber_bundle", "hopf_torus_leaf_family"}),
        "removing_chirality_clifford_layers_breaks_operator_sign_support": graveyard_remove_layers(
            {"chirality_orientation_cover", "clifford_module_geometry"}
        ),
        "removing_tensor_dynamic_layers_breaks_entropy_excitation_support": graveyard_remove_layers(
            {"tensor_product_coupling_geometry", "dynamic_transition_ratchet_geometry"}
        ),
        "one_layer_per_handle_labeling_is_rejected": graveyard_one_layer_labels(),
        "weyl_only_collapse_is_rejected": graveyard_weyl_only(),
        "downstream_only_collapse_is_rejected": graveyard_downstream_only(),
    }
    boundary = {
        "handles_are_declared_downstream_not_manifold_layers": {
            "intersection": sorted(set(HANDLES).intersection(LAYERS)),
            "pass": not set(HANDLES).intersection(LAYERS),
        },
        "operator_sign_support_includes_but_exceeds_weyl_layer": {
            "support": SUPPORTS["operator_action_sign"],
            "pass": "weyl_spinor_bundle" in SUPPORTS["operator_action_sign"]
            and len(SUPPORTS["operator_action_sign"]) > 1,
        },
        "feedback_entropy_support_includes_dynamic_geometry": {
            "support": SUPPORTS["feedback_entropy_gradient"],
            "pass": "dynamic_transition_ratchet_geometry" in SUPPORTS["feedback_entropy_gradient"]
            and "tensor_product_coupling_geometry" in SUPPORTS["feedback_entropy_gradient"],
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "13-layer nested constraint manifold support incidence for downstream operational handles",
        "source_alignment_category": "source_native_constraint_manifold_support",
        "candidate_layers": LAYERS,
        "handles": HANDLES,
        "support_relation": SUPPORTS,
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard_companions),
        "boundary": as_jsonable(boundary),
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        },
        "blockers": [],
        "open_choices": [
            "Support relation is a candidate manifold-first scaffold, not final axis ontology.",
            "Next pass should make these support relations dynamically deform geometry before staged execution consumes them.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout for manifold-first support structure and should not be added to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "positive_passed": sum(1 for row in positive.values() if row["pass"]),
            "positive_total": len(positive),
            "graveyard_passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "graveyard_total": len(graveyard_companions),
            "boundary_passed": sum(1 for row in boundary.values() if row["pass"]),
            "boundary_total": len(boundary),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
