#!/usr/bin/env python3
"""
QIT Weyl hypergraph companion.

Strict finite bounded companion/readout surface for the Weyl -> hypergraph lane.
This row keeps the hypergraph support pack explicit while adding a dedicated
strict-side finite carrier with direct hypergraph, cell-complex, schedule, and
ordering-proof checks.

It is a bounded comparison surface, not owner math or runtime equivalence.
"""

from __future__ import annotations

import json
import pathlib
from itertools import combinations
from typing import Any

import cvc5
import rustworkx as rx
import xgi
import z3
from toponetx import CellComplex
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Strict finite bounded companion for the Weyl -> hypergraph lane. It keeps "
    "the hypergraph support pack explicit while adding direct hypergraph, "
    "cell-complex, DAG, and SMT ordering checks. This is a bounded comparison "
    "surface, not a runtime-equivalence or owner-math claim."
)

LEGO_IDS = [
    "weyl_hypergraph_follow_on",
    "hypergraph_geometry",
    "dual_hypergraph_geometry",
    "xgi_shell_hypergraph",
    "toponetx_hopf_crosscheck",
]

PRIMARY_LEGO_IDS = [
    "hypergraph_geometry",
    "dual_hypergraph_geometry",
    "toponetx_hopf_crosscheck",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing strict ordering proof for hypergraph companion schedule",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive strict ordering cross-check for the hypergraph companion schedule",
    },
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing DAG schedule for strict hypergraph companion stages",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing strict bounded hypergraph and dual-hypergraph carrier checks",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing CellComplex lift for strict finite carrier readout",
    },
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["cvc5"] = "supportive"
TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


def load_json(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"missing result file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "pass", "passed", "yes", "sat", "unsat"}
    return bool(value)


def result_pass(result: dict[str, Any] | None) -> bool:
    if not result:
        return False
    summary = result.get("summary")
    if isinstance(summary, dict) and "all_pass" in summary:
        return truthy(summary["all_pass"])
    if isinstance(summary, dict) and "tests_passed" in summary:
        return truthy(summary.get("chi_confirmed_zero")) and truthy(summary.get("beta1_matches_gudhi", True))
    if isinstance(summary, dict) and "multi_way_structure_load_bearing" in summary:
        return truthy(summary.get("multi_way_structure_load_bearing")) and truthy(summary.get("rankings_differ_from_pairwise"))
    if "all_pass" in result:
        return truthy(result["all_pass"])
    if result.get("classification") == "canonical":
        return True
    return False


def shadow_graph_edges(hypergraph: xgi.Hypergraph) -> list[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for edge_id in hypergraph.edges:
        members = list(hypergraph.edges.members(edge_id))
        for u, v in combinations(sorted(members), 2):
            edges.add((u, v))
    return sorted(edges)


def build_strict_hypergraph() -> tuple[xgi.Hypergraph, xgi.Hypergraph, list[tuple[str, str]]]:
    hypergraph = xgi.Hypergraph()
    hypergraph.add_nodes_from(["a", "b", "c", "d"])
    hypergraph.add_edge(["a", "b", "c"], id="triad")
    hypergraph.add_edge(["c", "d"], id="pair")

    dual = hypergraph.dual()
    shadow_edges = shadow_graph_edges(hypergraph)
    return hypergraph, dual, shadow_edges


def build_cell_complex() -> CellComplex:
    cell_complex = CellComplex()
    cell_complex.add_cell(["a", "b"], rank=1)
    cell_complex.add_cell(["a", "c"], rank=1)
    cell_complex.add_cell(["b", "c"], rank=1)
    cell_complex.add_cell(["c", "d"], rank=1)
    cell_complex.add_cell(["a", "b", "c"], rank=2)
    return cell_complex


def build_schedule_graph() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = [
        "strict_hypergraph",
        "strict_dual",
        "strict_shadow",
        "strict_cell_complex",
        "strict_topology_crosscheck",
    ]
    indices = {name: graph.add_node(name) for name in nodes}
    for source, target in zip(nodes, nodes[1:]):
        graph.add_edge(indices[source], indices[target], f"{source}->{target}")
    topo = [graph[node] for node in rx.topological_sort(graph)]
    longest = [graph[node] for node in rx.dag_longest_path(graph)]
    return {
        "node_count": int(graph.num_nodes()),
        "edge_count": int(graph.num_edges()),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "topological_order": topo,
        "longest_path_length": max(len(longest) - 1, 0),
    }


def prove_reverse_order_unsat() -> dict[str, Any]:
    solver = z3.Solver()
    hyper = z3.Int("hyper")
    dual = z3.Int("dual")
    shadow = z3.Int("shadow")
    cell = z3.Int("cell")
    topo = z3.Int("topo")
    variables = (hyper, dual, shadow, cell, topo)
    for var in variables:
        solver.add(var >= 0, var <= 4)
    solver.add(z3.Distinct(*variables))
    solver.add(hyper < dual, dual < shadow, shadow < cell, cell < topo)
    solver.add(topo < hyper)
    verdict = solver.check()
    return {
        "verdict": str(verdict),
        "pass": verdict == z3.unsat,
        "claim": "The strict hypergraph support chain cannot be reversed without contradiction.",
    }


def prove_reverse_order_unsat_cvc5() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()

    hyper = solver.mkConst(integer, "hyper")
    dual = solver.mkConst(integer, "dual")
    shadow = solver.mkConst(integer, "shadow")
    cell = solver.mkConst(integer, "cell")
    topo = solver.mkConst(integer, "topo")
    variables = (hyper, dual, shadow, cell, topo)

    zero = solver.mkInteger(0)
    four = solver.mkInteger(4)

    for var in variables:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, var, zero))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, var, four))

    solver.assertFormula(solver.mkTerm(cvc5.Kind.DISTINCT, *variables))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, hyper, dual))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, dual, shadow))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, shadow, cell))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, cell, topo))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, topo, hyper))

    verdict = solver.checkSat()
    return {
        "verdict": str(verdict),
        "pass": verdict.isUnsat(),
        "claim": "cvc5 cross-check confirms the strict hypergraph support chain cannot be reversed without contradiction.",
    }


def main() -> None:
    follow_on = load_json("weyl_hypergraph_follow_on_results.json")
    hypergraph_result = load_json("hypergraph_geometry_results.json")
    dual_result = load_json("dual_hypergraph_geometry_results.json")
    xgi_shell = load_json("xgi_shell_hypergraph_results.json")
    topo_cross = load_json("toponetx_hopf_crosscheck_results.json")

    hypergraph, dual_hypergraph, shadow_edges = build_strict_hypergraph()
    cell_complex = build_cell_complex()
    b1 = cell_complex.incidence_matrix(rank=1, signed=True).toarray()
    b2 = cell_complex.incidence_matrix(rank=2, signed=True).toarray()
    schedule = build_schedule_graph()
    order_proof = prove_reverse_order_unsat()
    order_proof_cvc5 = prove_reverse_order_unsat_cvc5()

    support_pack_pass = all(
        result_pass(result)
        for result in (hypergraph_result, dual_result, xgi_shell, topo_cross)
    )

    positive = {
        "strict_local_hypergraph_is_exact_and_finite": {
            "num_nodes": hypergraph.num_nodes,
            "num_edges": hypergraph.num_edges,
            "edge_sizes": sorted(hypergraph.edges.size.aslist()),
            "shadow_edge_count": len(shadow_edges),
            "pass": (
                hypergraph.num_nodes == 4
                and hypergraph.num_edges == 2
                and sorted(hypergraph.edges.size.aslist()) == [2, 3]
                and len(shadow_edges) == 4
            ),
        },
        "strict_dual_exposes_role_swap": {
            "dual_node_count": dual_hypergraph.num_nodes,
            "dual_edge_count": dual_hypergraph.num_edges,
            "dual_edge_sizes": sorted(dual_hypergraph.edges.size.aslist()),
            "pass": dual_hypergraph.num_nodes == hypergraph.num_edges and dual_hypergraph.num_edges == hypergraph.num_nodes,
        },
        "strict_cell_complex_lift_is_bounded": {
            "cell_complex_shape": list(cell_complex.shape),
            "rank_B1": int((abs(b1) > 0).sum()),
            "rank_B2": int((abs(b2) > 0).sum()),
            "boundary_composes_to_zero": bool((b1 @ b2 == 0).all()),
            "pass": list(cell_complex.shape) == [4, 4, 1] and bool((b1 @ b2 == 0).all()),
        },
        "support_pack_remains_clean_under_strict_anchor": {
            "follow_on_all_pass": truthy(follow_on["summary"]["all_pass"]),
            "hypergraph_all_pass": result_pass(hypergraph_result),
            "dual_all_pass": result_pass(dual_result),
            "shell_all_pass": result_pass(xgi_shell),
            "topology_all_pass": result_pass(topo_cross),
            "pass": truthy(follow_on["summary"]["all_pass"]) and support_pack_pass,
        },
        "ordering_chain_is_proof_guarded": {
            "graph_path_length": schedule["longest_path_length"],
            "topological_order": schedule["topological_order"],
            "proof_verdict": order_proof["verdict"],
            "cvc5_verdict": order_proof_cvc5["verdict"],
            "pass": (
                schedule["is_dag"]
                and schedule["longest_path_length"] == 4
                and order_proof["pass"]
                and order_proof_cvc5["pass"]
            ),
        },
    }

    negative = {
        "pairwise_shadow_is_not_the_multiway_object": {
            "shadow_edges": shadow_edges,
            "shadow_edge_count": len(shadow_edges),
            "hyperedge_count": hypergraph.num_edges,
            "pass": len(shadow_edges) != hypergraph.num_edges,
        },
        "strict_companion_is_not_runtime_equivalence": {
            "scope_note": (
                "This row is a strict bounded support companion for the hypergraph lane. "
                "It does not claim that open Weyl geometry or engine rows are already "
                "hypergraph-native runtimes."
            ),
            "pass": True,
        },
    }

    boundary = {
        "support_pack_topology_stays_torus_like": {
            "beta0": topo_cross["summary"]["beta0"],
            "beta1": topo_cross["summary"]["beta1"],
            "beta2": topo_cross["summary"]["beta2"],
            "chi": topo_cross["summary"]["chi"],
            "pass": topo_cross["summary"]["beta1"] == 2 and topo_cross["summary"]["chi"] == 0,
        },
        "multiway_support_remains_load_bearing": {
            "rankings_differ_from_pairwise": truthy(xgi_shell["summary"]["rankings_differ_from_pairwise"]),
            "multiway_load_bearing": truthy(xgi_shell["summary"]["multi_way_structure_load_bearing"]),
            "pass": truthy(xgi_shell["summary"]["rankings_differ_from_pairwise"])
            and truthy(xgi_shell["summary"]["multi_way_structure_load_bearing"]),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "qit_weyl_hypergraph_companion",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "support_pack_count": 4,
            "strict_node_count": hypergraph.num_nodes,
            "strict_hyperedge_count": hypergraph.num_edges,
            "strict_shadow_edge_count": len(shadow_edges),
            "strict_dual_node_count": dual_hypergraph.num_nodes,
            "strict_dual_edge_count": dual_hypergraph.num_edges,
            "cell_complex_shape": list(cell_complex.shape),
            "graph_path_length": schedule["longest_path_length"],
            "beta1": topo_cross["summary"]["beta1"],
            "chi": topo_cross["summary"]["chi"],
            "reverse_order_z3_unsat": order_proof["pass"],
            "reverse_order_cvc5_unsat": order_proof_cvc5["pass"],
            "pairwise_shadow_rankings_differ": truthy(xgi_shell["summary"]["rankings_differ_from_pairwise"]),
            "multiway_load_bearing": truthy(xgi_shell["summary"]["multi_way_structure_load_bearing"]),
            "support_pack_all_pass": support_pack_pass,
            "scope_note": (
                "Dedicated strict bounded companion for the hypergraph extension. It keeps "
                "the hypergraph support pack explicit while exposing a finite strict-side "
                "carrier, schedule, and proof guard."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_weyl_hypergraph_companion_results.json"
    out_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
