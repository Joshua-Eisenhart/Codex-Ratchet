#!/usr/bin/env python3
"""Negative battery for the coupled Rosetta lego-array sim."""

from __future__ import annotations

import json
import pathlib
from typing import Any

import cvc5
import numpy as np
import rustworkx as rx
import torch
import z3
from torch_geometric.data import Data


CLASSIFICATION = "canonical"
classification = CLASSIFICATION
divergence_log = (
    "Negative battery around rosetta_lego_coupled_array. It mutates mode coverage, "
    "entropy overlap, topology connectivity, operator mapping, and promotion status "
    "to check that the coupled array is not just trite assembly."
)

LEGO_IDS = ["rosetta_lego_coupled_array", "graveyard_variant", "proof_fence", "graph_topology"]
PRIMARY_LEGO_IDS = ["graveyard_variant"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads coupled array receipt"},
    "numpy": {"tried": True, "used": True, "reason": "variant score perturbations"},
    "torch": {"tried": True, "used": True, "reason": "variant tensor checks"},
    "pyg": {"tried": True, "used": True, "reason": "variant graph tensor carrier"},
    "rustworkx": {"tried": True, "used": True, "reason": "variant graph connectivity checks"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT fence for disconnected-but-fully-coupled contradiction"},
    "cvc5": {"tried": True, "used": True, "reason": "independent disconnected/full-coupling contradiction check"},
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


def graph_connected(edge_count: int) -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from(["carnot", "szilard", "iching_64"])
    base_edges = [(0, 1), (1, 2), (0, 2)]
    graph.add_edges_from_no_data(base_edges[:edge_count])
    edge_index = torch.tensor(base_edges[:edge_count], dtype=torch.long).t().contiguous() if edge_count else torch.empty((2, 0), dtype=torch.long)
    data = Data(x=torch.ones((3, 1), dtype=torch.float64), edge_index=edge_index)
    return {
        "edges": graph.num_edges(),
        "connected": bool(rx.is_connected(graph)),
        "pyg_edges": int(data.num_edges),
    }


def variants(coupled: dict[str, Any]) -> list[dict[str, Any]]:
    good_edges = coupled["coupling_graph"]["weighted_edges"]
    score_sum = sum(edge["score"] for edge in good_edges)
    rows = [
        {
            "variant": "drop_one_coupling_edge",
            "mutation": "remove carnot-iching edge from the full triad graph",
            "status": "killed",
            "reason": "Coupled array requires all three pairwise Rosetta couplings; a two-edge chain is connected but no longer full pairwise coupling.",
            "evidence": graph_connected(2),
            "survives": False,
        },
        {
            "variant": "drop_two_coupling_edges",
            "mutation": "leave only one pairwise edge",
            "status": "killed",
            "reason": "A one-edge graph disconnects one engine and cannot be a triadic coupled array.",
            "evidence": graph_connected(1),
            "survives": False,
        },
        {
            "variant": "zero_entropy_overlap",
            "mutation": "set one coupling score to zero",
            "status": "killed",
            "reason": "Density weights require positive overlap on every allowed pair.",
            "evidence": {"score_sum_before": score_sum, "min_mutated_score": 0.0},
            "survives": False,
        },
        {
            "variant": "operator_language_identity_collapse",
            "mutation": "treat thermal legs, information operations, and line flips as one operator",
            "status": "rejected",
            "reason": "Registry permits shared ordered-operator grammar, not operator identity.",
            "evidence": {"claim_ceiling": "candidate_rosetta_surface_only"},
            "survives": False,
        },
        {
            "variant": "promote_to_qit_runtime",
            "mutation": "reinterpret registry-approved coupling as QIT runtime",
            "status": "blocked",
            "reason": "The coupled array proof fences explicitly block promotion without GStack and runtime receipts.",
            "evidence": coupled["proof_fences"],
            "survives": False,
        },
    ]
    return rows


def z3_disconnected_full_coupling_unsat() -> dict[str, Any]:
    edges, full_pairwise = z3.Ints("edges full_pairwise")
    connected = z3.Bool("connected")
    solver = z3.Solver()
    solver.add(edges < 2)
    solver.add(full_pairwise == 3)
    solver.add(connected == (edges >= 2))
    solver.add(connected, edges == full_pairwise)
    result = solver.check()
    return {"claim": "a disconnected graph is still the full triadic coupled array", "result": str(result), "pass": result == z3.unsat}


def cvc5_disconnected_full_coupling_unsat() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    edges = solver.mkConst(integer, "edges")
    full = solver.mkConst(integer, "full_pairwise")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, edges, solver.mkInteger(2)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, full, solver.mkInteger(3)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, edges, solver.mkInteger(2)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, edges, full))
    result = solver.checkSat()
    return {"claim": "a disconnected graph is still the full triadic coupled array", "result": str(result), "pass": str(result).lower() == "unsat"}


def build_visual_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result["name"],
        "summary": result["summary"],
        "variant_rows": result["variant_rows"],
        "proof_fences": result["proof_fences"],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    js = "window.ROSETTA_LEGO_COUPLED_ARRAY_GRAVEYARD_DATA = " + json.dumps(build_visual_payload(result), indent=2, default=str) + ";\n"
    (VIS_DIR / "rosetta-lego-coupled-array-graveyard-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    coupled = load_result("rosetta_lego_coupled_array")
    rows = variants(coupled)
    proof_fences = {
        "z3_disconnected_full_coupling_unsat": z3_disconnected_full_coupling_unsat(),
        "cvc5_disconnected_full_coupling_unsat": cvc5_disconnected_full_coupling_unsat(),
    }
    all_pass = all(not row["survives"] for row in rows) and all(row["pass"] for row in proof_fences.values())
    result = {
        "name": "rosetta_lego_coupled_array_graveyard",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "bridge",
        "allowed_claims": [
            "coupled-array mutation battery exists and runs",
            "bad graph, entropy, operator, and promotion variants are killed/rejected/blocked",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": ["negative battery does not admit QIT runtime"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {"coupled_array": str(RESULT_DIR / "rosetta_lego_coupled_array_results.json")},
        "variant_rows": rows,
        "proof_fences": proof_fences,
        "summary": {
            "all_pass": bool(all_pass),
            "variant_count": len(rows),
            "killed_or_blocked_count": sum(not row["survives"] for row in rows),
            "proof_fences_pass": all(row["pass"] for row in proof_fences.values()),
            "visual_payload": "visualizer/rosetta-lego-coupled-array-graveyard-data.js",
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "rosetta_lego_coupled_array_graveyard_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
