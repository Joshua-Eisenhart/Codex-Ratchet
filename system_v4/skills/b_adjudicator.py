"""
b_adjudicator.py — B-Layer Adjudication Skill

The B layer acts as a mechanical gatekeeper. It does not look at empirical evidence;
it only validates the structural integrity and logic bounding of A0_COMPILED blocks.
If the block's mathematical or logical assertions are sound, it issues an ACCEPT
or PARK. If invalid, it issues a REJECT (triggering thermodynamic routing).
"""

import json
from typing import Optional

class BAdjudicator:
    def __init__(self, refinery):
        self.refinery = refinery

    def adjudicate_block(self, node_id: str) -> Optional[str]:
        """
        Adjudicates an A0_COMPILED block and issues a B_ADJUDICATED node.
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
            print(f"Error: A0 Block {node_id} not found.")
            return None

        node = pydantic_nodes[found_id]
        if node.layer != "A0_COMPILED":
            print(f"Error: Node {node_id} is layer {node.layer}, expected A0_COMPILED.")
            return None

        orig_name = node.name.replace("_COMPILED", "")
        adjudicated_id = f"B_ADJUDICATED::{orig_name}"
        
        if adjudicated_id in pydantic_nodes:
            return adjudicated_id

        # Perform B-Layer adjudication
        # In proto, we simulate this by verifying the compiled_logic block exists and is valid JSON.
        raw_logic = node.properties.get("compiled_logic", "")
        verdict = "REJECT"
        b_reasoning = "Invalid structural logic."
        
        try:
            logic_dict = json.loads(raw_logic)
            if "assertions" in logic_dict and len(logic_dict["assertions"]) >= 2:
                verdict = "ACCEPT"
                b_reasoning = "Logic block structurally sound. Bounding bounds explicitly defined."
            else:
                verdict = "PARK"
                b_reasoning = "Logic block parses but lacks requisite dual bounding."
        except Exception as e:
            verdict = "REJECT"
            b_reasoning = f"Parse failure: {str(e)}"

        from system_v4.skills.v4_graph_builder import GraphNode, GraphEdge
        builder = self.refinery.builder

        builder.add_node(GraphNode(
            id=adjudicated_id,
            node_type="B_OUTCOME",
            name=f"{orig_name}_B_STATUS",
            description=f"Mechanical Adjudication for {orig_name}",
            layer="B_ADJUDICATED",
            trust_zone="B_ADJUDICATED",
            authority="PROTO_SCAFFOLD",
            properties={
                "b_verdict": verdict,
                "b_reasoning": b_reasoning,
                "evidence_tier": "PROTO_SHAPE_ONLY",
                "proto_note": "B gate checks JSON shape + 2 assertions, not substance",
                "proto_runner_version": "v1_deterministic",
            }
        ))
        self.refinery.log_finding(f"B Adjudicated block: {orig_name} -> {verdict}")

        builder.add_edge(GraphEdge(
            source_id=adjudicated_id, target_id=found_id,
            relation="ADJUDICATED_FROM", attributes={}
        ))

        self.refinery._save()
        return adjudicated_id
