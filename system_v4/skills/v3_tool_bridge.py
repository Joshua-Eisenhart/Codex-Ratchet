import json
import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any

# Ensure we can import system_v4
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.v4_graph_builder import SystemGraphBuilder, GraphNode, GraphEdge

def map_v3_to_v4(v3_tools: dict, v4_skills: list[str]) -> dict[str, str]:
    """Attempt basic fuzzy/keyword mapping from v3 tool to v4 skill."""
    mapping = {}
    
    # Pre-process v4 names for matching
    v4_keywords = {}
    for skill in v4_skills:
        name = skill.replace("v4_skill::", "")
        parts = set(name.split("_"))
        v4_keywords[skill] = parts

    for t_id, info in v3_tools.items():
        name = info["name"].lower()
        parts = set(name.replace("-", "_").split("_"))
        
        # 1. Exact match (rare)
        exact_match = f"v4_skill::{name}"
        if exact_match in v4_skills:
            mapping[t_id] = exact_match
            continue
            
        # 2. Strong overlap (e.g. read_document -> document_reader)
        best_match = None
        best_score = 0
        for s_id, s_words in v4_keywords.items():
            overlap = len(parts.intersection(s_words))
            score = overlap / max(len(parts), len(s_words)) if parts else 0
            if score > 0.4 and score > best_score:
                best_match = s_id
                best_score = score
                
        if best_match:
            mapping[t_id] = best_match
        else:
            mapping[t_id] = "v4_gov::ratchet_core" # Default fallback
            
    return mapping

def run_bridge(workspace_root: str):
    root = Path(workspace_root).resolve()
    graph_path = root / "system_v4" / "a2_state" / "graphs" / "system_architecture_v1.json"
    
    print("Loading architecture graph...")
    with graph_path.open() as f:
        graph = json.load(f)
    
    v3_tools = {}
    v4_skills = []
    
    for n_id, n in graph.get("nodes", {}).items():
        if n.get("node_type") == "V3_TOOL":
            v3_tools[n_id] = {"name": n.get("name", n_id)}
        elif n.get("node_type") == "V4_SKILL" or n_id.startswith("v4_skill::"):
            v4_skills.append(n_id)
            
    print(f"Found {len(v3_tools)} V3 tools and {len(v4_skills)} V4 skills in graph.")
    
    print("Mapping V3 tools to V4 skills...")
    mapping = map_v3_to_v4(v3_tools, v4_skills)
    
    added_edges = 0
    edges = graph.get("edges", [])
    existing_edge_ids = {e.get("relation_id") for e in edges if "relation_id" in e}
    
    for t_id, info in v3_tools.items():
        target_skill = mapping.get(t_id)
        if target_skill and target_skill in graph.get("nodes", {}):
            edge_id = f"EDGE::{t_id}--EVOLVED_INTO-->{target_skill}"
            if edge_id not in existing_edge_ids:
                edges.append({
                    "source": t_id,
                    "target": target_skill,
                    "relation": "EVOLVED_INTO",
                    "relation_id": edge_id,
                    "trust_zone": "GRAVEYARD",
                    "attributes": {"confidence": 0.8}
                })
                existing_edge_ids.add(edge_id)
                added_edges += 1
            
    print(f"Graph updated: +{added_edges} new EVOLVED_INTO edges.")
    if added_edges > 0:
        graph["stats"]["edges_by_type"]["EVOLVED_INTO"] = graph["stats"].get("edges_by_type", {}).get("EVOLVED_INTO", 0) + added_edges
        graph["stats"]["total_edges"] += added_edges
        with graph_path.open("w") as f:
            json.dump(graph, f, indent=2)
    
    # 2. Update Governance Map
    gov_path = root / "system_v4" / "a2_state" / "v3_v4_governance_map_v1.json"
    if gov_path.exists():
        with gov_path.open() as f:
            gov = json.load(f)
            
        if "v3_tool_mapping" not in gov:
            gov["v3_tool_mapping"] = {}
            
        gov["v3_tool_mapping"].update(mapping)
        gov["stats"]["v3_tools_mapped"] = len(mapping)
        gov["stats"]["v3_to_v4_edges"] = added_edges
        
        with gov_path.open("w") as f:
            json.dump(gov, f, indent=2)
            
        print("Updated v3_v4_governance_map_v1.json")

if __name__ == "__main__":
    run_bridge(str(Path(__file__).resolve().parents[2]))
