import os
import json
import statistics
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH_DIR = os.path.join(BASE_DIR, "a2_state", "graphs")
REPORT_PATH = os.path.join(BASE_DIR, "a2_state", "audit_logs", "GRAPH_HEALTH_DASHBOARD__v1.md")

def analyze_graph(filepath):
    with open(filepath, 'r') as f:
        try:
            graph = json.load(f)
        except json.JSONDecodeError:
            print(f"Error reading JSON from {filepath}")
            return None
            
    raw_nodes = graph.get("nodes", [])
    nodes = []
    node_ids = set()
    node_types = defaultdict(int)
    missing_fields = defaultdict(list)

    if isinstance(raw_nodes, dict):
        for nid, val in raw_nodes.items():
            if isinstance(val, dict):
                # Ensure the node has an 'id' field, using the key if missing
                if "id" not in val:
                    val["id"] = nid
                nodes.append(val)
                node_ids.add(val["id"])
            else:
                # Handle case where value is not a dict (rare but possible)
                nodes.append({"id": nid, "type": "UNKNOWN"})
                node_ids.add(nid)
    elif isinstance(raw_nodes, list):
        nodes = raw_nodes
        for n in nodes:
            if isinstance(n, dict):
                nid = n.get("id") or n.get("node_id") or n.get("uid")
                if nid:
                    node_ids.add(nid)
            
    node_count = len(nodes)
    
    for n in nodes:
        if not isinstance(n, dict):
            continue
        nid = n.get("id") or n.get("node_id") or n.get("uid")
        ntype = n.get("node_type") or n.get("type") or n.get("kind") or "UNKNOWN"
        node_types[ntype] += 1
        
        # Check required fields
        if "description" not in n or not str(n.get("description", "")).strip():
            missing_fields["description"].append(nid)
        # admissibility_state is very common in this corpus
        if "admissibility_state" not in n and "status" not in n:
             missing_fields["admissibility_state"].append(nid)
            
    edges = graph.get("edges", [])
    if isinstance(edges, dict):
        edges = list(edges.values())
        
    edge_count = len(edges)
    edge_relation_types = defaultdict(int)
    self_loops = 0
    duplicate_edges = 0
    dangling_edges = 0
    seen_edges = set()
    
    degrees = defaultdict(int)
    
    for e in edges:
        if not isinstance(e, dict):
            continue
        src = e.get("source") or e.get("source_id") or e.get("from")
        tgt = e.get("target") or e.get("target_id") or e.get("to")
        rel = e.get("relation") or e.get("type") or e.get("edge_type") or "UNKNOWN"
        
        edge_relation_types[rel] += 1
        
        if src is not None: degrees[src] += 1
        if tgt is not None: degrees[tgt] += 1
        
        if src == tgt and src is not None:
            self_loops += 1
            
        edge_tuple = (str(src), str(tgt), str(rel))
        if edge_tuple in seen_edges:
            duplicate_edges += 1
        seen_edges.add(edge_tuple)
        
        if src not in node_ids:
            dangling_edges += 1
        if tgt not in node_ids:
            dangling_edges += 1
            
    density = 0.0
    if node_count > 1:
        density = edge_count / (node_count * (node_count - 1))
        
    deg_list = [degrees[n.get("id") or n.get("node_id") or n.get("uid")] for n in nodes if isinstance(n, dict)]
    if deg_list:
        deg_min = min(deg_list)
        deg_max = max(deg_list)
        deg_mean = statistics.mean(deg_list)
        deg_median = statistics.median(deg_list)
    else:
        deg_min = deg_max = deg_mean = deg_median = 0
        
    isolated_nodes = sum(1 for d in deg_list if d == 0)
    
    adj = defaultdict(list)
    for e in edges:
        if not isinstance(e, dict): continue
        src = e.get("source") or e.get("source_id") or e.get("from")
        tgt = e.get("target") or e.get("target_id") or e.get("to")
        if src in node_ids and tgt in node_ids:
            adj[src].append(tgt)
            adj[tgt].append(src)
            
    visited = set()
    components = []
    
    for nid in node_ids:
        if nid not in visited:
            comp_size = 0
            queue = [nid]
            visited.add(nid)
            while queue:
                curr = queue.pop(0)
                comp_size += 1
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(comp_size)
            
    components_count = len(components)
    largest_component = max(components) if components else 0
    
    anomalies = []
    if duplicate_edges > 0:
        anomalies.append(f"⚠️ {duplicate_edges} duplicate edges found")
    if dangling_edges > 0:
        anomalies.append(f"⚠️ {dangling_edges} dangling edges found")
    if isolated_nodes > node_count * 0.5 and node_count > 0:
        anomalies.append(f"⚠️ High number of isolated nodes: {isolated_nodes}/{node_count} ({isolated_nodes*100/node_count:.1f}%)")
    for field, ids in missing_fields.items():
        if len(ids) > node_count * 0.2 and node_count > 0:
             anomalies.append(f"⚠️ Many nodes missing '{field}': {len(ids)} nodes")
    
    return {
        "filename": os.path.basename(filepath),
        "node_count": node_count,
        "edge_count": edge_count,
        "density": density,
        "components_count": components_count,
        "largest_component": largest_component,
        "degree_dist": {
            "min": deg_min,
            "max": deg_max,
            "mean": deg_mean,
            "median": deg_median
        },
        "isolated_nodes": isolated_nodes,
        "self_loops": self_loops,
        "duplicate_edges": duplicate_edges,
        "dangling_edges": dangling_edges,
        "node_types": dict(node_types),
        "edge_relation_types": dict(edge_relation_types),
        "missing_fields": {k: len(v) for k, v in missing_fields.items()},
        "anomalies": anomalies
    }



def main():
    if not os.path.exists(GRAPH_DIR):
        print(f"Error: {GRAPH_DIR} not found.")
        return
        
    results = []
    for f in sorted(os.listdir(GRAPH_DIR)):
        if f.endswith('.json'):
            path = os.path.join(GRAPH_DIR, f)
            print(f"Processing {f}...")
            res = analyze_graph(path)
            if res:
                results.append(res)
                
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    
    with open(REPORT_PATH, "w") as f:
        f.write("# Graph Health Dashboard v1\n\n")
        f.write("A comprehensive health and topology profile for all A2 graphs in the corpus.\n\n")
        
        for r in results:
            f.write(f"## {r['filename']}\n")
            f.write(f"- **Nodes**: {r['node_count']}\n")
            f.write(f"- **Edges**: {r['edge_count']}\n")
            f.write(f"- **Density**: {r['density']:.6f}\n")
            f.write(f"- **Connected Components**: {r['components_count']} (Largest: {r['largest_component']})\n")
            f.write(f"- **Degree Distribution**: Min={r['degree_dist']['min']}, Max={r['degree_dist']['max']}, Mean={r['degree_dist']['mean']:.2f}, Median={r['degree_dist']['median']:.2f}\n")
            f.write(f"- **Isolated Nodes (degree 0)**: {r['isolated_nodes']}\n")
            f.write(f"- **Self-loops**: {r['self_loops']}\n")
            f.write(f"- **Duplicate Edges**: {r['duplicate_edges']}\n")
            f.write(f"- **Dangling Edges**: {r['dangling_edges']}\n")
            
            f.write("\n### Node Types Distribution\n")
            if r['node_types']:
                for t, c in sorted(r['node_types'].items(), key=lambda x: -x[1]):
                    f.write(f"- `{t}`: {c}\n")
            else:
                f.write("None\n")
                
            f.write("\n### Edge Relation Types Distribution\n")
            if r['edge_relation_types']:
                for t, c in sorted(r['edge_relation_types'].items(), key=lambda x: -x[1]):
                    f.write(f"- `{t}`: {c}\n")
            else:
                f.write("None\n")
                
            f.write("\n### Missing Required Fields\n")
            if any(r['missing_fields'].values()):
                for field, count in r['missing_fields'].items():
                    if count > 0:
                        f.write(f"- `{field}`: {count} nodes missing\n")
            else:
                f.write("None\n")
                
            f.write("\n### Health Anomalies\n")
            if r['anomalies']:
                for a in r['anomalies']:
                    f.write(f"- {a}\n")
            else:
                 f.write("- ✅ No significant anomalies detected.\n")
            f.write("\n---\n\n")
            
    print(f"Report written to {REPORT_PATH}")

if __name__ == "__main__":
    main()
