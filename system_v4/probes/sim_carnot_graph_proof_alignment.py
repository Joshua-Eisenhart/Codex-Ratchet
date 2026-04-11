#!/usr/bin/env python3
"""
Carnot graph/proof alignment bridge.

Bounded bridge row that keeps the current Carnot exact row intact but adds:
  - a rustworkx stage-order graph for the forward/reverse cycle legs
  - z3 proofs for the reversible Carnot efficiency and refrigerator COP identities

This is not a runtime engine rewrite. It is a graph/proof-aware alignment lane
for the existing Carnot family.
"""

from __future__ import annotations

import json
import pathlib

import rustworkx as rx
import z3

import sim_qit_carnot_two_bath_cycle as base


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Graph/proof alignment bridge for the bounded Carnot engine family. It adds "
    "explicit stage-order graph structure and z3 proof surfaces around the "
    "reversible Carnot identities without claiming a runtime-geometry engine."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "carnot_cycle",
    "graph_shell_geometry",
]

PRIMARY_LEGO_IDS = [
    "quantum_thermodynamics",
    "carnot_cycle",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing algebraic proof surface for reversible Carnot efficiency and reverse COP identities",
    },
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing stage-order graph construction, topological order, and path-length checks",
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


def build_cycle_graph() -> dict:
    graph = rx.PyDiGraph()
    nodes = [
        "A_hot_high_gap_start",
        "B_hot_isotherm_low_gap",
        "C_adiabatic_expand_cold_low_gap",
        "D_cold_isotherm_high_gap",
        "A_return_hot_high_gap",
    ]
    idx = {label: graph.add_node(label) for label in nodes}
    graph.add_edge(idx["A_hot_high_gap_start"], idx["B_hot_isotherm_low_gap"], "hot_isotherm")
    graph.add_edge(idx["B_hot_isotherm_low_gap"], idx["C_adiabatic_expand_cold_low_gap"], "adiabatic_expand")
    graph.add_edge(idx["C_adiabatic_expand_cold_low_gap"], idx["D_cold_isotherm_high_gap"], "cold_isotherm")
    graph.add_edge(idx["D_cold_isotherm_high_gap"], idx["A_return_hot_high_gap"], "adiabatic_compress")
    topo = [graph[node] for node in rx.topological_sort(graph)]
    longest_path_nodes = [graph[node] for node in rx.dag_longest_path(graph)]
    return {
        "node_count": int(graph.num_nodes()),
        "edge_count": int(graph.num_edges()),
        "topological_order": topo,
        "longest_path": longest_path_nodes,
        "longest_path_length": max(len(longest_path_nodes) - 1, 0),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "source_count": int(sum(graph.in_degree(node) == 0 for node in graph.node_indices())),
        "sink_count": int(sum(graph.out_degree(node) == 0 for node in graph.node_indices())),
    }


def _rv(value: float) -> z3.ArithRef:
    return z3.RealVal(str(float(value)))


def prove_reversible_efficiency_identity(t_hot: float, t_cold: float) -> dict:
    solver = z3.Solver()
    q_hot = z3.Real("q_hot")
    q_cold = z3.Real("q_cold")
    work = z3.Real("work")
    eta = z3.Real("eta")
    th = _rv(t_hot)
    tc = _rv(t_cold)

    solver.add(q_hot > 0)
    solver.add(q_cold == -q_hot * tc / th)
    solver.add(work == q_hot + q_cold)
    solver.add(eta * q_hot == work)
    solver.add(eta != 1 - tc / th)

    verdict = solver.check()
    return {
        "verdict": str(verdict),
        "pass": verdict == z3.unsat,
        "claim": "Under reversible heat-ratio closure, Carnot efficiency identity is forced.",
    }


def prove_reversible_cop_identity(t_hot: float, t_cold: float) -> dict:
    solver = z3.Solver()
    q_cold = z3.Real("q_cold")
    work_in = z3.Real("work_in")
    cop = z3.Real("cop")
    th = _rv(t_hot)
    tc = _rv(t_cold)

    solver.add(q_cold > 0)
    solver.add(work_in == q_cold * (th - tc) / tc)
    solver.add(cop * work_in == q_cold)
    solver.add(cop != tc / (th - tc))

    verdict = solver.check()
    return {
        "verdict": str(verdict),
        "pass": verdict == z3.unsat,
        "claim": "Under reversible refrigerator bookkeeping, Carnot COP identity is forced.",
    }


def main() -> None:
    forward = base.forward_carnot_cycle(t_hot=2.0, t_cold=1.0, gap_high=3.0, gap_hot_low=1.0)
    reverse = base.reverse_refrigerator_cycle(forward)
    sweep = base.sweep_operating_points()
    graph_summary = build_cycle_graph()
    eff_proof = prove_reversible_efficiency_identity(
        t_hot=forward["parameters"]["t_hot"],
        t_cold=forward["parameters"]["t_cold"],
    )
    cop_proof = prove_reversible_cop_identity(
        t_hot=forward["parameters"]["t_hot"],
        t_cold=forward["parameters"]["t_cold"],
    )

    max_eff_gap = float(max(abs(row["efficiency"] - row["carnot_bound"]) for row in sweep))
    max_cop_gap = float(max(abs(row["cop"] - row["cop_carnot"]) for row in sweep))

    positive = {
        "forward_cycle_graph_is_a_single_valid_leg_chain": {
            **graph_summary,
            "pass": (
                graph_summary["is_dag"]
                and graph_summary["node_count"] == 5
                and graph_summary["edge_count"] == 4
                and graph_summary["source_count"] == 1
                and graph_summary["sink_count"] == 1
                and graph_summary["longest_path_length"] == 4
            ),
        },
        "z3_forces_the_reversible_carnot_efficiency_identity": eff_proof,
        "z3_forces_the_reversible_refrigerator_cop_identity": cop_proof,
        "measured_exact_row_matches_the_reversible_identities": {
            "forward_efficiency": float(forward["summary"]["efficiency"]),
            "forward_carnot_bound": float(forward["summary"]["carnot_bound"]),
            "reverse_cop": float(reverse["summary"]["cop"]),
            "reverse_cop_carnot": float(reverse["summary"]["cop_carnot"]),
            "pass": (
                abs(forward["summary"]["efficiency"] - forward["summary"]["carnot_bound"]) < 1e-10
                and abs(reverse["summary"]["cop"] - reverse["summary"]["cop_carnot"]) < 1e-10
            ),
        },
    }

    negative = {
        "sweep_does_not_break_the_reversible_bound_identity": {
            "max_efficiency_gap_abs": max_eff_gap,
            "max_cop_gap_abs": max_cop_gap,
            "pass": max_eff_gap < 1e-10 and max_cop_gap < 1e-10,
        },
        "graph_alignment_row_is_not_a_runtime_geometry_claim": {
            "scope_note": (
                "This row adds graph/proof structure around the exact Carnot cycle; it does not "
                "claim that the stochastic runtime rows already inherit graph-native mechanics."
            ),
            "pass": True,
        },
    }

    boundary = {
        "forward_graph_topological_order_matches_cycle_leg_order": {
            "topological_order": graph_summary["topological_order"],
            "pass": graph_summary["topological_order"] == [
                "A_hot_high_gap_start",
                "B_hot_isotherm_low_gap",
                "C_adiabatic_expand_cold_low_gap",
                "D_cold_isotherm_high_gap",
                "A_return_hot_high_gap",
            ],
        },
        "heat_work_signs_stay_engine_consistent": {
            "q_hot": float(forward["summary"]["q_hot"]),
            "q_cold": float(forward["summary"]["q_cold"]),
            "work_net": float(forward["summary"]["work_net"]),
            "pass": (
                forward["summary"]["q_hot"] > 0.0
                and forward["summary"]["q_cold"] < 0.0
                and forward["summary"]["work_net"] > 0.0
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "carnot_graph_proof_alignment",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "graph_summary": graph_summary,
        "summary": {
            "all_pass": all_pass,
            "graph_path_length": graph_summary["longest_path_length"],
            "cycle_schedule_valid": positive["forward_cycle_graph_is_a_single_valid_leg_chain"]["pass"],
            "efficiency_identity_unsat": eff_proof["pass"],
            "cop_identity_unsat": cop_proof["pass"],
            "forward_efficiency": float(forward["summary"]["efficiency"]),
            "forward_carnot_bound": float(forward["summary"]["carnot_bound"]),
            "reverse_cop": float(reverse["summary"]["cop"]),
            "reverse_cop_carnot": float(reverse["summary"]["cop_carnot"]),
            "scope_note": (
                "Graph/proof bridge around the exact Carnot row. Useful as a pre-constraint "
                "alignment surface before attempting graph-native runtime carriers."
            ),
        },
    }

    out_path = RESULT_DIR / "carnot_graph_proof_alignment_results.json"
    out_path.write_text(json.dumps(results, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
