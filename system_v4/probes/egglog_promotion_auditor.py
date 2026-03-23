import json
import os
from pathlib import Path
from collections import defaultdict
from egglog import *

class NodeId(Expr):
    def __init__(self, id: StringLike) -> None: ...

class Graph(Expr):
    @classmethod
    def LOW_CONTROL(cls) -> 'Graph': ...
    @classmethod
    def PROMOTED(cls) -> 'Graph': ...

# Relations
node_in = relation("node_in", NodeId, Graph)
edge_in = relation("edge_in", NodeId, NodeId, Graph)
authority = relation("authority", NodeId, String)
degree = relation("degree", NodeId, Graph, i64)

# Targets
qualifies_kernel = relation("qualifies_kernel", NodeId)
confirmed = relation("confirmed", NodeId)
connected = relation("connected", NodeId, NodeId)
bridge_eligible = relation("bridge_eligible", NodeId)

def load_graph(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_auditor():
    base_dir = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4")
    low_ctrl_path = base_dir / "a2_state/graphs/a2_low_control_graph_v1.json"
    promoted_path = base_dir / "a2_state/graphs/promoted_subgraph.json"
    
    print(f"Loading {low_ctrl_path.name}...")
    low_ctrl = load_graph(low_ctrl_path)
    print(f"Loading {promoted_path.name}...")
    promoted = load_graph(promoted_path)

    egraph = EGraph()
    
    # 1. Rules
    r1 = rule(
        degree(var('n', NodeId), Graph.LOW_CONTROL(), var('d', i64)),
        var('d', i64) >= i64(3)
    ).then(
        qualifies_kernel(var('n', NodeId))
    )

    r2 = rule(
        node_in(var('n', NodeId), Graph.LOW_CONTROL()),
        node_in(var('n', NodeId), Graph.PROMOTED())
    ).then(
        confirmed(var('n', NodeId))
    )

    r3a_1 = rule(edge_in(var('a', NodeId), var('b', NodeId), var('g', Graph))).then(connected(var('a', NodeId), var('b', NodeId)))
    r3a_2 = rule(edge_in(var('a', NodeId), var('b', NodeId), var('g', Graph))).then(connected(var('b', NodeId), var('a', NodeId)))

    r3b = rule(
        authority(var('n', NodeId), String("CROSS_VALIDATED")),
        connected(var('n', NodeId), var('other', NodeId))
    ).then(
        bridge_eligible(var('n', NodeId))
    )

    egraph.register(r1, r2, r3a_1, r3a_2, r3b)

    # 2. Extract facts from JSON and inject
    # Low control nodes and edges
    lc_nodes = low_ctrl.get("nodes", {})
    # Wait, looking at a2_low_control_graph_v1.json, there isn't a "nodes" dict, just an "edges" array.
    # Where are nodes defined? In low_control, edges contain source_id and target_id.
    # Let's extract nodes from edges.
    lc_node_degrees = defaultdict(int)
    lc_node_set = set()
    lc_authorities = {}
    
    for edge in low_ctrl.get("edges", []):
        src = edge["source_id"]
        tgt = edge["target_id"]
        lc_node_set.add(src)
        lc_node_set.add(tgt)
        lc_node_degrees[src] += 1
        lc_node_degrees[tgt] += 1
        
        egraph.register(edge_in(NodeId(src), NodeId(tgt), Graph.LOW_CONTROL()))
        # Check if authority is in attributes?
        # Typically the attributes might have trust_zone or we must infer authority from other graphs.
        # Actually, let's look at the source nodes from promoted_obj. "authority" was in node properties.
        # If low_control doesn't have it explicitly, we'll extract it if "authority" is inside an edge attribute for testing.
        
    for n in lc_node_set:
        egraph.register(node_in(NodeId(n), Graph.LOW_CONTROL()))
        egraph.register(degree(NodeId(n), Graph.LOW_CONTROL(), i64(lc_node_degrees[n])))
        
    # In promoted_subgraph.json, there are nodes with "properties": {"authority": "..."}
    promoted_nodes = promoted.get("nodes", {})
    for n_id, n_data in promoted_nodes.items():
        egraph.register(node_in(NodeId(n_id), Graph.PROMOTED()))
        
        auth = n_data.get("properties", {}).get("authority")
        if auth:
            egraph.register(authority(NodeId(n_id), String(auth)))

    # Edges in promoted
    for edge in promoted.get("edges", []):
        egraph.register(edge_in(NodeId(edge["source_id"]), NodeId(edge["target_id"]), Graph.PROMOTED()))
        
    print("Running saturation...")
    report = egraph.run(10)
    print(report)

    # Query extraction
    print("Querying results...")
    # egglog v13 query python api pattern:
    # Instead of direct query return, we extract using extract() or by check() in a loop?
    # Another way is egraph.query(qualifies_kernel(var('n', NodeId))) ?
    # Let's trace back from the nodes we know. We can test `egraph.check(qualifies_kernel(NodeId(x)))` for each node since we know the domains.
    
    qualifies_set = set()
    confirmed_set = set()
    bridge_eligible_set = set()
    
    # Testing over union of all nodes
    all_nodes = lc_node_set.union(set(promoted_nodes.keys()))
    for x in all_nodes:
        # egglog.check() throws an EggSmolError if the relation isn't proven.
        try:
            egraph.check(qualifies_kernel(NodeId(x)))
            qualifies_set.add(x)
        except Exception:
            pass
            
        try:
            egraph.check(confirmed(NodeId(x)))
            confirmed_set.add(x)
        except Exception:
            pass
            
        try:
            egraph.check(bridge_eligible(NodeId(x)))
            bridge_eligible_set.add(x)
        except Exception:
            pass

    print(f"Qualified for Kernel: {len(qualifies_set)}")
    print(f"Confirmed Nodes: {len(confirmed_set)}")
    print(f"Bridge Eligible Nodes: {len(bridge_eligible_set)}")
    
    # Write Audit Log
    out_path = base_dir / "a2_state/audit_logs/EGGLOG_PROMOTION_AUDIT__v1.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# EGGLOG PROMOTION AUDIT — v1\n\n")
        f.write(f"> **Date**: {datetime.datetime.now().isoformat()}\n")
        f.write("> **Status**: GENERATED\n\n")
        f.write("## Overview\n")
        f.write("Evaluation of promotion rules across `a2_low_control_graph_v1.json` and `promoted_subgraph.json` using `egglog` equality saturation.\n\n")
        f.write("## Saturation Report\n")
        f.write("```\n")
        f.write(str(report))
        f.write("\n```\n\n")
        
        f.write(f"## Discovered Facts\n")
        f.write(f"- **Total Qualified for Kernel (degree >= 3 in LOW_CONTROL)**: {len(qualifies_set)}\n")
        f.write(f"- **Total Confirmed (in both LOW_CONTROL and PROMOTED)**: {len(confirmed_set)}\n")
        f.write(f"- **Total Bridge Eligible (authority CROSS_VALIDATED & connected)**: {len(bridge_eligible_set)}\n\n")
        
        f.write("### Qualified for Kernel (Sample)\n")
        for x in sorted(list(qualifies_set))[:20]:
            f.write(f"- `{x}`\n")
        if len(qualifies_set) > 20:
            f.write(f"- ... (and {len(qualifies_set)-20} more)\n")
        f.write("\n")
            
        f.write("### Confirmed Nodes (Sample)\n")
        for x in sorted(list(confirmed_set))[:20]:
            f.write(f"- `{x}`\n")
        if len(confirmed_set) > 20:
            f.write(f"- ... (and {len(confirmed_set)-20} more)\n")
        f.write("\n")
            
        f.write("### Bridge Eligible Nodes (Sample)\n")
        for x in sorted(list(bridge_eligible_set))[:20]:
            f.write(f"- `{x}`\n")
        if len(bridge_eligible_set) > 20:
            f.write(f"- ... (and {len(bridge_eligible_set)-20} more)\n")
        f.write("\n")
        
    print(f"Audit log written to: {out_path}")

if __name__ == "__main__":
    import datetime
    run_auditor()
