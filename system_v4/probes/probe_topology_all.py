import json
import glob
import os
import time
import networkx as nx
import igraph as ig
import leidenalg
import gudhi

def load_graph(path):
    with open(path, 'r') as f:
        data = json.load(f)
    G = nx.Graph()
    nodes = data.get('nodes', {})
    if isinstance(nodes, dict):
        for nid, attrs in nodes.items():
            if isinstance(attrs, dict):
                G.add_node(nid, **attrs)
            else:
                G.add_node(nid)
    elif isinstance(nodes, list):
        for n in nodes:
            nid = n.get("id") or n.get("node_id")
            if nid: G.add_node(nid, **n)
            
    edges = data.get('edges', [])
    for e in edges:
        src = e.get("source_id") or e.get("source") or e.get("from")
        tgt = e.get("target_id") or e.get("target") or e.get("to")
        if not src:
            rel_id = e.get("relation_id") or ""
            if isinstance(rel_id, str) and "::" in rel_id:
                src = rel_id.split("::")[0]
        if src and tgt:
            G.add_edge(src, tgt)
    return G

def compute_gudhi(G):
    sub = G.copy()
    if sub.number_of_edges() == 0:
        return [sub.number_of_nodes()], {}
    # Compute distances via shortest paths
    lengths = dict(nx.all_pairs_shortest_path_length(sub))
    max_d = 8
    dm = []
    sub_list = list(sub.nodes())
    for n1 in sub_list:
        row = []
        for n2 in sub_list:
            d = lengths.get(n1, {}).get(n2, max_d)
            row.append(min(d, max_d))
        dm.append(row)
    rips = gudhi.RipsComplex(distance_matrix=dm, max_edge_length=4)
    st = rips.create_simplex_tree(max_dimension=2)
    persistence = st.persistence()
    betti = st.betti_numbers()
    
    # persistence diagram stats
    h0_intervals = [p[1] for p in persistence if p[0] == 0]
    h1_intervals = [p[1] for p in persistence if p[0] == 1]
    
    def get_stats(intervals):
        if not intervals: return {"count": 0, "inf": 0, "max_life": 0}
        finite = [d - b for b, d in intervals if d < float('inf')]
        inf_count = sum(1 for b, d in intervals if d == float('inf'))
        max_life = max(finite) if finite else 0
        return {"count": len(intervals), "inf": inf_count, "max_life": round(max_life, 2)}
    
    stats = {
        "H0": get_stats(h0_intervals),
        "H1": get_stats(h1_intervals)
    }
    return betti, stats

def compute_leidenalg(G, resolutions):
    if G.number_of_edges() == 0:
        return {r: {"comm": G.number_of_nodes(), "mod": 0, "top5": [1]*(min(5, G.number_of_nodes()))} for r in resolutions}
    ig_g = ig.Graph.from_networkx(G)
    results = {}
    for res in resolutions:
        try:
            partition = leidenalg.find_partition(ig_g, leidenalg.RBConfigurationVertexPartition, resolution_parameter=res)
            n_comm = len(partition)
            mod = partition.modularity
            sizes = sorted([len(c) for c in partition], reverse=True)[:5]
            results[res] = {"comm": n_comm, "mod": round(mod, 4), "top5": sizes}
        except Exception as e:
            results[res] = {"error": str(e)}
    return results

def main():
    graph_dir = "system_v4/a2_state/graphs"
    files = sorted(glob.glob(f"{graph_dir}/*.json"))
    
    results = {}
    resolutions = [0.1, 0.5, 1.0, 2.0, 5.0]
    
    print(f"Checking {len(files)} graph files...")
    for idx, fpath in enumerate(files):
        name = os.path.basename(fpath).replace('.json', '')
        print(f"[{idx+1}/{len(files)}] Loading {name}...")
        G = load_graph(fpath)
        nodes, edges = G.number_of_nodes(), G.number_of_edges()
        if nodes >= 5000:
            print(f"  Skipping {name}: {nodes} >= 5000 nodes")
            continue
            
        print(f"  Nodes: {nodes}, Edges: {edges}")
        print("  Computing GUDHI persistence...")
        t0 = time.time()
        betti, persist_stats = compute_gudhi(G)
        t_gudhi = time.time() - t0
        
        print(f"  Computing leidenalg communities at resolutions {resolutions}...")
        t0 = time.time()
        leid = compute_leidenalg(G, resolutions)
        t_leid = time.time() - t0
        
        results[name] = {
            "nodes": nodes,
            "edges": edges,
            "betti": betti,
            "persistence": persist_stats,
            "leidenalg": leid,
            "time_gudhi": round(t_gudhi, 2),
            "time_leidenalg": round(t_leid, 2)
        }
        
    # Generate Output Markdown
    out_md = [
        "# FULL TOPOLOGY COMPARISON — v1",
        f"**Generated**: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "**Scope**: All graphs < 5000 nodes in `system_v4/a2_state/graphs/`",
        "**Tool versions**: leidenalg 0.11.0, GUDHI 3.11.0, igraph 1.0.0",
        "",
        "## 1. Graph Census and Persistence Homology (GUDHI)",
        "",
        "| Graph | Nodes | Edges | β₀ (Components) | β₁ (Cycles) | H0 Stats | H1 Stats |",
        "|-------|------:|------:|----------------:|------------:|----------|----------|"
    ]
    
    for name, data in results.items():
        betti = data['betti']
        b0 = betti[0] if len(betti) > 0 else 0
        b1 = betti[1] if len(betti) > 1 else 0
        h0_stats = data.get('persistence', {}).get('H0', {})
        h1_stats = data.get('persistence', {}).get('H1', {})
        h0 = f"{h0_stats.get('count', 0)} total, max_life={h0_stats.get('max_life', 0)}"
        h1 = f"{h1_stats.get('count', 0)} total, max_life={h1_stats.get('max_life', 0)}"
        
        out_md.append(f"| **{name}** | {data['nodes']} | {data['edges']} | {b0} | {b1} | {h0} | {h1} |")
        
    out_md.extend([
        "",
        "## 2. Multi-Resolution Community Detection (leidenalg)",
        ""
    ])
    
    for name, data in results.items():
        out_md.append(f"### {name}")
        out_md.append("| Res | Communities | Modularity (Q) | Top-5 Sizes |")
        out_md.append("|----:|------------:|---------------:|-------------|")
        for res, res_data in data['leidenalg'].items():
            if "error" in res_data:
                out_md.append(f"| {res} | ERROR | {res_data['error']} | N/A |")
            else:
                out_md.append(f"| {res} | {res_data['comm']} | {res_data['mod']} | {res_data['top5']} |")
        out_md.append("")
        
    # We will write an initial analysis here and then refine it using another step.
    
    out_path = "system_v4/a2_state/audit_logs/FULL_TOPOLOGY_COMPARISON__v1.md"
    with open(out_path, "w") as f:
        f.write("\n".join(out_md))
        
    print(f"\nReport written to {out_path}")

if __name__ == '__main__':
    main()
