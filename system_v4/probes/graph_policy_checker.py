#!/usr/bin/env python3
import json
import os
import glob
from typing import List, Dict, Any, Set

class GraphPolicyChecker:
    def __init__(self, graph_paths: List[str]):
        self.graph_paths = graph_paths
        self.graphs = {}
        self.load_graphs()
        self.promoted_nodes_ids = self.get_promoted_node_ids()

    def load_graphs(self):
        for path in self.graph_paths:
            try:
                with open(path, 'r') as f:
                    self.graphs[path] = json.load(f)
            except Exception as e:
                print(f"Error loading {path}: {e}")

    def get_promoted_node_ids(self) -> Set[str]:
        # Identify promoted nodes from a specific file if it exists
        promoted_file = "system_v4/a2_state/graphs/promoted_subgraph.json"
        if os.path.exists(promoted_file):
            try:
                with open(promoted_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('nodes', {}).keys())
            except Exception as e:
                print(f"Error loading promoted subgraph: {e}")
        return set()

    def run_policies(self):
        results = {}
        for path, graph in self.graphs.items():
            graph_results = {
                "rule1_kernel_admissibility": self.check_kernel_admissibility(graph),
                "rule2_no_dangling_edges": self.check_no_dangling_edges(graph),
                "rule3_promoted_visibility": self.check_promoted_visibility(graph),
                "rule4_skill_operation_type": self.check_skill_operation_type(graph),
                "rule5_graveyard_live_edges": self.check_graveyard_live_edges(graph)
            }
            results[path] = graph_results
        return results

    def check_kernel_admissibility(self, graph: Dict[str, Any]):
        violations = []
        nodes = graph.get('nodes', {})
        for node_id, node in nodes.items():
            if node.get('node_type') == "KERNEL_CONCEPT":
                if node.get('admissibility_state') != "ADMITTED":
                    violations.append(node_id)
        return {"pass": len(violations) == 0, "violations": violations}

    def check_no_dangling_edges(self, graph: Dict[str, Any]):
        violations = []
        nodes = graph.get('nodes', {})
        edges = graph.get('edges', [])
        for edge in edges:
            source_id = edge.get('source_id')
            target_id = edge.get('target_id')
            if source_id not in nodes:
                violations.append(f"Edge {edge.get('relation_id')} references non-existent source {source_id}")
            if target_id not in nodes:
                violations.append(f"Edge {edge.get('relation_id')} references non-existent target {target_id}")
        return {"pass": len(violations) == 0, "violations": violations}

    def check_promoted_visibility(self, graph: Dict[str, Any]):
        # This rule says "promoted nodes must appear in at least 2 layer graphs"
        # We check each node in the current graph: if it's "promoted", is it in any OTHER loaded graph?
        violations = []
        nodes = graph.get('nodes', {})
        for node_id in nodes:
            if node_id in self.promoted_nodes_ids:
                count = 0
                for g_path, g_data in self.graphs.items():
                    if node_id in g_data.get('nodes', {}):
                        count += 1
                if count < 2:
                    violations.append(node_id)
        return {"pass": len(violations) == 0, "violations": violations}

    def check_skill_operation_type(self, graph: Dict[str, Any]):
        violations = []
        nodes = graph.get('nodes', {})
        for node_id, node in nodes.items():
            if node.get('node_type') == "SKILL":
                # Check top-level or properties
                op_type = node.get('operation_type') or node.get('properties', {}).get('operation_type')
                if not op_type:
                    violations.append(node_id)
        return {"pass": len(violations) == 0, "violations": violations}

    def check_graveyard_live_edges(self, graph: Dict[str, Any]):
        violations = []
        nodes = graph.get('nodes', {})
        edges = graph.get('edges', [])
        
        # Identify graveyard nodes (ID contains "graveyard")
        graveyard_ids = {node_id for node_id in nodes if "graveyard" in node_id.lower()}
        
        for edge in edges:
            source_id = edge.get('source_id')
            target_id = edge.get('target_id')
            if (source_id in graveyard_ids or target_id in graveyard_ids) and edge.get('status') == "LIVE":
                violations.append(edge.get('relation_id'))
        
        return {"pass": len(violations) == 0, "violations": violations}

def generate_report(results: Dict[str, Any], output_path: str):
    with open(output_path, 'w') as f:
        f.write("# POLICY PROCESS_CYCLE EVALUATION REPORT - v1\n\n")
        f.write("## Executive Summary\n\n")
        
        # Summary Table
        f.write("| Graph | Rule 1 | Rule 2 | Rule 3 | Rule 4 | Rule 5 |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")
        
        for path, graph_results in results.items():
            base_name = os.path.basename(path)
            row = [base_name]
            for rule in ["rule1_kernel_admissibility", "rule2_no_dangling_edges", "rule3_promoted_visibility", "rule4_skill_operation_type", "rule5_graveyard_live_edges"]:
                res = graph_results[rule]
                row.append("✅ PASS" if res["pass"] else f"❌ FAIL ({len(res['violations'])})")
            f.write(f"| {' | '.join(row)} |\n")
        
        f.write("\n## Policy Details\n\n")
        f.write("1. **Kernel nodes** must have `admissibility_state = ADMITTED`.\n")
        f.write("2. **No edge** may reference a non-existent node.\n")
        f.write("3. **Promoted nodes** must appear in at least 2 layer graphs.\n")
        f.write("4. **Skill nodes** must have `operation_type` defined.\n")
        f.write("5. **Graveyard nodes** must not have `LIVE` status edges.\n")
        
        f.write("\n## Detailed Violations\n\n")
        has_violations = False
        for path, graph_results in results.items():
            graph_has_violations = any(not res["pass"] for res in graph_results.values())
            if graph_has_violations:
                has_violations = True
                f.write(f"### {os.path.basename(path)}\n")
                for rule, res in graph_results.items():
                    if not res["pass"]:
                        f.write(f"- **{rule}**: {len(res['violations'])} violations found.\n")
                        # Show first 5 violations
                        for v in res['violations'][:5]:
                            f.write(f"  - `{v}`\n")
                        if len(res['violations']) > 5:
                            f.write(f"  - ... and {len(res['violations']) - 5} more.\n")
                f.write("\n")
        
        if not has_violations:
            f.write("No violations found across all evaluated graphs.\n")

if __name__ == "__main__":
    # Define paths to scan
    graph_files = glob.glob("system_v4/a2_state/graphs/*.json") + glob.glob("system_v4/a1_state/*.json")
    # Filter out non-graph files if any (like session.json)
    graph_files = [p for p in graph_files if "graph" in p.lower() or "subgraph" in p.lower() or "projection" in p.lower() or "registry" in p.lower()]
    
    checker = GraphPolicyChecker(graph_files)
    all_results = checker.run_policies()
    
    report_path = "system_v4/a2_state/audit_logs/POLICY_PROCESS_CYCLE_EVALUATION_REPORT__v1.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    generate_report(all_results, report_path)
    print(f"Report generated at {report_path}")
