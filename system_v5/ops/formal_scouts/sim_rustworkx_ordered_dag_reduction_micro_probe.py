#!/usr/bin/env python3
"""Formal scout for rustworkx ordered DAG reduction."""

from __future__ import annotations

import hashlib
import json
import pathlib

import rustworkx as rx


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "sim_rustworkx_ordered_dag_reduction_micro_probe_results.json"

NAME = "sim_rustworkx_ordered_dag_reduction_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: observed rustworkx ordered DAG reduction on one finite "
    "carrier and one swapped-control negative. This is local tool evidence, "
    "not promoted bridge, axis, engine, topology theorem, or target-system evidence."
)

TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PyDiGraph construction, topological sort, reachability, and transitive reduction",
    },
    "python": {
        "tried": True,
        "used": True,
        "reason": "supportive finite fixture control flow and pass/fail checks",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result receipt serialization",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical result path construction",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive stable observable digest",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "rustworkx": "load_bearing",
    "python": "supportive",
    "json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
}


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_graph(branch_order: list[str]) -> rx.PyDiGraph:
    graph = rx.PyDiGraph()
    node_ids = {"root": graph.add_node("root")}
    for label in branch_order:
        node_ids[label] = graph.add_node(label)
    node_ids["sink"] = graph.add_node("sink")
    for label in branch_order:
        graph.add_edge(node_ids["root"], node_ids[label], f"root->{label}")
        graph.add_edge(node_ids[label], node_ids["sink"], f"{label}->sink")
    graph.add_edge(node_ids["root"], node_ids["sink"], "transitive_shortcut")
    return graph


def reduction_observable(branch_order: list[str]) -> dict[str, object]:
    graph = build_graph(branch_order)
    reduction, _node_map = rx.transitive_reduction(graph)
    topo_indices = [int(idx) for idx in rx.topological_sort(graph)]
    topo_labels = [str(graph[idx]) for idx in topo_indices]
    reduction_edges = sorted((str(reduction[src]), str(reduction[dst])) for src, dst in reduction.edge_list())
    return {
        "branch_order": list(branch_order),
        "topological_labels": topo_labels,
        "reduction_edges": reduction_edges,
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "reduction_edge_count": reduction.num_edges(),
        "root_reaches_sink": bool(rx.digraph_has_path(graph, 0, graph.num_nodes() - 1)),
        "sink_reaches_root": bool(rx.digraph_has_path(graph, graph.num_nodes() - 1, 0)),
    }


def main() -> None:
    baseline = reduction_observable(["alpha_gate", "beta_gate"])
    swapped = reduction_observable(["beta_gate", "alpha_gate"])
    changed_observable = baseline["topological_labels"] != swapped["topological_labels"]
    shortcut_removed = (
        ("root", "sink") not in baseline["reduction_edges"]
        and ("root", "sink") not in swapped["reduction_edges"]
    )
    checks = {
        "classification_is_formal_scout": CLASSIFICATION == "formal_scout",
        "execution_kind_is_nonclassical": SIM_EXECUTION_KIND == "nonclassical",
        "promotion_disabled": PROMOTION_ALLOWED is False,
        "finite_carrier_ran": baseline["node_count"] == 4 and baseline["edge_count"] == 5,
        "rustworkx_reduction_removed_transitive_shortcut": shortcut_removed,
        "swapped_control_changed_observable": changed_observable,
        "reverse_reachability_killed": baseline["sink_reaches_root"] is False,
    }
    positive = {
        "rustworkx_transitive_reduction_runs": {
            "pass": checks["rustworkx_reduction_removed_transitive_shortcut"],
            "reduction_edge_count": baseline["reduction_edge_count"],
        },
        "branch_order_swap_changes_topological_labels": {
            "pass": checks["swapped_control_changed_observable"],
            "observable": "topological_labels",
        },
    }
    graveyard_companions = {
        "reverse_reachability_control_killed": {
            "pass": checks["reverse_reachability_killed"],
            "reason": "the fixture is a one-way DAG, not a cyclic reachability artifact",
        },
        "promotion_remains_disabled": {
            "pass": PROMOTION_ALLOWED is False,
            "reason": "tool-function evidence stays scout-only",
        },
    }
    boundary = {
        "finite_fixture_only": {
            "pass": checks["finite_carrier_ran"],
            "claim": "bounded to one four-node ordered DAG with a transitive shortcut",
        },
        "not_graph_theorem_or_engine_claim": {
            "pass": True,
            "claim": "does not promote a graph theorem, bridge, axis, engine, or target-system result",
        },
    }
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
    }
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "fixture": "finite four-node ordered DAG with a transitive shortcut",
        "baseline": baseline,
        "swapped_control_negative": swapped,
        "changed_observable_required": True,
        "changed_observable": changed_observable,
        "observable_digest": stable_hash({"baseline": baseline, "swapped": swapped}),
        "checks": checks,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "v5 formal scout receipt only",
            "rustworkx ordered-DAG reduction micro-probe, not a canonical sim or promoted lego",
            "nonclassical execution kind with promotion explicitly blocked",
        ],
        "pass": all(checks.values()),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT_PATH), "pass": result["pass"], "changed": changed_observable}, sort_keys=True))


if __name__ == "__main__":
    main()
