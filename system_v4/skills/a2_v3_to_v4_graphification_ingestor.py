import os
import re
from pathlib import Path
from system_v4.skills.v4_graph_builder import SystemGraphBuilder, GraphNode, GraphEdge

def ingest_v3_into_v4_graph():
    print("--- [ V4 A2 Refinery: V3 Graphification Ingest ] ---")
    workspace = Path(os.path.abspath(".")).resolve()
    builder = SystemGraphBuilder(str(workspace))
    
    # Ingest system_v3/specs as Protocol / Constraint nodes
    specs_dir = workspace / "system_v3" / "specs"
    print(f"Scanning V3 Specs at {specs_dir}...")
    
    if specs_dir.exists():
        for md_file in specs_dir.glob("*.md"):
            # Determine loose layer/type heuristically from filename
            name = md_file.name
            layer = "CONTROL_PLANE"
            if "A2" in name: layer = "A2"
            elif "A1" in name: layer = "A1"
            elif "A0" in name: layer = "A0"
            elif "B_" in name: layer = "B"
            elif "SIM" in name: layer = "SIM"
            
            node_type = "PROTOCOL"
            if "CONTRACT" in name: node_type = "CONTRACT"
            elif "SPEC" in name: node_type = "SPEC"
            elif "CONSTRAINT" in name: node_type = "CONSTRAINT"
            
            node = GraphNode(
                id=f"V3_SPEC::{name}",
                node_type=node_type,
                layer=layer,
                name=name,
                description="Ingested flat markdown specification from V3.",
                original_path=str(md_file.relative_to(workspace)),
                properties={"size_bytes": md_file.stat().st_size}
            )
            builder.add_node(node)
            print(f" > Added Node: {node.id}")
            
    # Ingest system_v3/tools as Skill / Agent nodes
    tools_dir = workspace / "system_v3" / "tools"
    print(f"\nScanning V3 Tools at {tools_dir}...")
    
    tool_nodes = {}
    if tools_dir.exists():
        for py_file in tools_dir.glob("*.py"):
            name = py_file.name
            layer = "OPERATIONS"
            if "a2_" in name: layer = "A2"
            elif "a1_" in name: layer = "A1"
            elif "a0_" in name: layer = "A0"
            elif "browser_" in name: layer = "SIM_UI"
            elif "audit_" in name: layer = "AUDIT"
            
            node_type = "SKILL"
            if "runner" in name or "controller" in name: node_type = "AGENT"
            elif "audit" in name: node_type = "VALIDATOR"
            
            node = GraphNode(
                id=f"V3_TOOL::{name}",
                node_type=node_type,
                layer=layer,
                name=name,
                description="Ingested flat python script from V3.",
                original_path=str(py_file.relative_to(workspace)),
                properties={"size_bytes": py_file.stat().st_size}
            )
            builder.add_node(node)
            tool_nodes[name] = node
            print(f" > Added Node: {node.id}")
            
            # Simple heuristic dependency edge extraction (regexing for imports)
            try:
                content = py_file.read_text(encoding='utf-8')
                for other_tool in tools_dir.glob("*.py"):
                    if other_tool.name != name:
                        # Extract base module names (e.g. from 'system_v3.tools.build_export_candidate_pack import ...')
                        base_mod = other_tool.stem
                        if re.search(r'import\s+.*' + base_mod, content) or re.search(r'from\s+.*' + base_mod + r'\s+import', content):
                            edge = GraphEdge(
                                source_id=node.id,
                                target_id=f"V3_TOOL::{other_tool.name}",
                                relation="IMPORTS_FROM"
                            )
                            builder.add_edge(edge)
            except Exception:
                pass # skip unreadable files during simple static analysis
    
    # Save the resultant Graph into the A2 Sandbox
    builder.save_graph_artifacts(version_label="v3_ingest_pass1")
    
    print("\n--- [ Graphification Complete ] ---")
    print(f"Total Nodes: {len(builder.pydantic_model.nodes)}")
    print(f"Total Edges: {len(builder.pydantic_model.edges)}")
    print(f"Saved to: {builder.a2_sandbox_dir}")

if __name__ == "__main__":
    ingest_v3_into_v4_graph()
