import json
import os
from pathlib import Path
import igraph as ig
import leidenalg
from collections import Counter, defaultdict

# Paths to the 5 layer graphs
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GRAPH_DIR = str(_REPO_ROOT / "system_v4" / "a2_state" / "graphs") + os.sep
LAYERS = {
    "HIGH_INTAKE": "a2_high_intake_graph_v1.json",
    "MID_REFINEMENT": "a2_mid_refinement_graph_v1.json",
    "LOW_CONTROL": "a2_low_control_graph_v1.json",
    "A1_JARGONED": "a1_jargoned_graph_v1.json",
    "PROMOTED": "promoted_subgraph.json"
}

def load_graph_data():
    all_nodes = {} # id -> set of layers
    all_edges = set() # (source, target)
    
    for layer_name, filename in LAYERS.items():
        path = os.path.join(GRAPH_DIR, filename)
        if not os.path.exists(path):
            print(f"Warning: {path} not found.")
            continue
            
        with open(path, 'r') as f:
            data = json.load(f)
            
        nodes = data.get("nodes", {})
        edges = data.get("edges", [])
        
        # nodes can be a dict (id -> attrs) or a list of dicts
        if isinstance(nodes, dict):
            node_ids_in_layer = list(nodes.keys())
        else:
            node_ids_in_layer = [n.get("id") or n for n in nodes]
        
        for node_id in node_ids_in_layer:
            if node_id:
                if node_id not in all_nodes:
                    all_nodes[node_id] = set()
                all_nodes[node_id].add(layer_name)
                
        for e in edges:
            src = e.get("source_id")
            tgt = e.get("target_id")
            if src and tgt:
                all_edges.add((src, tgt))
                # Ensure nodes are registered even if not in 'nodes' list
                if src not in all_nodes: all_nodes[src] = set()
                if tgt not in all_nodes: all_nodes[tgt] = set()
                # Actually, some edges might be cross-layer. 
                # For simplicity, we only mark layer membership if the node is in the 'nodes' list of that layer's file.
                
    return all_nodes, list(all_edges)

def analyze():
    print("Loading graph data...")
    node_layer_map, edges = load_graph_data()
    
    node_ids = sorted(list(node_layer_map.keys()))
    id_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    
    print(f"Building igraph with {len(node_ids)} nodes and {len(edges)} edges...")
    g = ig.Graph(directed=True)
    g.add_vertices(len(node_ids))
    
    edge_indices = []
    for src, tgt in edges:
        if src in id_to_idx and tgt in id_to_idx:
            edge_indices.append((id_to_idx[src], id_to_idx[tgt]))
    
    g.add_edges(edge_indices)
    
    print("Running leidenalg community detection...")
    # Use modularity or RB configuration
    partition = leidenalg.find_partition(g, leidenalg.ModularityVertexPartition)
    
    community_ids = partition.membership # index aligned with node_ids
    
    # Analysis
    node_to_community = {node_ids[i]: community_ids[i] for i in range(len(node_ids))}
    
    layer_stats = {}
    for layer_name in LAYERS.keys():
        layer_nodes = [nid for nid, layers in node_layer_map.items() if layer_name in layers]
        if not layer_nodes:
            continue
            
        communities_in_layer = [node_to_community[nid] for nid in layer_nodes]
        counts = Counter(communities_in_layer)
        most_common_comm, dominant_count = counts.most_common(1)[0]
        purity = (dominant_count / len(layer_nodes)) * 100
        
        layer_stats[layer_name] = {
            "total_nodes": len(layer_nodes),
            "num_communities": len(counts),
            "dominant_community": most_common_comm,
            "purity": purity,
            "community_dist": counts
        }
    
    # Bridge communities (communities spanning multiple layers)
    community_to_layers = defaultdict(set)
    for nid, layers in node_layer_map.items():
        comm_id = node_to_community[nid]
        for layer_name in layers:
            community_to_layers[comm_id].add(layer_name)
            
    bridge_communities = {cid: list(layers) for cid, layers in community_to_layers.items() if len(layers) > 1}
    
    # Bridge nodes (nodes appearing in multiple layers)
    multi_layer_nodes = {nid: list(layers) for nid, layers in node_layer_map.items() if len(layers) > 1}
    
    # Output to Markdown
    output_path = str(_REPO_ROOT / "system_v4" / "a2_state" / "audit_logs" / "COMMUNITY_LAYER_ALIGNMENT_AUDIT__v1.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("# Community vs Layer Alignment Audit v1\n\n")
        f.write(f"**Total Nodes (Union):** {len(node_ids)}\n")
        f.write(f"**Total Edges (Union):** {len(edges)}\n")
        f.write(f"**Total Communities Found:** {len(set(community_ids))}\n\n")
        
        f.write("## 1. Manual Layer Alignment\n\n")
        f.write("| Layer | Total Nodes | Communities | Dominant Community | Purity % | Internally Diverse? |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        
        for layer, stats in layer_stats.items():
            diverse = "Yes" if stats["num_communities"] > (stats["total_nodes"] * 0.1) else "No"
            f.write(f"| {layer} | {stats['total_nodes']} | {stats['num_communities']} | {stats['dominant_community']} | {stats['purity']:.2f}% | {diverse} |\n")
            
        f.write("\n## 2. Bridge Communities (Spanning Multiple Layers)\n\n")
        f.write(f"Found **{len(bridge_communities)}** bridge communities.\n\n")
        f.write("| Community ID | Layers Spanned |\n")
        f.write("| :--- | :--- |\n")
        # List top 20 bridges by number of layers spanned
        sorted_bridges = sorted(bridge_communities.items(), key=lambda x: len(x[1]), reverse=True)
        for cid, layers in sorted_bridges[:20]:
            f.write(f"| {cid} | {', '.join(layers)} |\n")
            
        f.write("\n## 3. Bridge Nodes (Cross-Layer Anchors)\n\n")
        f.write(f"Found **{len(multi_layer_nodes)}** nodes that exist in multiple manual layers.\n")
        f.write("These nodes are critical junction points in the graph hierarchy.\n\n")
        f.write("| Node ID | Layers |\n")
        f.write("| :--- | :--- |\n")
        # List first 20 bridge nodes
        for nid, layers in list(multi_layer_nodes.items())[:20]:
            f.write(f"| {nid} | {', '.join(layers)} |\n")
            
        f.write("\n## Summary Conclusion\n\n")
        f.write("Do the algorithmically-discovered communities ALIGN with manual layers?\n\n")
        
        avg_purity = sum(s['purity'] for s in layer_stats.values()) / len(layer_stats)
        if avg_purity > 80:
            f.write(f"**Strong Alignment:** Average layer purity is {avg_purity:.2f}%. Manual layers largely correspond to structural communities.\n")
        elif avg_purity > 50:
            f.write(f"**Moderate Alignment:** Average layer purity is {avg_purity:.2f}%. Some layers are internally fragmented.\n")
        else:
            f.write(f"**Weak Alignment:** Average layer purity is {avg_purity:.2f}%. Topology does not strictly respect manual boundaries.\n")

    print(f"Audit log written to {output_path}")

if __name__ == "__main__":
    analyze()
