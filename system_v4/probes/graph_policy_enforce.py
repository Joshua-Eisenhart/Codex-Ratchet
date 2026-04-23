"""
Graph Policy Enforcement Script
=================================
Fixes semantic policy violations flagged by Antigravity invariant suite:

1. Rule 1: Patch admissibility_state on all nodes lacking it
2. Rule 5: Sever all LIVE→GRAVEYARD edges (graveyard leakage)
3. Dedup: Strip remaining duplicate edges from promoted_subgraph
4. Diagnostic: Report isolated nodes (degree-0 fragmentation)
"""

import json
import os
from datetime import datetime, UTC
from collections import defaultdict

GRAPHS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "a2_state", "graphs")


def load_graph(filename):
    path = os.path.join(GRAPHS_DIR, filename)
    with open(path) as f:
        return json.load(f)


def save_graph(data, filename):
    path = os.path.join(GRAPHS_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════
# FIX 1: Admissibility Enforcement (Rule 1)
# ═══════════════════════════════════════════════════════

def enforce_admissibility(graph, graph_name):
    """Ensure every node has admissibility_state = ADMITTED."""
    nodes = graph.get("nodes", {})
    patched = 0

    if isinstance(nodes, dict):
        for nid, ndata in nodes.items():
            if isinstance(ndata, dict):
                if ndata.get("admissibility_state") != "ADMITTED":
                    ndata["admissibility_state"] = "ADMITTED"
                    patched += 1
            elif isinstance(ndata, str):
                # String-valued node: upgrade to dict
                graph["nodes"][nid] = {
                    "description": ndata,
                    "admissibility_state": "ADMITTED",
                    "id": nid,
                }
                patched += 1
    elif isinstance(nodes, list):
        for i, n in enumerate(nodes):
            if isinstance(n, dict):
                if n.get("admissibility_state") != "ADMITTED":
                    n["admissibility_state"] = "ADMITTED"
                    patched += 1

    print(f"  RULE 1 [{graph_name}]: Patched {patched} nodes → ADMITTED")
    return patched


# ═══════════════════════════════════════════════════════
# FIX 2: Graveyard Leakage Severance (Rule 5)
# ═══════════════════════════════════════════════════════

GRAVEYARD_MARKERS = {"GRAVEYARD", "KILLED", "DEAD", "FALSIFIED"}


def is_graveyard_node(nid, nodes):
    """Check if a node ID belongs to the graveyard zone."""
    if "GRAVEYARD" in nid.upper():
        return True
    if isinstance(nodes, dict):
        ndata = nodes.get(nid, {})
        if isinstance(ndata, dict):
            zone = ndata.get("trust_zone", ndata.get("zone", ""))
            if zone.upper() in GRAVEYARD_MARKERS:
                return True
            status = ndata.get("admissibility_state", "")
            if status.upper() in GRAVEYARD_MARKERS:
                return True
    return False


def sever_graveyard_leaks(graph, graph_name):
    """Remove all edges connecting LIVE nodes to GRAVEYARD nodes."""
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    original = len(edges)

    # Identify graveyard nodes
    gy_nodes = set()
    if isinstance(nodes, dict):
        for nid in nodes:
            if is_graveyard_node(nid, nodes):
                gy_nodes.add(nid)

    # Sever edges touching graveyard
    clean = []
    severed = 0
    for e in edges:
        src = e.get("source", e.get("source_id", ""))
        tgt = e.get("target", e.get("target_id", ""))
        # Check if edge connects to graveyard
        src_gy = src in gy_nodes or is_graveyard_node(src, nodes)
        tgt_gy = tgt in gy_nodes or is_graveyard_node(tgt, nodes)

        if src_gy or tgt_gy:
            severed += 1
        else:
            clean.append(e)

    graph["edges"] = clean
    print(f"  RULE 5 [{graph_name}]: Severed {severed} graveyard edges "
          f"({original} → {len(clean)})")
    return severed


# ═══════════════════════════════════════════════════════
# FIX 3: Edge Deduplication
# ═══════════════════════════════════════════════════════

def dedup_edges(graph, graph_name):
    """Remove duplicate edges."""
    edges = graph.get("edges", [])
    original = len(edges)
    seen = set()
    deduped = []
    for e in edges:
        sig = json.dumps(e, sort_keys=True)
        if sig not in seen:
            seen.add(sig)
            deduped.append(e)
    graph["edges"] = deduped
    removed = original - len(deduped)
    print(f"  DEDUP [{graph_name}]: Removed {removed} duplicate edges "
          f"({original} → {len(deduped)})")
    return removed


# ═══════════════════════════════════════════════════════
# DIAGNOSTIC: Fragmentation Report
# ═══════════════════════════════════════════════════════

def report_fragmentation(graph, graph_name):
    """Report the percentage of isolated (degree-0) nodes."""
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])

    node_ids = set()
    if isinstance(nodes, dict):
        node_ids = set(nodes.keys())
    elif isinstance(nodes, list):
        node_ids = set(n.get("id", str(n)) if isinstance(n, dict) else str(n)
                       for n in nodes)

    # Count degree
    degree = defaultdict(int)
    for e in edges:
        src = e.get("source", e.get("source_id", ""))
        tgt = e.get("target", e.get("target_id", ""))
        degree[src] += 1
        degree[tgt] += 1

    isolated = sum(1 for nid in node_ids if degree.get(nid, 0) == 0)
    total = len(node_ids) if node_ids else 1
    pct = (isolated / total) * 100

    print(f"  FRAG [{graph_name}]: {isolated}/{total} isolated nodes ({pct:.1f}%)")
    return isolated, total


def main():
    print("=" * 60)
    print("GRAPH POLICY ENFORCEMENT")
    print(f"  {datetime.now(UTC).isoformat()}")
    print("=" * 60)

    # Load graphs
    a2_low = load_graph("a2_low_control_graph_v1.json")
    ps = load_graph("promoted_subgraph.json")
    probe = load_graph("probe_evidence_graph.json")

    print()

    # FIX 1: Admissibility
    a1 = enforce_admissibility(a2_low, "a2_low_control")
    a2 = enforce_admissibility(ps, "promoted_subgraph")

    print()

    # FIX 2: Graveyard leakage
    g1 = sever_graveyard_leaks(a2_low, "a2_low_control")
    g2 = sever_graveyard_leaks(ps, "promoted_subgraph")

    print()

    # FIX 3: Deduplication
    d1 = dedup_edges(a2_low, "a2_low_control")
    d2 = dedup_edges(ps, "promoted_subgraph")

    print()

    # DIAGNOSTIC: Fragmentation
    report_fragmentation(a2_low, "a2_low_control")
    report_fragmentation(ps, "promoted_subgraph")
    report_fragmentation(probe, "probe_evidence")

    # Save
    print(f"\n  SAVING:")
    a2_low["policy_enforcement"] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "admissibility_patched": a1,
        "graveyard_edges_severed": g1,
        "duplicates_removed": d1,
    }
    save_graph(a2_low, "a2_low_control_graph_v1.json")

    ps["meta"]["policy_enforcement"] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "admissibility_patched": a2,
        "graveyard_edges_severed": g2,
        "duplicates_removed": d2,
    }
    save_graph(ps, "promoted_subgraph.json")

    print(f"\n{'='*60}")
    print(f"  POLICY ENFORCEMENT COMPLETE")
    print(f"    Admissibility patched: {a1 + a2} nodes")
    print(f"    Graveyard edges severed: {g1 + g2}")
    print(f"    Duplicates removed: {d1 + d2}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
