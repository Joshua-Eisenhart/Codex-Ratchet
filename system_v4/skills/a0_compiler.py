"""
a0_compiler.py — A0 Block Compilation Skill

Takes A1_CARTRIDGE packages (which contain multi-lane adversarial bounds)
and compiles them down to deterministic A0_COMPILED execution blocks.
An A0_COMPILED node represents an atomic, verifiable test structure that has
had all residual narrative ambiguity squeezed out.
"""

import json
from typing import Optional

class A0Compiler:
    def __init__(self, refinery):
        self.refinery = refinery

    def compile_cartridge(self, node_id: str) -> Optional[str]:
        """
        Compiles an A1_CARTRIDGE into an A0_COMPILED node.
        """
        pydantic_nodes = self.refinery.builder.pydantic_model.nodes
        graph = self.refinery.builder.graph
        
        found_id = None
        if node_id in pydantic_nodes:
            found_id = node_id
        else:
            for nid, data in pydantic_nodes.items():
                if data.name == node_id:
                    found_id = nid
                    break
                    
        if not found_id:
            print(f"Error: Cartridge {node_id} not found.")
            return None

        node = pydantic_nodes[found_id]
        if node.layer != "A1_CARTRIDGE":
            print(f"Error: Node {node_id} is layer {node.layer}, expected A1_CARTRIDGE.")
            return None

        orig_name = node.name.replace("_CARTRIDGE", "")
        compiled_id = f"A0_COMPILED::{orig_name}"
        
        if compiled_id in pydantic_nodes:
            return compiled_id

        # Compile the logic
        # In a real compiler, we would generate actual Python or Verilog ASTs here.
        # For the proto-loop, we squeeze the cartridge into a strict pseudo-code schema.
        props = node.properties
        
        compiled_logic = {
            "test_target": props.get("candidate_shape", "UNKNOWN"),
            "assertions": [
                {
                    "type": "POSITIVE_STEELMAN",
                    "condition": props.get("steelman_positive", "")
                },
                {
                    "type": "NEGATIVE_BOUNDARY",
                    "condition": props.get("adversarial_negative", "")
                }
            ],
            "execution": {
                "on_success": props.get("success_condition", "PASS"),
                "on_failure": props.get("fail_condition", "FAIL_CLOSED")
            }
        }
        
        from system_v4.skills.v4_graph_builder import GraphNode, GraphEdge
        builder = self.refinery.builder

        builder.add_node(GraphNode(
            id=compiled_id,
            node_type="EXECUTION_BLOCK",
            name=f"{orig_name}_COMPILED",
            description=f"Deterministic A0 compilation of {orig_name}",
            layer="A0_COMPILED",
            trust_zone="A0_COMPILED",
            authority="CROSS_VALIDATED",
            properties={"compiled_logic": json.dumps(compiled_logic, indent=2)}
        ))
        self.refinery.log_finding(f"Compiled A0_COMPILED block for: {orig_name}")

        builder.add_edge(GraphEdge(
            source_id=compiled_id, target_id=found_id,
            relation="COMPILED_FROM", attributes={}
        ))

        self.refinery._save()
        return compiled_id
