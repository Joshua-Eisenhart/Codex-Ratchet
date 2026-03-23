"""
a2_obsidian_notebooklm_research_stack.py

Implements the "Claude Code + NotebookLM + Obsidian" stack natively in the A2 Pipeline.
This operator bridges the V4 Structural Memory (A2 Refinery Graph) into a local
Obsidian-compatible Markdown vault, allowing the nonclassical graph to be browsed
via Obsidian's local knowledge graph UI, and setting up the ingestion paths for
NotebookLM audio synthesis and Claude multi-path orchestration.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List
from system_v4.skills.a2_graph_refinery import A2GraphRefinery

class ObsidianNotebookLMStack:
    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root).resolve()
        self.refinery = A2GraphRefinery(str(self.root))
        
        # Target top-level vault directory
        self.vault_dir = self.root / "obsidian_vault"
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        
    def _safe_filename(self, name: str) -> str:
        """Strip invalid characters for Obsidian file names."""
        clean = re.sub(r'[\\/*?:"<>|]', "", name)
        return clean.strip() or "Unnamed_Node"

    def export_graph_to_obsidian(self) -> dict:
        """
        Projects the A2 Refinery Accumulation graph into an Obsidian vault.
        Nodes -> .md files
        Edges -> [[WikiLinks]]
        """
        graph_data = {}
        target_path = self.root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json"
        
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                graph_data = json.load(f)
                
        nodes = graph_data.get("nodes", {})
        edges = graph_data.get("edges", [])
        
        print(f"Exporting {len(nodes)} nodes and {len(edges)} edges to {self.vault_dir}...")
        
        # Pass 1: Build edge lookup mappings
        outgoing_edges: Dict[str, List[Dict]] = {}
        incoming_edges: Dict[str, List[Dict]] = {}
        
        for e in edges:
            src = e.get("source_id")
            tgt = e.get("target_id")
            rel = e.get("relation")
            
            if src not in outgoing_edges:
                outgoing_edges[src] = []
            outgoing_edges[src].append({"target": tgt, "relation": rel})
            
            if tgt not in incoming_edges:
                incoming_edges[tgt] = []
            incoming_edges[tgt].append({"source": src, "relation": rel})
            
        # Pass 2: Generate Markdown Files
        generated_files = 0
        for node_id, node in nodes.items():
            safe_name = self._safe_filename(node.get("name", node_id))
            file_path = self.vault_dir / f"{safe_name}.md"
            
            lines = []
            # YAML Frontmatter
            lines.append("---")
            lines.append(f"id: \"{node_id}\"")
            lines.append(f"type: \"{node.get('node_type', 'UNKNOWN')}\"")
            lines.append(f"layer: \"{node.get('layer', 'UNKNOWN')}\"")
            lines.append(f"authority: \"{node.get('authority', 'UNKNOWN')}\"")
            lines.append("---")
            lines.append("")
            
            # Body
            lines.append(f"# {node.get('name', 'Unnamed Node')}")
            lines.append(f"**Node ID:** `{node_id}`")
            lines.append("")
            desc = node.get("description", "")
            if desc:
                lines.append("## Description")
                lines.append(desc)
                lines.append("")
                
            # Render properties
            props = node.get("properties", {})
            if props:
                lines.append("## Properties")
                for pk, pv in props.items():
                    # Handle dicts/lists safely
                    if isinstance(pv, (dict, list)):
                        pv = json.dumps(pv)
                    lines.append(f"- **{pk}**: {str(pv)[:200]}")
                lines.append("")
                
            # Output Outgoing WikiLinks
            out_edges = outgoing_edges.get(node_id, [])
            if out_edges:
                lines.append("## Outward Relations")
                for oe in out_edges:
                    tgt_node = nodes.get(oe["target"])
                    if tgt_node:
                        tgt_name = self._safe_filename(tgt_node.get("name", oe["target"]))
                        lines.append(f"- **{oe['relation']}** → [[{tgt_name}]]")
                lines.append("")
                
            # Output Incoming WikiLinks
            in_edges = incoming_edges.get(node_id, [])
            if in_edges:
                lines.append("## Inward Relations")
                for ie in in_edges:
                    src_node = nodes.get(ie["source"])
                    if src_node:
                        src_name = self._safe_filename(src_node.get("name", ie["source"]))
                        lines.append(f"- [[{src_name}]] → **{ie['relation']}**")
                lines.append("")
                
            # Write to disk
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            generated_files += 1
            
        return {
            "status": "success",
            "vault_path": str(self.vault_dir),
            "files_generated": generated_files
        }

if __name__ == "__main__":
    stack = ObsidianNotebookLMStack("/Users/joshuaeisenhart/Desktop/Codex Ratchet")
    result = stack.export_graph_to_obsidian()
    print(f"Obsidian Vault Generation Complete: {result['files_generated']} files materialized.")
