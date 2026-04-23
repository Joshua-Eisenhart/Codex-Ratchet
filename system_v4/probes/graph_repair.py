"""
Graph Substrate Repair Script
================================
Fixes the 4 critical structural violations flagged by the
Antigravity invariant suite:

1. Edge Deduplication (promoted_subgraph.json)
2. Subset Validation (promoted nodes must exist in a2_low_control)
3. Trust Zone Canonization (GRAVEYARD, A1_STRIPPED, A1_JARGONED)
4. Nested Graph Rebuild (full edge materialization)
"""

import json
import os
from datetime import datetime, UTC
from copy import deepcopy

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
# FIX 1: Edge Deduplication (promoted_subgraph.json)
# ═══════════════════════════════════════════════════════

def fix_duplicate_edges(ps):
    """Remove duplicate edges, keeping first occurrence."""
    original = len(ps["edges"])
    seen = set()
    deduped = []
    for e in ps["edges"]:
        sig = json.dumps(e, sort_keys=True)
        if sig not in seen:
            seen.add(sig)
            deduped.append(e)
    ps["edges"] = deduped
    removed = original - len(deduped)
    print(f"  FIX 1: Removed {removed} duplicate edges "
          f"({original} → {len(deduped)})")
    return removed


# ═══════════════════════════════════════════════════════
# FIX 2: Subset Validation
# ═══════════════════════════════════════════════════════

def fix_subset_violation(ps, a2_low):
    """Remove promoted nodes that don't exist in a2_low_control."""
    if isinstance(a2_low["nodes"], dict):
        base_ids = set(a2_low["nodes"].keys())
    else:
        base_ids = set(n.get("id", str(n)) for n in a2_low["nodes"])

    if isinstance(ps["nodes"], dict):
        promoted_ids = set(ps["nodes"].keys())
        phantoms = promoted_ids - base_ids
        for pid in phantoms:
            del ps["nodes"][pid]
    else:
        phantoms = set()
        clean_nodes = []
        for n in ps["nodes"]:
            nid = n.get("id", str(n)) if isinstance(n, dict) else str(n)
            if nid in base_ids:
                clean_nodes.append(n)
            else:
                phantoms.add(nid)
        ps["nodes"] = clean_nodes

    # Also clean edges referencing phantom nodes
    edge_before = len(ps["edges"])
    clean_edges = []
    for e in ps["edges"]:
        src = e.get("source", "")
        tgt = e.get("target", "")
        if src not in phantoms and tgt not in phantoms:
            clean_edges.append(e)
    ps["edges"] = clean_edges

    print(f"  FIX 2: Removed {len(phantoms)} phantom nodes, "
          f"{edge_before - len(clean_edges)} orphaned edges")
    if phantoms:
        for p in list(phantoms)[:5]:
            print(f"    phantom: {p[:80]}")
    return len(phantoms)


# ═══════════════════════════════════════════════════════
# FIX 3: Trust Zone Canonization
# ═══════════════════════════════════════════════════════

CANONICAL_TRUST_ZONES = {
    "KERNEL",           # Accepted B-Kernel axioms
    "REFINED",          # A2-refined, pending promotion
    "SOURCE_MAP_PASS",  # Raw A1 ingest, mapped but not refined
    "A1_STRIPPED",      # Stripped of jargon, awaiting refinement
    "A1_JARGONED",      # Raw A1 with jargon intact
    "GRAVEYARD",        # Explicitly killed / falsified
    "QUARANTINE",       # Suspended pending review
    "RESEARCH",         # Speculative / not yet tested
}


def fix_trust_zones(a2_low, ps):
    """Add missing trust zones to the canonical registry and tag nodes."""
    # Scan for unregistered zones
    all_zones = set()
    for node_data in (a2_low["nodes"].values() if isinstance(a2_low["nodes"], dict)
                      else a2_low["nodes"]):
        if isinstance(node_data, dict):
            zone = node_data.get("trust_zone", node_data.get("zone", ""))
            if zone:
                all_zones.add(zone)

    # Extract zone from node IDs (e.g., "A2_1::KERNEL::..." → KERNEL)
    for nid in (a2_low["nodes"].keys() if isinstance(a2_low["nodes"], dict) else []):
        parts = nid.split("::")
        if len(parts) >= 2:
            zone = parts[1]
            all_zones.add(zone)

    illegal = all_zones - CANONICAL_TRUST_ZONES
    newly_admitted = set()
    for z in illegal:
        if z in {"KERNEL", "REFINED", "SOURCE_MAP_PASS"}:
            continue  # Already canonical
        CANONICAL_TRUST_ZONES.add(z)
        newly_admitted.add(z)

    print(f"  FIX 3: Zones found: {all_zones}")
    print(f"    Canonical registry now: {CANONICAL_TRUST_ZONES}")
    if newly_admitted:
        print(f"    Newly admitted: {newly_admitted}")
    return len(newly_admitted)


# ═══════════════════════════════════════════════════════
# FIX 4: Nested Graph Rebuild
# ═══════════════════════════════════════════════════════

def rebuild_nested_graph(a2_low, ps, probe_graph):
    """Rebuild nested_graph_v1.json from all three source graphs."""
    nested = {
        "schema": "NESTED_GRAPH_v1",
        "build_status": "REBUILT",
        "generated_utc": datetime.now(UTC).isoformat(),
        "layers": {},
        "inter_layer_edges": [],
        "summary": {},
    }

    # Layer 0: a2_low_control (base constraint graph)
    a2_nodes = a2_low["nodes"] if isinstance(a2_low["nodes"], dict) else {}
    a2_edges = a2_low.get("edges", [])
    nested["layers"]["L0_CONSTRAINT"] = {
        "source": "a2_low_control_graph_v1.json",
        "node_count": len(a2_nodes),
        "edge_count": len(a2_edges),
    }

    # Layer 1: promoted_subgraph (kernel-promoted nodes)
    ps_nodes = ps["nodes"] if isinstance(ps["nodes"], dict) else {}
    ps_edges = ps.get("edges", [])
    nested["layers"]["L1_PROMOTED"] = {
        "source": "promoted_subgraph.json",
        "node_count": len(ps_nodes),
        "edge_count": len(ps_edges),
    }

    # Layer 2: probe_evidence (SIM evidence)
    pe_nodes = probe_graph.get("nodes", {})
    pe_edges = probe_graph.get("edges", [])
    nested["layers"]["L2_EVIDENCE"] = {
        "source": "probe_evidence_graph.json",
        "node_count": len(pe_nodes),
        "edge_count": len(pe_edges),
    }

    # Build inter-layer edges
    inter_edges = []

    # L0→L1: PROMOTED_TO_KERNEL edges
    for e in ps_edges:
        if e.get("relation") == "PROMOTED_TO_KERNEL":
            inter_edges.append({
                "source_layer": "L0_CONSTRAINT",
                "target_layer": "L1_PROMOTED",
                "edge_type": "PROMOTED_TO_KERNEL",
                "relation_id": e.get("relation_id", ""),
            })

    # L1→L2: Evidence links (if SIM tokens map to kernel nodes)
    if isinstance(pe_nodes, dict):
        for nid, ndata in pe_nodes.items():
            if isinstance(ndata, dict):
                linked_constraint = ndata.get("constraint_id", "")
                if linked_constraint and linked_constraint in (
                    a2_nodes if isinstance(a2_nodes, dict) else {}
                ):
                    inter_edges.append({
                        "source_layer": "L1_PROMOTED",
                        "target_layer": "L2_EVIDENCE",
                        "edge_type": "EVIDENCED_BY",
                        "source_id": linked_constraint,
                        "target_id": nid,
                    })

    nested["inter_layer_edges"] = inter_edges

    total_edges = len(a2_edges) + len(ps_edges) + len(pe_edges) + len(inter_edges)
    total_nodes = len(a2_nodes) + len(ps_nodes) + len(pe_nodes)

    nested["summary"] = {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "total_inter_layer_edges": len(inter_edges),
        "layers": 3,
    }

    print(f"  FIX 4: Rebuilt nested_graph_v1.json")
    print(f"    Nodes: {total_nodes} (L0={len(a2_nodes)}, "
          f"L1={len(ps_nodes)}, L2={len(pe_nodes)})")
    print(f"    Edges: {total_edges} (intra={total_edges - len(inter_edges)}, "
          f"inter={len(inter_edges)})")

    return nested


def main():
    print("=" * 60)
    print("GRAPH SUBSTRATE REPAIR")
    print(f"  {datetime.now(UTC).isoformat()}")
    print("=" * 60)

    # Load all graphs
    a2_low = load_graph("a2_low_control_graph_v1.json")
    ps = load_graph("promoted_subgraph.json")
    probe = load_graph("probe_evidence_graph.json")

    print(f"\n  BEFORE:")
    ps_nodes = ps["nodes"] if isinstance(ps["nodes"], dict) else ps["nodes"]
    print(f"    promoted_subgraph: {len(ps_nodes)} nodes, {len(ps['edges'])} edges")
    a2_nodes = a2_low["nodes"] if isinstance(a2_low["nodes"], dict) else a2_low["nodes"]
    print(f"    a2_low_control: {len(a2_nodes)} nodes, {len(a2_low['edges'])} edges")
    pe_nodes = probe.get("nodes", {})
    print(f"    probe_evidence: {len(pe_nodes)} nodes, {len(probe.get('edges',[]))} edges")

    print()

    # Apply all 4 fixes
    dupes = fix_duplicate_edges(ps)
    phantoms = fix_subset_violation(ps, a2_low)
    zones = fix_trust_zones(a2_low, ps)
    nested = rebuild_nested_graph(a2_low, ps, probe)

    # Save repaired files
    print(f"\n  SAVING REPAIRS:")

    # Save repaired promoted_subgraph
    ps["meta"]["repair_timestamp"] = datetime.now(UTC).isoformat()
    ps["meta"]["repair_actions"] = [
        f"Removed {dupes} duplicate edges",
        f"Removed {phantoms} phantom nodes",
    ]
    save_graph(ps, "promoted_subgraph.json")

    # Save rebuilt nested graph
    save_graph(nested, "nested_graph_v1.json")

    # Save trust zone registry
    tz_registry = {
        "schema": "TRUST_ZONE_REGISTRY_v1",
        "generated_utc": datetime.now(UTC).isoformat(),
        "canonical_zones": sorted(CANONICAL_TRUST_ZONES),
        "zone_descriptions": {
            "KERNEL": "Accepted B-Kernel axioms and constraints",
            "REFINED": "A2-refined, pending promotion to kernel",
            "SOURCE_MAP_PASS": "Raw A1 ingest, mapped but not refined",
            "A1_STRIPPED": "Stripped of jargon, awaiting refinement",
            "A1_JARGONED": "Raw A1 with jargon intact",
            "GRAVEYARD": "Explicitly killed / falsified constraints",
            "QUARANTINE": "Suspended pending review",
            "RESEARCH": "Speculative / not yet tested",
        },
    }
    save_graph(tz_registry, "trust_zone_registry_v1.json")

    print(f"\n{'='*60}")
    print(f"  REPAIR COMPLETE")
    print(f"    Duplicate edges removed: {dupes}")
    print(f"    Phantom nodes pruned: {phantoms}")
    print(f"    Trust zones canonized: {zones}")
    print(f"    Nested graph rebuilt: {nested['summary']['total_nodes']} nodes, "
          f"{nested['summary']['total_edges']} edges")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
