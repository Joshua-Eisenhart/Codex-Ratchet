import os
import re
from pathlib import Path
from system_v4.skills.v4_graph_builder import SystemGraphBuilder, GraphNode, GraphEdge

def ingest_full_v3():
    print("--- [ V4 A2 Refinery: Full System V3 Ingest ] ---")
    workspace = Path(os.path.abspath(".")).resolve()
    builder = SystemGraphBuilder(str(workspace))
    
    v3_dir = workspace / "system_v3"
    print(f"Scanning full V3 state at {v3_dir}...")
    
    if not v3_dir.exists():
        print("system_v3 not found!")
        return
        
    for root, dirs, files in os.walk(v3_dir):
        root_path = Path(root)
        
        for f in files:
            if not f.endswith('.md') and not f.endswith('.json') and not f.endswith('.py') and not f.endswith('.jsonl') and not f.endswith('.txt'):
                continue
                
            file_path = root_path / f
            dir_name = file_path.parent.name
            
            # Simple heuristic
            layer = "UNKNOWN"
            node_type = "STATE_SURFACE"
            
            if "a2_state" in root:
                layer = "A2"
                node_type = "MEMORY_SURFACE" if "memory" in f or "log" in f.lower() else "CONTROL_SURFACE"
            elif "a1_state" in root:
                layer = "A1"
                node_type = "QUEUE_SURFACE"
            elif "b_state" in root:
                layer = "B"
                node_type = "ADJUDICATION_SURFACE"
            elif "specs" in root:
                layer = "CONTROL_PLANE"
                node_type = "SPEC" if "SPEC" in f else "CONTRACT" if "CONTRACT" in f else "PROTOCOL"
            elif "tools" in root or "skills" in root:
                layer = "OPERATIONS"
                node_type = "SKILL"
            elif "public_facing_docs" in root:
                layer = "INTERFACE"
                node_type = "PUBLIC_DOC"
            else:
                layer = "A0"
                
            try:
                size = file_path.stat().st_size
            except Exception:
                size = 0
            
            node = GraphNode(
                id=f"V3_{layer}::{f}",
                node_type=node_type,
                layer=layer,
                name=f,
                description=f"Ingested {node_type} from system_v3/{dir_name}",
                original_path=str(file_path.relative_to(workspace)),
                properties={"size_bytes": size, "state_dir": dir_name}
            )
            builder.add_node(node)

    builder.save_graph_artifacts(version_label="v3_full_system_ingest_v1")
    
    print("\n--- [ Graphification Complete ] ---")
    print(f"Total Nodes: {len(builder.pydantic_model.nodes)}")
    print(f"Saved to: {builder.a2_sandbox_dir}")

if __name__ == "__main__":
    ingest_full_v3()
