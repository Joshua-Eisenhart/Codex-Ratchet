import json
import os
from typing import Dict, List, Set, Tuple

def load_graph(path: str) -> dict:
    with open(path, 'r') as f:
        return json.load(f)

def get_node_ids(graph: dict) -> Set[str]:
    return set(graph.get('nodes', {}).keys())

def get_edge_tuples(graph: dict) -> Set[Tuple[str, str]]:
    edges = graph.get('edges', [])
    edge_set = set()
    for edge in edges:
        s = edge.get('source_id')
        t = edge.get('target_id')
        if s and t:
            # Using sorted tuple for undirected comparison if needed, 
            # but usually these graphs are directed. 
            # Let's keep them as (s, t) for directed accuracy.
            edge_set.add((s, t))
    return edge_set

def compute_jaccard(set1: Set, set2: Set) -> float:
    if not set1 and not set2:
        return 1.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def main():
    base_path = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs"
    graph_files = {
        "A2_INTAKE": "a2_high_intake_graph_v1.json",
        "A2_REFINEMENT": "a2_mid_refinement_graph_v1.json",
        "A2_CONTROL": "a2_low_control_graph_v1.json",
        "PROMOTED": "promoted_subgraph.json",
        "A1_JARGONED": "a1_jargoned_graph_v1.json"
    }
    
    graphs = {}
    node_sets = {}
    edge_sets = {}
    
    print("Loading graphs...")
    for label, filename in graph_files.items():
        path = os.path.join(base_path, filename)
        g = load_graph(path)
        graphs[label] = g
        node_sets[label] = get_node_ids(g)
        edge_sets[label] = get_edge_tuples(g)
        print(f"Loaded {label}: {len(node_sets[label])} nodes, {len(edge_sets[label])} edges")

    labels = list(graph_files.keys())
    
    # 1. Pairwise metrics
    results = []
    results.append("# Cross-Graph Overlap Analysis Report\n")
    results.append("## Node Connectivity and Overlap Matrix\n")
    
    # Jaccard Similarity Matrix
    header = "| | " + " | ".join(labels) + " |"
    divider = "|---|" + "|".join(["---" for _ in labels]) + "|"
    results.append(header)
    results.append(divider)
    
    for row_label in labels:
        row = [f"**{row_label}**"]
        for col_label in labels:
            sim = compute_jaccard(node_sets[row_label], node_sets[col_label])
            row.append(f"{sim:.4f}")
        results.append("| " + " | ".join(row) + " |")
    
    results.append("\n## Pairwise Intersection Details\n")
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            l1, l2 = labels[i], labels[j]
            shared_nodes = node_sets[l1].intersection(node_sets[l2])
            unique1 = node_sets[l1] - node_sets[l2]
            unique2 = node_sets[l2] - node_sets[l1]
            shared_edges = edge_sets[l1].intersection(edge_sets[l2])
            
            results.append(f"### {l1} vs {l2}")
            results.append(f"- **Shared Nodes:** {len(shared_nodes)}")
            results.append(f"- **Unique to {l1}:** {len(unique1)}")
            results.append(f"- **Unique to {l2}:** {len(unique2)}")
            results.append(f"- **Shared Edges:** {len(shared_edges)}\n")

    # 3. Subset check: Promoted in Control?
    results.append("## Critical Integrity Checks\n")
    is_subset = node_sets["PROMOTED"].issubset(node_sets["A2_CONTROL"])
    status = "PASS" if is_subset else "FAIL"
    results.append(f"### 1. Promoted ⊆ Low-Control")
    results.append(f"- **Status:** {status}")
    if not is_subset:
        missing = node_sets["PROMOTED"] - node_sets["A2_CONTROL"]
        results.append(f"- **Missing Nodes from Control ({len(missing)}):**")
        for m in list(missing)[:10]:
            results.append(f"  - `{m}`")
        if len(missing) > 10:
            results.append(f"  - ... and {len(missing) - 10} more.")
    
    # 4. Flow Down: Intake -> Refinement -> Control
    results.append("\n### 2. Flow Integrity (Intake → Refinement → Control)")
    # A node in Refinement should be from Intake OR be a new synthetic Refined node (A2_2)
    # Actually, the check is usually: if it's in Control, was it in Refinement?
    
    ref_not_in_intake = node_sets["A2_REFINEMENT"] - node_sets["A2_INTAKE"]
    results.append(f"- **Refinement nodes not in Intake:** {len(ref_not_in_intake)}")
    
    ctrl_not_in_ref = node_sets["A2_CONTROL"] - node_sets["A2_REFINEMENT"]
    results.append(f"- **Control nodes not in Refinement:** {len(ctrl_not_in_ref)}")
    
    # 5. Unexpected nodes
    results.append("\n### 3. Unexpected Placements")
    # For example: nodes in Control that aren't in Refinement or Intake (Spontaneous generation?)
    spontaneous = node_sets["A2_CONTROL"] - node_sets["A2_REFINEMENT"] - node_sets["A2_INTAKE"]
    results.append(f"- **Spontaneous nodes in Control (not in Ref/Intake):** {len(spontaneous)}")
    if spontaneous:
        results.append("  - Examples:")
        for s in list(spontaneous)[:5]:
            results.append(f"    - `{s}`")

    # Write final report
    report_path = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/CROSS_GRAPH_OVERLAP_ANALYSIS__v1.md"
    with open(report_path, 'w') as f:
        f.write("\n".join(results))
    
    print(f"Analysis complete. Report written to {report_path}")

if __name__ == "__main__":
    main()
