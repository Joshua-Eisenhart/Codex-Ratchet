"""
a1_cartridge_assembler.py — A1 Cartridge Envelope Skill

Takes A1_STRIPPED structural candidates and assembles them into
A1_CARTRIDGE packages. Following Spec 26 (BOOTPACK_A1_WIGGLE) and
Spec 27 (BOOTPACK_RATCHET_FUEL_MINT), a cartridge provides:
  - Multi-lane adversarial exploration (STEELMAN, ADVERSARIAL_NEG)
  - Explicit candidate shapes (TERM_DEF, MATH_DEF, SIM_SPEC)
  - Explicit fail/success conditions bounding the extraction
"""

from typing import Optional

def generate_cartridge_assembly_prompt(name: str, desc: str, anchors: list[str]) -> str:
    """
    Generates the prompt for the LLM to wrap an A1_STRIPPED item into an A1_CARTRIDGE.
    """
    return f"""CARTRIDGE ASSEMBLY PROTOCOL
You are the A1 Cartridge Assembler.
Your task is to take a raw A1_STRIPPED kernel candidate and package it as ratchet-ready fuel.

INPUT STRIPPED KERNEL:
Name: {name}
Description: {desc}
Required Anchors: {anchors}

RULES (Specs 26, 27):
1. Forbid hidden assumptions, metric smuggling, and fallback to prose.
2. Require both positive and negative candidates.
3. At least one negative candidate must target implicit time, commutativity, or ontology leakage.

OUTPUT FORMAT:
Respond ONLY with a JSON object matching this schema:
{{
  "candidate_shape": "TERM_DEF", // or MATH_DEF, SIM_SPEC
  "steelman_positive": "Rigorous constructive definition...",
  "adversarial_negative": "Explicit boundary violation definition...",
  "success_condition": "SIM interaction criteria to pass...",
  "fail_condition": "Explicit mode of failure..."
}}
"""

class A1CartridgeAssembler:
    def __init__(self, refinery):
        self.refinery = refinery

    def assemble_cartridge(
        self,
        node_id: str,
        candidate_shape: str,
        steelman_positive: str,
        adversarial_negative: str,
        success_condition: str,
        fail_condition: str
    ) -> Optional[str]:
        """
        Creates an A1_CARTRIDGE node spanning an A1_STRIPPED concept.
        """
        from system_v4.skills.v4_graph_builder import GraphNode, GraphEdge
        builder = self.refinery.builder

        if not builder.node_exists(node_id):
            print(f"Error: A1_STRIPPED node {node_id} not found.")
            return None

        orig_name = builder.get_node(node_id).name

        cartridge_id = f"A1_CARTRIDGE::{orig_name}"
        if builder.node_exists(cartridge_id):
            return cartridge_id

        builder.add_node(GraphNode(
            id=cartridge_id,
            node_type="CARTRIDGE_PACKAGE",
            name=f"{orig_name}_CARTRIDGE",
            description=f"Multi-lane adversarial examination envelope for {orig_name}",
            layer="A1_CARTRIDGE",
            trust_zone="A1_CARTRIDGE",
            authority="PROTO_SCAFFOLD",
            properties={
                "candidate_shape": candidate_shape,
                "steelman_positive": steelman_positive,
                "adversarial_negative": adversarial_negative,
                "success_condition": success_condition,
                "fail_condition": fail_condition
            }
        ))
        self.refinery.log_finding(f"Assembled A1_CARTRIDGE envelope for: {orig_name}")

        builder.add_edge(GraphEdge(
            source_id=cartridge_id, target_id=node_id,
            relation="PACKAGED_FROM", attributes={}
        ))

        self.refinery._save()
        return cartridge_id
