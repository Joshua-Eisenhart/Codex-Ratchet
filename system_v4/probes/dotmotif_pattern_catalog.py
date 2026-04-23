#!/usr/bin/env python3
"""
DotMotif Structural Pattern Catalog
====================================
Runs 6 motif patterns across 3 system graphs using dotmotif 0.14.0.

Outputs:
  - Structured JSON summary to stdout
  - Markdown table for audit log consumption

Graphs:
  1. a2_low_control_graph_v1.json   (419 nodes, 858 edges)
  2. promoted_subgraph.json         (296 nodes, 733 edges)
  3. a2_high_intake_graph_v1.json   (8793 nodes — subsampled to 500 nodes)
"""

import json
import os
import sys
import time
import random
from collections import defaultdict
from pathlib import Path

import networkx as nx
from dotmotif import Motif, NetworkXExecutor

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GRAPH_DIR = Path(__file__).resolve().parent.parent / "a2_state" / "graphs"

GRAPH_FILES = {
    "a2_low_control": "a2_low_control_graph_v1.json",
    "promoted_subgraph": "promoted_subgraph.json",
    "a2_high_intake_500": "a2_high_intake_graph_v1.json",
}

HIGH_INTAKE_SUBSAMPLE = 500

# Motif definitions (dotmotif DSL)
MOTIF_DEFINITIONS = {
    "Triangle (A→B→C→A)": """\
A -> B
B -> C
C -> A
""",
    "Star (hub-3: A→B,C,D)": """\
A -> B
A -> C
A -> D
""",
    "Chain-of-3 (A→B→C)": """\
A -> B
B -> C
""",
    "Bidirectional (A↔B)": """\
A -> B
B -> A
""",
    "Fork (A→B, A→C)": """\
A -> B
A -> C
""",
    "Diamond (A→B,C→D)": """\
A -> B
A -> C
B -> D
C -> D
""",
}


# ---------------------------------------------------------------------------
# Graph loading
# ---------------------------------------------------------------------------

def load_graph_from_json(filepath: str) -> nx.DiGraph:
    """Load a JSON graph file into a NetworkX DiGraph."""
    with open(filepath) as f:
        data = json.load(f)

    G = nx.DiGraph()

    # Add nodes
    nodes = data.get("nodes", {})
    if isinstance(nodes, dict):
        for node_id, attrs in nodes.items():
            G.add_node(node_id, **{k: v for k, v in attrs.items() if k != "id"})
    elif isinstance(nodes, list):
        for node in nodes:
            nid = node.get("id", str(node))
            G.add_node(nid, **{k: v for k, v in node.items() if k != "id"})

    # Add edges
    edges = data.get("edges", [])
    if isinstance(edges, list):
        for edge in edges:
            src = edge.get("source_id") or edge.get("source")
            tgt = edge.get("target_id") or edge.get("target")
            if src and tgt:
                attrs = {k: v for k, v in edge.items()
                         if k not in ("source_id", "target_id", "source", "target")}
                G.add_edge(src, tgt, **attrs)

    return G


def subsample_graph(G: nx.DiGraph, max_nodes: int, seed: int = 42) -> nx.DiGraph:
    """Extract a connected subgraph via BFS from the highest-degree node."""
    if G.number_of_nodes() <= max_nodes:
        return G

    # Pick seed: highest degree node
    seed_node = max(G.nodes(), key=lambda n: G.degree(n))

    # BFS expansion
    visited = set()
    queue = [seed_node]
    while queue and len(visited) < max_nodes:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        neighbors = list(G.successors(node)) + list(G.predecessors(node))
        random.seed(seed)
        random.shuffle(neighbors)
        for nb in neighbors:
            if nb not in visited:
                queue.append(nb)

    return G.subgraph(visited).copy()


# ---------------------------------------------------------------------------
# Motif search
# ---------------------------------------------------------------------------

def run_motif_search(G: nx.DiGraph, motif_dsl: str) -> list:
    """Run a single motif pattern against a graph, return list of matches."""
    motif = Motif(motif_dsl)
    executor = NetworkXExecutor(graph=G)
    return executor.find(motif)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze_results(all_results: dict, graph_stats: dict) -> dict:
    """Analyze pattern counts and flag surprises."""
    analysis = {
        "most_common": {},
        "surprises": [],
    }

    for graph_name, motif_results in all_results.items():
        n_nodes = graph_stats[graph_name]["nodes"]
        n_edges = graph_stats[graph_name]["edges"]

        # Find most common pattern for this graph
        sorted_motifs = sorted(motif_results.items(), key=lambda x: x[1], reverse=True)
        if sorted_motifs:
            analysis["most_common"][graph_name] = {
                "pattern": sorted_motifs[0][0],
                "count": sorted_motifs[0][1],
            }

        # Flag surprises
        for motif_name, count in motif_results.items():
            # Unexpected cycles in what might be a DAG-like structure
            if "Triangle" in motif_name and count > 0:
                analysis["surprises"].append({
                    "graph": graph_name,
                    "pattern": motif_name,
                    "count": count,
                    "reason": f"Cyclic triangle found — graph has {count} 3-cycles, "
                              f"suggesting non-DAG dependency structure",
                })

            # Bidirectional edges (mutual dependencies)
            if "Bidirectional" in motif_name and count > 0:
                pct = round(count / max(n_edges, 1) * 100, 2)
                analysis["surprises"].append({
                    "graph": graph_name,
                    "pattern": motif_name,
                    "count": count,
                    "reason": f"{count} mutual dependencies found ({pct}% of edges)",
                })

            # Very high star count relative to nodes (orphan star hubs)
            if "Star" in motif_name and count > n_nodes * 2:
                analysis["surprises"].append({
                    "graph": graph_name,
                    "pattern": motif_name,
                    "count": count,
                    "reason": f"Star count ({count}) >> node count ({n_nodes}) — "
                              f"indicates heavily concentrated hub nodes",
                })

            # Diamond convergence (structural bottlenecks)
            if "Diamond" in motif_name and count > 0:
                analysis["surprises"].append({
                    "graph": graph_name,
                    "pattern": motif_name,
                    "count": count,
                    "reason": f"{count} diamond/converging-path patterns — "
                              f"potential structural bottlenecks",
                })

    return analysis


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_markdown_table(all_results: dict, graph_stats: dict) -> str:
    """Format results as a markdown table."""
    motif_names = list(MOTIF_DEFINITIONS.keys())
    graph_names = list(all_results.keys())

    lines = []
    # Header
    header = "| Pattern | " + " | ".join(graph_names) + " |"
    sep = "|---|" + "|".join(["---:"] * len(graph_names)) + "|"
    lines.append(header)
    lines.append(sep)

    for mname in motif_names:
        row = f"| {mname} | "
        cells = []
        for gname in graph_names:
            count = all_results.get(gname, {}).get(mname, 0)
            cells.append(f"{count:,}")
        row += " | ".join(cells) + " |"
        lines.append(row)

    # Totals row
    row = "| **TOTAL** | "
    cells = []
    for gname in graph_names:
        total = sum(all_results.get(gname, {}).values())
        cells.append(f"**{total:,}**")
    row += " | ".join(cells) + " |"
    lines.append(row)

    return "\n".join(lines)


def format_graph_stats_table(graph_stats: dict) -> str:
    """Format graph size info as markdown."""
    lines = ["| Graph | Nodes | Edges |", "|---|---:|---:|"]
    for name, stats in graph_stats.items():
        lines.append(f"| {name} | {stats['nodes']:,} | {stats['edges']:,} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("DOTMOTIF STRUCTURAL PATTERN CATALOG")
    print("=" * 60)
    print()

    # Load graphs
    graphs = {}
    graph_stats = {}

    for label, filename in GRAPH_FILES.items():
        filepath = GRAPH_DIR / filename
        print(f"Loading {label} from {filepath.name}...")
        G = load_graph_from_json(str(filepath))

        if label == "a2_high_intake_500":
            full_nodes = G.number_of_nodes()
            full_edges = G.number_of_edges()
            print(f"  Full graph: {full_nodes:,} nodes, {full_edges:,} edges")
            G = subsample_graph(G, HIGH_INTAKE_SUBSAMPLE)
            print(f"  Subsampled: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")
        else:
            print(f"  Loaded: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")

        graphs[label] = G
        graph_stats[label] = {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
        }

    print()

    # Run motifs
    all_results = {}
    timing = {}

    for graph_label, G in graphs.items():
        print(f"--- Scanning: {graph_label} ({G.number_of_nodes()} nodes) ---")
        all_results[graph_label] = {}
        timing[graph_label] = {}

        for motif_name, motif_dsl in MOTIF_DEFINITIONS.items():
            t0 = time.time()
            try:
                matches = run_motif_search(G, motif_dsl)
                count = len(matches)
            except Exception as e:
                print(f"  ERROR on {motif_name}: {e}")
                count = -1
            elapsed = time.time() - t0

            all_results[graph_label][motif_name] = count
            timing[graph_label][motif_name] = round(elapsed, 3)
            print(f"  {motif_name}: {count:,} matches ({elapsed:.3f}s)")

        print()

    # Analysis
    analysis = analyze_results(all_results, graph_stats)

    # Print results
    print("=" * 60)
    print("RESULTS TABLE")
    print("=" * 60)
    print()
    print(format_graph_stats_table(graph_stats))
    print()
    print(format_markdown_table(all_results, graph_stats))
    print()

    print("MOST COMMON PATTERNS:")
    for gname, info in analysis["most_common"].items():
        print(f"  {gname}: {info['pattern']} ({info['count']:,} matches)")
    print()

    print("FLAGGED SURPRISES:")
    if analysis["surprises"]:
        for s in analysis["surprises"]:
            print(f"  [{s['graph']}] {s['pattern']}: {s['reason']}")
    else:
        print("  None found.")
    print()

    # Structured JSON output
    output = {
        "catalog_version": "v1",
        "tool": "dotmotif 0.14.0",
        "graph_stats": graph_stats,
        "motif_counts": all_results,
        "timing_seconds": timing,
        "analysis": analysis,
    }

    print("=" * 60)
    print("JSON SUMMARY")
    print("=" * 60)
    print(json.dumps(output, indent=2))

    return output


if __name__ == "__main__":
    main()
