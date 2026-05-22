#!/usr/bin/env python3
"""Formal scout for NetworkX ordered graph readout review."""

from __future__ import annotations

import hashlib
import json
import pathlib

import networkx as nx


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "sim_networkx_ordered_graph_readout_review_unknown_micro_probe_results.json"

NAME = "sim_networkx_ordered_graph_readout_review_unknown_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: observed NetworkX ordered graph readout sensitivity "
    "on one finite carrier and one swapped-control negative. The review status "
    "remains unknown and not promoted; this is not bridge, axis, engine, topology theorem, "
    "or target-system evidence."
)

TOOL_MANIFEST = {
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing DiGraph construction and topological-generation readout",
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
    "networkx": "load_bearing",
    "python": "supportive",
    "json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
}


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def graph_observable(branch_order: list[str]) -> dict[str, object]:
    graph = nx.DiGraph()
    graph.add_node("root")
    for branch in branch_order:
        graph.add_node(branch)
    graph.add_node("sink")
    for branch in branch_order:
        graph.add_edge("root", branch)
        graph.add_edge(branch, "sink")
    generations = [list(generation) for generation in nx.topological_generations(graph)]
    topological_readout = list(nx.topological_sort(graph))
    branch_generation = generations[1] if len(generations) > 1 else []
    weighted_readout = sum((idx + 1) * (len(label) + ord(label[0])) for idx, label in enumerate(topological_readout))
    return {
        "branch_order": list(branch_order),
        "nodes": list(graph.nodes),
        "edges": [[str(src), str(dst)] for src, dst in graph.edges],
        "is_dag": bool(nx.is_directed_acyclic_graph(graph)),
        "topological_generations": generations,
        "topological_readout": topological_readout,
        "branch_generation": branch_generation,
        "weighted_readout": weighted_readout,
        "review_status": "unknown_not_promoted",
    }


def main() -> None:
    baseline = graph_observable(["left_gate", "right_gate"])
    swapped = graph_observable(["right_gate", "left_gate"])
    changed_observable = baseline["topological_readout"] != swapped["topological_readout"]
    same_edge_support = sorted(baseline["edges"]) == sorted(swapped["edges"])
    checks = {
        "classification_is_formal_scout": CLASSIFICATION == "formal_scout",
        "execution_kind_is_nonclassical": SIM_EXECUTION_KIND == "nonclassical",
        "promotion_disabled": PROMOTION_ALLOWED is False,
        "finite_carrier_ran": len(baseline["nodes"]) == 4 and len(baseline["edges"]) == 4,
        "same_unordered_edge_support": same_edge_support,
        "swapped_control_changed_observable": changed_observable,
        "review_status_remains_unknown": baseline["review_status"] == "unknown_not_promoted",
    }
    positive = {
        "networkx_ordered_readout_runs": {
            "pass": checks["finite_carrier_ran"],
            "node_count": len(baseline["nodes"]),
            "edge_count": len(baseline["edges"]),
        },
        "branch_order_swap_changes_topological_readout": {
            "pass": checks["swapped_control_changed_observable"],
            "observable": "topological_readout",
        },
    }
    graveyard_companions = {
        "unordered_edge_support_control_preserved": {
            "pass": checks["same_unordered_edge_support"],
            "reason": "the negative control changes order while preserving unordered edge support",
        },
        "review_status_not_promoted": {
            "pass": checks["review_status_remains_unknown"],
            "reason": "this row remains a review-unknown scout and not an admitted tool result",
        },
    }
    boundary = {
        "finite_fixture_only": {
            "pass": checks["finite_carrier_ran"],
            "claim": "bounded to one four-node ordered branch DAG",
        },
        "not_graph_theorem_or_engine_claim": {
            "pass": PROMOTION_ALLOWED is False,
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
        "fixture": "finite four-node ordered branch DAG",
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
            "NetworkX ordered-readout review micro-probe, not a canonical sim or promoted lego",
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
