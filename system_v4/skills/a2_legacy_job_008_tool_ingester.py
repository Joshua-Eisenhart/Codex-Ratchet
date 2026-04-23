"""
a2_legacy_job_008_tool_ingester.py

Ingests the final GPT-Pro companion thread (JOB 008) output which maps 215 legacy 
v3 tools to current v4 skills. This script reads the companion YAML file from the 
threads results directory, establishes LEGACY_TOOL node identities, and maps 
DIRECT_PORT, ABSORBED_INTO, and SPLIT_INTO structural edges directly to the v4 
A2 skill graph.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
from system_v4.skills.v4_graph_builder import GraphNode, GraphEdge
from system_v4.skills.a2_graph_refinery import A2GraphRefinery

class Job008Ingester:
    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root).resolve()
        self.refinery = A2GraphRefinery(str(self.root))
        
        # This defaults to the standard target output path from the GPT-Pro companion
        self.yaml_path = self.root / "threads" / "results" / "JOB_008" / "JOB_008_v3_tool_to_v4_skill_bridge_map_v1.yaml"
        
    def _safe_skill_id(self, name: str) -> str:
        """Normalize V4 Skill target to ID."""
        clean = name.replace("-", "_").replace(".py", "").lower()
        return f"SKILL::{clean}"
        
    def _safe_legacy_id(self, name: str) -> str:
        """Normalize V3 tool target to ID."""
        clean = name.replace(".py", "").lower()
        return f"LEGACY_V3_TOOL::{clean}"

    def run_ingestion(self) -> dict:
        if not self.yaml_path.exists():
            print(f"File not found: {self.yaml_path}")
            print("Please ensure you have downloaded the JOB_008 companion output from the GPT Sandbox.")
            return {"status": "missing_file"}
            
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        if not data or not isinstance(data, dict):
            return {"status": "invalid_yaml"}
            
        added_nodes = 0
        added_edges = 0
        
        # The structure is expected to list v3 tools and their mapped v4 targets
        for map_type in ["DIRECT_PORT", "ABSORBED_INTO", "SPLIT_INTO"]:
            entries = data.get(map_type, [])
            for entry in entries:
                # E.g. {"legacy_tool": "a0_base.py", "v4_targets": ["a2_boot.py"]}
                v3_name = entry.get("legacy_tool", "unknown")
                v4_targets = entry.get("v4_targets", [])
                
                v3_id = self._safe_legacy_id(v3_name)
                
                # Materialize the Legacy Tool Node
                if not self.refinery.builder.node_exists(v3_id):
                    self.refinery.builder.add_node(GraphNode(
                        id=v3_id,
                        node_type="LEGACY_V3_TOOL",
                        name=v3_name,
                        description=f"Legacy Tool from V3 System mapped in JOB 008",
                        layer="A1_JARGONED",
                        trust_zone="A1",
                        authority="SOURCE_DOCUMENT_MAP",
                        properties={"mapped_type": map_type, "low_confidence": entry.get("low_confidence", False)}
                    ))
                    added_nodes += 1
                
                # Add directional mapping edges towards active V4 Skills
                for target in v4_targets:
                    v4_id = self._safe_skill_id(target)
                    
                    self.refinery.builder.add_edge(GraphEdge(
                        source_id=v3_id, target_id=v4_id,
                        relation=f"{map_type}_TO", attributes={"job_source": "JOB_008"}
                    ))
                    added_edges += 1
                    
        self.refinery._save()
        return {
            "status": "success",
            "nodes_added": added_nodes,
            "edges_added": added_edges
        }

if __name__ == "__main__":
    ingester = Job008Ingester(str(Path(__file__).resolve().parents[2]))
    res = ingester.run_ingestion()
    if res["status"] == "success":
        print(f"Successfully processed JOB_008: Added {res['nodes_added']} legacy nodes and {res['edges_added']} mapping edges.")
