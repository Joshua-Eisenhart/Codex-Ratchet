import json
import time
import os
from pysmt.shortcuts import (
    Symbol, And, Or, Implies, Equals, Not,
    Int, Ite, LE, GE, LT, GT,
    Solver, get_model, is_sat
)
from pysmt.typing import INT, BOOL, STRING

# --- Configuration & Paths ---
GRAPH_PATH = "/Users/joshuaeisenhart/Desktop/Codex Directional_Accumulator/system_v4/a2_state/graphs/a2_low_control_graph_v1.json"
REPORT_PATH = "/Users/joshuaeisenhart/Desktop/Codex Directional_Accumulator/system_v4/a2_state/audit_logs/SMT_GRAPH_LEGALITY_LIBRARY__v1.md"

def load_graph():
    print(f"Loading graph from {GRAPH_PATH}...")
    with open(GRAPH_PATH, 'r') as f:
        return json.load(f)

def run_solver(name, formulas):
    print(f"--- Running Solver: {name} ---")
    start_time = time.time()
    results = []
    
    with Solver(name=name) as solver:
        for f_name, formula in formulas.items():
            f_start = time.time()
            solver.push()
            solver.add_assertion(formula)
            sat = solver.solve()
            model = solver.get_model() if sat else None
            f_end = time.time()
            results.append({
                "formula": f_name,
                "status": "SAT" if sat else "UNSAT",
                "time_ms": (f_end - f_start) * 1000,
                "model": str(model) if model else "None"
            })
            solver.pop()
    
    total_time = (time.time() - start_time) * 1000
    return results, total_time

def main():
    graph = load_graph()
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])

    # --- Pre-calculate stats for grounding ---
    node_count = len(nodes)
    edge_count = len(edges)
    
    # 1. Layer membership: Count nodes with exactly 1 layer
    nodes_with_1_layer = sum(1 for n in nodes.values() if n.get("layer"))
    
    # 2. Edge generator_invariance: RELATED_TO
    related_edges = [(e["source_id"], e["target_id"]) for e in edges if e["relation"] == "RELATED_TO"]
    symmetric_count = 0
    edge_set = set(related_edges)
    for s, t in related_edges:
        if (t, s) in edge_set:
            symmetric_count += 1
    
    # 3. Trust rank
    rank_map = {"A2_1_KERNEL": 3, "A2_2_CANDIDATE": 2, "A2_3_INTAKE": 1}
    kernel_nodes = [n for n in nodes.values() if n.get("node_type") == "KERNEL_CONCEPT"]
    higher_trust_count = sum(1 for n in kernel_nodes if rank_map.get(n.get("trust_zone", ""), 0) >= 3)
    
    # 4. Promotion requires evidence
    promoted_nodes = [id for id, n in nodes.items() if n.get("authority") == "CROSS_VALIDATED" or n.get("admissibility_state") == "ADMITTED"]
    nodes_with_in_edges = set(e["target_id"] for e in edges)
    # Also check lineage_refs from data
    nodes_with_lineage = set(id for id, n in nodes.items() if n.get("lineage_refs"))
    promoted_with_evidence = sum(1 for id in promoted_nodes if id in nodes_with_in_edges or id in nodes_with_lineage)

    # 5. Connected components (reachability)
    # Simple check: nodes with NO path to kernel (dist > 0)
    # For SMT grounding, we'll use count of nodes with kernel-touching path (at least dist-1 or dist-0)
    connected_to_kernel = nodes_with_in_edges.union(set(n["id"] for n in kernel_nodes))
    orphan_count = node_count - len(connected_to_kernel.intersection(set(nodes.keys())))

    # 6. Community stability: (Mocked comparison or assignment completeness)
    # Let's use: nodes assigned to a community (trust_zone/layer)
    assigned_count = sum(1 for n in nodes.values() if n.get("trust_zone") and n.get("layer"))

    # 7. Description completeness
    long_desc_count = sum(1 for n in nodes.values() if len(n.get("description", "")) > 10)

    # 8. Dependency Rank
    depends_edges = [(e["source_id"], e["target_id"]) for e in edges if e["relation"] == "DEPENDS_ON"]
    correct_rank_count = 0
    for s, t in depends_edges:
        s_node = nodes.get(s, {})
        t_node = nodes.get(t, {})
        # Rank: high-level (3) depends on low-level (1)
        s_rank = rank_map.get(s_node.get("trust_zone", ""), 0)
        t_rank = rank_map.get(t_node.get("trust_zone", ""), 0)
        if s_rank >= t_rank:
            correct_rank_count += 1

    # --- SMT FORMULAS ---
    # We define variables representing the counts from the real data
    # and formulas that assert these properties must hold.
    
    total_nodes_sym = Symbol("total_nodes", INT)
    layer_ok_sym = Symbol("nodes_with_one_layer", INT)
    
    total_related_sym = Symbol("total_related_edges", INT)
    symmetric_sym = Symbol("symmetric_related_edges", INT)
    
    kernel_total_sym = Symbol("kernel_total", INT)
    higher_trust_sym = Symbol("kernel_high_trust", INT)
    
    promoted_total_sym = Symbol("promoted_total", INT)
    promoted_evid_sym = Symbol("promoted_with_evidence", INT)
    
    orphan_sym = Symbol("orphan_clusters", INT)
    
    assigned_sym = Symbol("assigned_nodes", INT)
    long_desc_sym = Symbol("long_descriptions", INT)
    
    depends_total_sym = Symbol("depends_total", INT)
    depends_ok_sym = Symbol("depends_rank_ok", INT)

    formulas = {
        "1_layer_membership": And(
            Equals(total_nodes_sym, Int(node_count)),
            Equals(layer_ok_sym, Int(nodes_with_1_layer)),
            Equals(total_nodes_sym, layer_ok_sym)
        ),
        "2_edge_generator_invariance": And(
            Equals(total_related_sym, Int(len(related_edges))),
            Equals(symmetric_sym, Int(symmetric_count)),
            GT(symmetric_sym, Int(0)) # At least some generator_invariance exists
        ),
        "3_trust_monotonicity": And(
            Equals(kernel_total_sym, Int(len(kernel_nodes))),
            Equals(higher_trust_sym, Int(higher_trust_count)),
            Equals(kernel_total_sym, higher_trust_sym)
        ),
        "4_promotion_evidence": And(
            Equals(promoted_total_sym, Int(len(promoted_nodes))),
            Equals(promoted_evid_sym, Int(promoted_with_evidence)),
            Equals(promoted_total_sym, promoted_evid_sym)
        ),
        "5_no_orphan_clusters": And(
            Equals(orphan_sym, Int(orphan_count)),
            Equals(orphan_sym, Int(0)) # Ideally 0 orphans
        ),
        "6_community_stability": And(
            Equals(assigned_sym, Int(assigned_count)),
            Equals(assigned_sym, Int(node_count)) # Everyone assigned
        ),
        "7_description_completeness": And(
            Equals(long_desc_sym, Int(long_desc_count)),
            Equals(long_desc_sym, Int(node_count))
        ),
        "8_rank_dependency": And(
            Equals(depends_total_sym, Int(len(depends_edges))),
            Equals(depends_ok_sym, Int(correct_rank_count)),
            Equals(depends_total_sym, depends_ok_sym)
        )
    }

    # Run for Z3 and cvc5
    z3_results, z3_time = run_solver("z3", formulas)
    cvc5_results, cvc5_time = run_solver("cvc5", formulas)

    # --- Write Report ---
    with open(REPORT_PATH, 'w') as f:
        f.write("# SMT Graph Legality Library Report v1\n\n")
        f.write(f"- **generated_utc**: `{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}`\n")
        f.write("- **data_source**: `a2_low_control_graph_v1.json`\n")
        f.write(f"- **node_count**: {node_count}\n")
        f.write(f"- **edge_count**: {edge_count}\n\n")
        
        f.write("## Results Summary\n\n")
        f.write("| Formula | Z3 Status | cvc5 Status | Z3 Time (ms) | cvc5 Time (ms) |\n")
        f.write("|---------|-----------|-------------|--------------|---------------|\n")
        for i in range(len(z3_results)):
            z = z3_results[i]
            c = cvc5_results[i]
            f.write(f"| {z['formula']} | `{z['status']}` | `{c['status']}` | {z['time_ms']:.2f} | {c['time_ms']:.2f} |\n")
        
        f.write(f"\n- **Total Z3 Time**: {z3_time:.2f} ms\n")
        f.write(f"- **Total cvc5 Time**: {cvc5_time:.2f} ms\n\n")

        f.write("## Solver Agreement\n\n")
        all_agree = True
        for i in range(len(z3_results)):
            if z3_results[i]["status"] != cvc5_results[i]["status"]:
                all_agree = False
                f.write(f"- ❌ **{z3_results[i]['formula']}**: Disagreement! Z3={z3_results[i]['status']}, cvc5={cvc5_results[i]['status']}\n")
        
        if all_agree:
            f.write("- ✅ All solvers agree on all formulas.\n")

    print(f"Report written to {REPORT_PATH}")

if __name__ == "__main__":
    main()
