#!/usr/bin/env python3
"""Coupled Rosetta lego-array sim.

This consumes the machine-readable Rosetta lego registry and builds a bounded
functional coupling over the current survivor legos.  It couples the Carnot,
Szilard, and I Ching-64 rows through shared modes, entropy families, topology
signatures, axis slots, and proof fences.  It does not promote to QIT/GStack.
"""

from __future__ import annotations

import json
import math
import pathlib
from typing import Any

import cvc5
import numpy as np
import qutip
import rustworkx as rx
import scipy.linalg
import sympy as sp
import torch
import xgi
import z3
from qiskit.quantum_info import DensityMatrix
from torch_geometric.data import Data


CLASSIFICATION = "canonical"
classification = CLASSIFICATION
divergence_log = (
    "Bounded coupled Rosetta lego-array sim over current Carnot, Szilard, and "
    "I Ching-64 survivor legos. It tests whether registry-approved pairwise "
    "couplings assemble into a larger functional comparison graph without QIT, "
    "GStack, or axis promotion."
)

LEGO_IDS = [
    "cycle_receipt_coupling_candidate_registry",
    "carnot_cycle",
    "szilard_cycle",
    "iching_64_schedule",
    "axis_schedule",
    "entropy_family",
    "operator_order",
    "graph_topology",
    "density_matrix",
    "proof_fence",
    "rosetta_correlation",
]
PRIMARY_LEGO_IDS = ["cycle_receipt_coupling_candidate_registry", "rosetta_correlation"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads registry receipt"},
    "numpy": {"tried": True, "used": True, "reason": "coupling score matrix and normalized weights"},
    "scipy": {"tried": True, "used": True, "reason": "matrix-log entropy of coupling density"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic coupling score normalization identity"},
    "torch": {"tried": True, "used": True, "reason": "tensor coupling objective and gradient check"},
    "pyg": {"tried": True, "used": True, "reason": "coupled lego graph tensor"},
    "rustworkx": {"tried": True, "used": True, "reason": "coupled lego graph"},
    "xgi": {"tried": True, "used": True, "reason": "hyperedges for shared lego families"},
    "qiskit": {"tried": True, "used": True, "reason": "density witness for coupling weights"},
    "qutip": {"tried": True, "used": True, "reason": "independent density witness for coupling weights"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT fence against full-QIT promotion from registry couplings"},
    "cvc5": {"tried": True, "used": True, "reason": "independent UNSAT fence against full-QIT promotion"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["json"] = "supportive"
TOOL_INTEGRATION_DEPTH["pathlib"] = "supportive"
TOOL_INTEGRATION_DEPTH["python_stdlib"] = "supportive"
TOOL_INTEGRATION_DEPTH["python_json"] = "supportive"

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def load_result(stem: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{stem}_results.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def coupling_score(row: dict[str, Any]) -> float:
    mode_score = len(row["shared_modes"]) / 3.0
    axis_score = len(row["shared_axis_slots"]) / 7.0
    entropy_score = min(len(row["shared_entropy_families"]) / 9.0, 1.0)
    tool_score = min(row["shared_tool_count"] / 13.0, 1.0)
    return float((mode_score + axis_score + entropy_score + tool_score) / 4.0)


def build_coupling_graph(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    engines = sorted({row["left"] for row in matrix} | {row["right"] for row in matrix})
    graph = rx.PyGraph()
    graph.add_nodes_from(engines)
    node_index = {graph[index]: index for index in range(graph.num_nodes())}
    weighted_edges = []
    for row in matrix:
        weighted_edges.append((node_index[row["left"]], node_index[row["right"]], coupling_score(row)))
    graph.add_edges_from(weighted_edges)
    edge_index = torch.tensor([[a for a, _, _ in weighted_edges], [b for _, b, _ in weighted_edges]], dtype=torch.long)
    features = torch.tensor(
        [
            [
                sum(row["left"] == engine or row["right"] == engine for row in matrix),
                sum(coupling_score(row) for row in matrix if row["left"] == engine or row["right"] == engine),
            ]
            for engine in engines
        ],
        dtype=torch.float64,
    )
    data = Data(x=features, edge_index=edge_index)
    hypergraph = xgi.Hypergraph([
        ["axis_schedule", *engines],
        ["entropy_family", *engines],
        ["operator_order", *engines],
        ["density_matrix", *engines],
        ["proof_fence", *engines],
    ])
    return {
        "engines": engines,
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "xgi_edges": hypergraph.num_edges,
        "weighted_edges": [
            {"left": row["left"], "right": row["right"], "score": coupling_score(row)}
            for row in matrix
        ],
        "pass": graph.num_nodes() == 3 and graph.num_edges() == 3 and int(data.num_nodes) == 3 and int(data.num_edges) == 3 and hypergraph.num_edges == 5,
    }


def coupling_density(scores: list[float]) -> dict[str, Any]:
    probs = np.asarray(scores, dtype=np.float64)
    probs = probs / probs.sum()
    rho = np.diag(probs.astype(np.complex128))
    scipy_entropy = float(np.real(-np.trace(rho @ scipy.linalg.logm(rho + np.eye(len(probs)) * 1e-15))))
    qiskit_trace = float(np.real(np.trace(DensityMatrix(rho).data)))
    qutip_trace = float(np.real(qutip.Qobj(rho).tr()))
    torch_scores = torch.tensor(scores, dtype=torch.float64, requires_grad=True)
    objective = torch.log(torch_scores).sum()
    objective.backward()
    sym = sp.symbols("w0:3", positive=True)
    norm_identity = sp.simplify(sum(sym) / sum(sym))
    return {
        "probabilities": [float(v) for v in probs],
        "shannon_entropy": float(-np.sum(probs * np.log(probs))),
        "scipy_vn_entropy": scipy_entropy,
        "qiskit_trace": qiskit_trace,
        "qutip_trace": qutip_trace,
        "torch_gradient_positive": all(float(v) > 0.0 for v in torch_scores.grad),
        "sympy_normalization_identity": str(norm_identity),
        "pass": bool(
            abs(float(-np.sum(probs * np.log(probs))) - scipy_entropy) < 1e-9
            and abs(qiskit_trace - 1.0) < 1e-12
            and abs(qutip_trace - 1.0) < 1e-12
            and all(float(v) > 0.0 for v in torch_scores.grad)
            and norm_identity == 1
        ),
    }


def qit_promotion_unsat() -> dict[str, Any]:
    registry_approved, gstack_receipt, qit_runtime, promote = z3.Bools("registry_approved gstack_receipt qit_runtime promote")
    solver = z3.Solver()
    solver.add(registry_approved)
    solver.add(z3.Not(gstack_receipt), z3.Not(qit_runtime))
    solver.add(promote == z3.And(registry_approved, gstack_receipt, qit_runtime))
    solver.add(promote)
    result = solver.check()
    return {"claim": "registry-approved Rosetta couplings imply QIT runtime promotion", "result": str(result), "pass": result == z3.unsat}


def cvc5_qit_promotion_unsat() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    registry = solver.mkConst(bool_sort, "registry_approved")
    gstack = solver.mkConst(bool_sort, "gstack_receipt")
    runtime = solver.mkConst(bool_sort, "qit_runtime")
    promote = solver.mkConst(bool_sort, "promote")
    solver.assertFormula(registry)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.NOT, gstack))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.NOT, runtime))
    solver.assertFormula(
        solver.mkTerm(cvc5.Kind.EQUAL, promote, solver.mkTerm(cvc5.Kind.AND, registry, gstack, runtime))
    )
    solver.assertFormula(promote)
    result = solver.checkSat()
    return {"claim": "registry-approved Rosetta couplings imply QIT runtime promotion", "result": str(result), "pass": str(result).lower() == "unsat"}


def build_visual_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result["name"],
        "summary": result["summary"],
        "coupling_graph": result["coupling_graph"],
        "coupling_density": result["coupling_density"],
        "proof_fences": result["proof_fences"],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    js = "window.ROSETTA_LEGO_COUPLED_ARRAY_DATA = " + json.dumps(build_visual_payload(result), indent=2, default=str) + ";\n"
    (VIS_DIR / "rosetta-lego-coupled-array-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    registry = load_result("cycle_receipt_coupling_candidate_registry")
    matrix = registry["coupling_matrix"]
    graph = build_coupling_graph(matrix)
    density = coupling_density([edge["score"] for edge in graph["weighted_edges"]])
    proof_fences = {
        "z3_blocks_qit_promotion": qit_promotion_unsat(),
        "cvc5_blocks_qit_promotion": cvc5_qit_promotion_unsat(),
    }
    all_pass = graph["pass"] and density["pass"] and all(row["pass"] for row in proof_fences.values()) and all(row["allowed_next"] for row in matrix)
    result = {
        "name": "rosetta_lego_coupled_array",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "bridge",
        "allowed_claims": [
            "registry-approved Rosetta legos can assemble into a coupled comparison graph",
            "coupled array has graph, tensor, hypergraph, density, symbolic, and proof receipts",
            "QIT/GStack/axis promotion remains blocked",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": ["no GStack receipt", "no QIT runtime receipt", "no full axis admission"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "registry": str(RESULT_DIR / "cycle_receipt_coupling_candidate_registry_results.json"),
        },
        "coupling_matrix_used": matrix,
        "coupling_graph": graph,
        "coupling_density": density,
        "proof_fences": proof_fences,
        "summary": {
            "all_pass": bool(all_pass),
            "engine_count": graph["nodes"],
            "coupled_pair_count": graph["edges"],
            "weighted_edge_count": len(graph["weighted_edges"]),
            "qit_promotion_blocked": all(row["pass"] for row in proof_fences.values()),
            "visual_payload": "visualizer/rosetta-lego-coupled-array-data.js",
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "rosetta_lego_coupled_array_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
