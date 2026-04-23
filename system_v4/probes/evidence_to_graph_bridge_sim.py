#!/usr/bin/env python3
"""
Evidence-to-Graph Bridge SIM
================================
Transforms the unified evidence report into a typed knowledge graph.

Node types: Attractor, AxisOp, EvidenceToken, SpecClaim, Counterexample
Edge types: supports, refutes, derived_from, generated_by

Output: a2_state/graphs/evidence_graph.json
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, UTC
from hashlib import sha256

PROBES_DIR = Path(__file__).parent
RESULTS_DIR = PROBES_DIR / "a2_state" / "sim_results"
GRAPHS_DIR = PROBES_DIR.parent / "a2_state" / "graphs"


def hash_node(payload):
    """Deterministic node ID from payload."""
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return sha256(canonical.encode()).hexdigest()[:16]


def build_evidence_graph():
    """Read evidence report and all sim results, build a typed graph."""
    print("=" * 72)
    print("EVIDENCE-TO-GRAPH BRIDGE")
    print("=" * 72)

    nodes = []
    edges = []

    # Load autoresearch evaluation report
    eval_path = RESULTS_DIR / "autoresearch_evaluation_report.json"
    if eval_path.exists():
        with open(str(eval_path)) as f:
            eval_data = json.load(f)

        # Create a system-level node
        sys_node = {
            "id": "SYS_AGGREGATE",
            "type": "SystemState",
            "aggregate_score": eval_data.get("aggregate_score", 0),
            "total_problems": eval_data.get("total_problems", 0),
            "timestamp": eval_data.get("timestamp", ""),
        }
        nodes.append(sys_node)

        # Create nodes for each problem
        for result in eval_data.get("results", []):
            problem_id = hash_node({"name": result["name"]})
            prob_node = {
                "id": problem_id,
                "type": "SpecClaim",
                "name": result["name"],
                "description": result.get("description", ""),
                "score": result.get("score", 0),
                "status": result.get("status", "UNKNOWN"),
                "sim_file": result.get("sim_file", ""),
            }
            nodes.append(prob_node)

            # Edge from problem to system
            edge_type = "supports" if result.get("score", 0) >= 0.8 else "refutes"
            edges.append({
                "source": problem_id,
                "target": "SYS_AGGREGATE",
                "type": edge_type,
                "weight": result.get("score", 0),
            })

    # Load compositional results
    comp_path = RESULTS_DIR / "axis_compositional_structure_results.json"
    if comp_path.exists():
        with open(str(comp_path)) as f:
            comp_data = json.load(f)

        for entry in comp_data.get("top_ranked", comp_data.get("results", []))[:20]:
            axes = entry.get("axes", entry.get("combo", []))
            sig = entry.get("significance", entry.get("sig", 0))
            comp_id = hash_node({"axes": axes, "type": "composition"})
            comp_node = {
                "id": comp_id,
                "type": "AxisComposition",
                "axes": axes,
                "significance": sig,
                "closure": entry.get("closure_residual", entry.get("closure", 0)),
                "clusters": entry.get("clusters", 0),
            }
            nodes.append(comp_node)

    # Load Lie closure results
    lie_path = RESULTS_DIR / "axis_lie_closure_results.json"
    if lie_path.exists():
        with open(str(lie_path)) as f:
            lie_data = json.load(f)

        for result in lie_data.get("results", []):
            lie_id = hash_node({"d": result["d"], "type": "lie_closure"})
            lie_node = {
                "id": lie_id,
                "type": "LieClosure",
                "dimension": result["d"],
                "base_rank": result.get("base_rank", 0),
                "rank_after_L1": result.get("rank_after_L1", 0),
                "rank_after_L2": result.get("rank_after_L2", 0),
                "expansion": result.get("expansion_L1", 0) + result.get("expansion_L2", 0),
            }
            nodes.append(lie_node)
            edges.append({
                "source": lie_id,
                "target": "SYS_AGGREGATE",
                "type": "supports",
                "weight": 1.0 if lie_node["expansion"] > 0 else 0.0,
            })

    # Load deep composition results
    deep_path = RESULTS_DIR / "deep_axis_composition_results.json"
    if deep_path.exists():
        with open(str(deep_path)) as f:
            deep_data = json.load(f)

        results = deep_data.get("results", {})
        # Non-commutativity ranking → edges between axis pairs
        for nc in results.get("noncommutativity_ranking", []):
            pair = nc.get("pair", [])
            if len(pair) == 2:
                nc_id = hash_node({"pair": pair, "type": "noncomm"})
                nodes.append({
                    "id": nc_id,
                    "type": "NonCommutativity",
                    "pair": pair,
                    "score": nc.get("noncommutativity", 0),
                })

    # Build final graph
    graph = {
        "timestamp": datetime.now(UTC).isoformat(),
        "schema_version": "1.0",
        "node_types": ["SystemState", "SpecClaim", "AxisComposition",
                       "LieClosure", "NonCommutativity", "EvidenceToken"],
        "edge_types": ["supports", "refutes", "derived_from", "generated_by"],
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "n_nodes": len(nodes),
            "n_edges": len(edges),
            "n_supporting": sum(1 for e in edges if e["type"] == "supports"),
            "n_refuting": sum(1 for e in edges if e["type"] == "refutes"),
        },
    }

    os.makedirs(str(GRAPHS_DIR), exist_ok=True)
    outpath = GRAPHS_DIR / "evidence_graph.json"
    with open(str(outpath), "w") as f:
        json.dump(graph, f, indent=2)

    print(f"  Nodes: {len(nodes)}")
    print(f"  Edges: {len(edges)}")
    print(f"  Supporting: {graph['stats']['n_supporting']}")
    print(f"  Refuting: {graph['stats']['n_refuting']}")
    print(f"  Graph saved: {outpath}")

    return graph


if __name__ == "__main__":
    build_evidence_graph()
