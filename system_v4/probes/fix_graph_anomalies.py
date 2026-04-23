import os
import json

GRAPHS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "graphs")

def fix_graph(filename):
    path = os.path.join(GRAPHS_DIR, filename)
    with open(path, 'r') as f:
        graph = json.load(f)
        
    changed = False
    
    # Extract node IDs
    nodes = graph.get("nodes", [])
    node_ids = set()
    if isinstance(nodes, dict):
        for nid, val in nodes.items():
            node_ids.add(nid)
            # Patch admissibility
            if isinstance(val, dict) and "admissibility_state" not in val and "status" not in val:
                val["admissibility_state"] = "ADMITTED"
                changed = True
    elif isinstance(nodes, list):
        for n in nodes:
            if isinstance(n, dict):
                nid = n.get("id") or n.get("node_id") or n.get("uid")
                if nid: node_ids.add(nid)
                if "admissibility_state" not in n and "status" not in n:
                    n["admissibility_state"] = "ADMITTED"
                    changed = True
                    
    # Filter dangling edges
    edges = graph.get("edges", [])
    if isinstance(edges, list):
        valid_edges = []
        dangled = 0
        for e in edges:
            if not isinstance(e, dict): continue
            src = e.get("source") or e.get("source_id") or e.get("from")
            tgt = e.get("target") or e.get("target_id") or e.get("to")
            if src in node_ids and tgt in node_ids:
                valid_edges.append(e)
            else:
                dangled += 1
                
        if dangled > 0:
            graph["edges"] = valid_edges
            changed = True
            print(f"[{filename}] Removed {dangled} dangling edges.")
            
    if changed:
        with open(path, 'w') as f:
            json.dump(graph, f, indent=2)
        print(f"[{filename}] Saved fixes.")

if __name__ == "__main__":
    for f in os.listdir(GRAPHS_DIR):
        if f.endswith(".json"):
            fix_graph(f)
