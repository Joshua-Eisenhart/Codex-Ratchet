#!/usr/bin/env python3
"""
PURE LEGO: Engine Protocol DAG
==============================
Reusable protocol-order lego for Carnot and Szilard stage schedules.

This lane is intentionally narrow:
  - rustworkx is load-bearing for protocol DAG structure
  - z3 is load-bearing for precedence impossibility proofs
  - no stochastic runtime carrier is embedded here

It serves as a base lego for later engine rows, not as a single engine sim.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Iterable

import rustworkx as rx
import z3


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical protocol-DAG lego for Carnot and Szilard stage ordering. "
    "It keeps the graph/proof layer reusable and separate from stochastic "
    "runtime carriers."
)

LEGO_IDS = [
    "engine_protocol_dag",
    "protocol_schedule_legality",
]

PRIMARY_LEGO_IDS = [
    "engine_protocol_dag",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing precedence impossibility proofs for protocol schedules",
    },
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite protocol DAG construction, source/sink checks, and topological ordering",
    },
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


@dataclass(frozen=True)
class ProtocolFamily:
    family: str
    stages: list[str]
    edges: list[tuple[str, str]]
    negative_cycle_edge: tuple[str, str]
    negative_label: str


FAMILIES = [
    ProtocolFamily(
        family="carnot",
        stages=[
            "hot_isotherm",
            "adiabatic_expand",
            "cold_isotherm",
            "adiabatic_compress",
        ],
        edges=[
            ("hot_isotherm", "adiabatic_expand"),
            ("adiabatic_expand", "cold_isotherm"),
            ("cold_isotherm", "adiabatic_compress"),
        ],
        negative_cycle_edge=("adiabatic_compress", "hot_isotherm"),
        negative_label="closed_cycle_back_edge",
    ),
    ProtocolFamily(
        family="szilard",
        stages=[
            "measurement",
            "feedback",
            "reset",
        ],
        edges=[
            ("measurement", "feedback"),
            ("feedback", "reset"),
        ],
        negative_cycle_edge=("reset", "measurement"),
        negative_label="closed_protocol_back_edge",
    ),
]


def _build_graph(stages: Iterable[str], edges: Iterable[tuple[str, str]]) -> dict:
    graph = rx.PyDiGraph()
    node_index = {stage: graph.add_node(stage) for stage in stages}
    for source, target in edges:
        graph.add_edge(node_index[source], node_index[target], f"{source}->{target}")

    is_dag = bool(rx.is_directed_acyclic_graph(graph))
    if is_dag:
        topological_order = [graph[node] for node in rx.topological_sort(graph)]
        longest_path = [graph[node] for node in rx.dag_longest_path(graph)]
    else:
        topological_order = None
        longest_path = None
    sources = [graph[node] for node in graph.node_indices() if graph.in_degree(node) == 0]
    sinks = [graph[node] for node in graph.node_indices() if graph.out_degree(node) == 0]

    return {
        "node_count": int(graph.num_nodes()),
        "edge_count": int(graph.num_edges()),
        "is_dag": is_dag,
        "topological_order": topological_order,
        "longest_path": longest_path,
        "longest_path_length": max(len(longest_path) - 1, 0) if longest_path is not None else None,
        "sources": sources,
        "sinks": sinks,
    }


def _prove_order_constraints(stages: list[str], edges: list[tuple[str, str]]) -> dict:
    solver = z3.Solver()
    pos = {stage: z3.Int(stage) for stage in stages}

    n = len(stages)
    for stage in stages:
        solver.add(pos[stage] >= 0, pos[stage] < n)
    solver.add(z3.Distinct([pos[stage] for stage in stages]))
    for source, target in edges:
        solver.add(pos[source] < pos[target])

    sat_correct_order = solver.check()

    reverse_solver = z3.Solver()
    for stage in stages:
        reverse_solver.add(pos[stage] >= 0, pos[stage] < n)
    reverse_solver.add(z3.Distinct([pos[stage] for stage in stages]))
    for source, target in edges:
        reverse_solver.add(pos[source] < pos[target])
    reverse_solver.add(pos[stages[-1]] < pos[stages[0]])
    reverse_verdict = reverse_solver.check()

    return {
        "correct_order_verdict": str(sat_correct_order),
        "correct_order_sat": sat_correct_order == z3.sat,
        "reverse_order_verdict": str(reverse_verdict),
        "reverse_order_unsat": reverse_verdict == z3.unsat,
    }


def _prove_cycle_control(stages: list[str], edges: list[tuple[str, str]], cycle_edge: tuple[str, str]) -> dict:
    solver = z3.Solver()
    pos = {stage: z3.Int(stage) for stage in stages}
    n = len(stages)

    for stage in stages:
        solver.add(pos[stage] >= 0, pos[stage] < n)
    solver.add(z3.Distinct([pos[stage] for stage in stages]))
    for source, target in edges + [cycle_edge]:
        solver.add(pos[source] < pos[target])

    verdict = solver.check()

    cycle_graph = _build_graph(stages, edges + [cycle_edge])
    return {
        "cycle_edge": f"{cycle_edge[0]}->{cycle_edge[1]}",
        "z3_verdict": str(verdict),
        "z3_unsat": verdict == z3.unsat,
        "graph_is_dag": cycle_graph["is_dag"],
        "graph_topological_order": cycle_graph["topological_order"],
    }


def build_family_row(family: ProtocolFamily) -> dict:
    graph = _build_graph(family.stages, family.edges)
    proof = _prove_order_constraints(family.stages, family.edges)
    cycle_control = _prove_cycle_control(family.stages, family.edges, family.negative_cycle_edge)

    positive = {
        "dag_is_acyclic_and_orderable": {
            **graph,
            "pass": (
                graph["is_dag"]
                and graph["node_count"] == len(family.stages)
                and graph["edge_count"] == len(family.edges)
                and graph["sources"] == [family.stages[0]]
                and graph["sinks"] == [family.stages[-1]]
            ),
        },
        "z3_correct_order_is_sat": {
            **proof,
            "pass": proof["correct_order_sat"],
        },
    }

    negative = {
        "reverse_order_is_unsat": {
            **proof,
            "pass": proof["reverse_order_unsat"],
        },
        "cycle_control_is_unsat": {
            **cycle_control,
            "pass": cycle_control["z3_unsat"] and (cycle_control["graph_is_dag"] is False),
        },
    }

    boundary = {
        "source_sink_structure_is_single_entry_single_exit": {
            "sources": graph["sources"],
            "sinks": graph["sinks"],
            "pass": graph["sources"] == [family.stages[0]] and graph["sinks"] == [family.stages[-1]],
        },
        "topological_order_matches_declared_protocol": {
            "topological_order": graph["topological_order"],
            "pass": graph["topological_order"] == family.stages,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    return {
        "family": family.family,
        "stages": family.stages,
        "edges": [f"{a}->{b}" for a, b in family.edges],
        "negative_control": family.negative_label,
        "graph": graph,
        "proofs": {
            "order_constraints": proof,
            "cycle_control": cycle_control,
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "node_count": graph["node_count"],
            "edge_count": graph["edge_count"],
            "source_count": len(graph["sources"]),
            "sink_count": len(graph["sinks"]),
            "longest_path_length": graph["longest_path_length"],
            "cycle_control_unsat": cycle_control["z3_unsat"],
            "scope_note": (
                "Reusable protocol-order lego for engine families. It encodes stage DAGs, "
                "source/sink structure, precedence legality, and a small cycle negative control."
            ),
        },
    }


def main() -> None:
    rows = [build_family_row(family) for family in FAMILIES]
    all_pass = all(row["summary"]["all_pass"] for row in rows)

    results = {
        "name": "engine_protocol_dag",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "rows": rows,
        "summary": {
            "all_pass": all_pass,
            "family_count": len(rows),
            "passed_family_count": sum(1 for row in rows if row["summary"]["all_pass"]),
            "graph_tool": "rustworkx",
            "proof_tool": "z3",
            "scope_note": (
                "Reusable graph/proof lego for finite protocol schedules. The DAG is the "
                "core object, and the solver checks precedence impossibility."
            ),
        },
    }

    out_path = RESULT_DIR / "engine_protocol_dag_results.json"
    out_path.write_text(json.dumps(results, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
