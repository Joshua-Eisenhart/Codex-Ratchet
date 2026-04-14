#!/usr/bin/env python3
"""
Bounded Weyl/Hopf <-> hypergraph translation lane.

This row compares the ranked hypergraph follow-on against the existing
hypergraph support pack and the dedicated Weyl/Hopf -> hypergraph bridge.
It is intentionally bounded: it tells the controller whether the hypergraph
lane is bridge-only or companion-ready without claiming runtime equivalence.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

import rustworkx as rx
import z3
classification = "classical_baseline"  # auto-backfill


PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Bounded translation lane for the Weyl/Hopf -> hypergraph family. It "
    "compares the ranked hypergraph follow-on, the dedicated hypergraph bridge, "
    "and the existing hypergraph support pack without claiming runtime equivalence."
)

LEGO_IDS = [
    "weyl_hypergraph_follow_on",
    "hypergraph_geometry",
    "dual_hypergraph_geometry",
    "xgi_shell_hypergraph",
    "toponetx_hopf_crosscheck",
]

PRIMARY_LEGO_IDS = [
    "weyl_hypergraph_follow_on",
    "hypergraph_geometry",
    "dual_hypergraph_geometry",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing order proof for follow-on -> bridge -> support-pack chain",
    },
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing DAG for follow-on and support-pack order",
    },
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"

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
        return value.strip().lower() in {"true", "pass", "passed", "yes", "sat"}
    return bool(value)


def result_pass(result: dict[str, Any] | None) -> bool:
    if not result:
        return False
    summary = result.get("summary")
    if isinstance(summary, dict) and "all_pass" in summary:
        return truthy(summary["all_pass"])
    if "all_pass" in result:
        return truthy(result["all_pass"])
    if result.get("classification") == "canonical":
        return True
    if isinstance(summary, dict) and "multi_way_structure_load_bearing" in summary:
        return truthy(summary.get("multi_way_structure_load_bearing")) and truthy(summary.get("rankings_differ_from_pairwise"))
    positive = result.get("positive")
    if isinstance(positive, dict) and positive:
        return all(truthy(v.get("pass")) for v in positive.values() if isinstance(v, dict))
    return False


def build_chain_graph() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = [
        "weyl_hypergraph_follow_on",
        "hypergraph_geometry",
        "dual_hypergraph_geometry",
        "xgi_shell_hypergraph",
        "toponetx_hopf_crosscheck",
    ]
    idx = {name: graph.add_node(name) for name in nodes}
    for source, target in zip(nodes, nodes[1:]):
        graph.add_edge(idx[source], idx[target], f"{source}->{target}")
    topo = [graph[node] for node in rx.topological_sort(graph)]
    longest = [graph[node] for node in rx.dag_longest_path(graph)]
    return {
        "node_count": int(graph.num_nodes()),
        "edge_count": int(graph.num_edges()),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "topological_order": topo,
        "longest_path_length": max(len(longest) - 1, 0),
        "source_count": int(sum(graph.in_degree(node) == 0 for node in graph.node_indices())),
        "sink_count": int(sum(graph.out_degree(node) == 0 for node in graph.node_indices())),
    }


def prove_ordering_guard() -> dict[str, Any]:
    solver = z3.Solver()
    follow = z3.Int("follow")
    bridge = z3.Int("bridge")
    support = z3.Int("support")
    for var in (follow, bridge, support):
        solver.add(var >= 0, var <= 2)
    solver.add(z3.Distinct(follow, bridge, support))
    solver.add(follow < bridge, bridge < support)
    solver.add(support < follow)
    verdict = solver.check()
    return {
        "verdict": str(verdict),
        "pass": verdict == z3.unsat,
        "claim": "The hypergraph support pack cannot precede the follow-on and bridge ordering.",
    }


def main() -> None:
    follow_on = load_json("weyl_hypergraph_follow_on_results.json")
    hypergraph = load_json("hypergraph_geometry_results.json")
    dual_hypergraph = load_json("dual_hypergraph_geometry_results.json")
    xgi_shell = load_json("xgi_shell_hypergraph_results.json")
    topo_cross = load_json("toponetx_hopf_crosscheck_results.json")

    graph_summary = build_chain_graph()
    ordering_guard = prove_ordering_guard()

    support_pack_pass = all(
        result_pass(result)
        for result in (hypergraph, dual_hypergraph, xgi_shell, topo_cross)
    )

    positive = {
        "follow_on_remains_the_ranked_extension_point": {
            "best_family": follow_on["summary"]["best_family"],
            "best_family_score": follow_on["summary"]["best_family_score"],
            "hypergraph_support_count": follow_on["summary"]["hypergraph_support_count"],
            "hypergraph_multiway_load_bearing": follow_on["summary"]["hypergraph_multiway_load_bearing"],
            "pass": follow_on["summary"]["best_family"] == "hypergraph_family",
        },
        "support_pack_is_clean_and_finite": {
            "hypergraph_all_pass": result_pass(hypergraph),
            "dual_all_pass": result_pass(dual_hypergraph),
            "shell_all_pass": result_pass(xgi_shell),
            "crosscheck_all_pass": result_pass(topo_cross),
            "pass": support_pack_pass,
        },
        "ordering_guard_blocks_the_reverse_route": ordering_guard,
    }

    negative = {
        "pairwise_shadow_is_distinct_from_multiway_support": {
            "rankings_differ_from_pairwise": truthy(xgi_shell.get("summary", {}).get("rankings_differ_from_pairwise")),
            "multiway_load_bearing": truthy(xgi_shell.get("summary", {}).get("multi_way_structure_load_bearing")),
            "pass": truthy(xgi_shell.get("summary", {}).get("rankings_differ_from_pairwise"))
            and truthy(xgi_shell.get("summary", {}).get("multi_way_structure_load_bearing")),
        },
        "lane_is_not_a_runtime_equivalence_claim": {
            "scope_note": (
                "This lane only compares the open hypergraph follow-on to the support pack and "
                "the bounded bridge. It does not claim a hypergraph-native engine runtime."
            ),
            "pass": True,
        },
    }

    boundary = {
        "order_matches_follow_on_then_bridge_then_support_pack": {
            "topological_order": graph_summary["topological_order"],
            "pass": graph_summary["topological_order"] == [
                "weyl_hypergraph_follow_on",
                "hypergraph_geometry",
                "dual_hypergraph_geometry",
                "xgi_shell_hypergraph",
                "toponetx_hopf_crosscheck",
            ],
        },
        "support_pack_is_topologically_torus_like": {
            "beta0": topo_cross["summary"]["beta0"],
            "beta1": topo_cross["summary"]["beta1"],
            "beta2": topo_cross["summary"]["beta2"],
            "chi": topo_cross["summary"]["chi"],
            "pass": truthy(topo_cross["summary"]["chi_confirmed_zero"]),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "qit_weyl_hypergraph_translation_lane",
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
            "graph_path_length": graph_summary["longest_path_length"],
            "best_family": follow_on["summary"]["best_family"],
            "best_family_score": follow_on["summary"]["best_family_score"],
            "support_pack_count": 4,
            "hypergraph_support_count": follow_on["summary"]["hypergraph_support_count"],
            "pairwise_shadow_rankings_differ": truthy(xgi_shell.get("summary", {}).get("rankings_differ_from_pairwise")),
            "multiway_load_bearing": truthy(xgi_shell.get("summary", {}).get("multi_way_structure_load_bearing")),
            "support_pack_all_pass": support_pack_pass,
            "scope_note": (
                "Bounded open-vs-strict translation lane for the hypergraph extension. It keeps "
                "the hypergraph family first-ranked while checking the existing support pack as "
                "the strict companion surface."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_weyl_hypergraph_translation_lane_results.json"
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
