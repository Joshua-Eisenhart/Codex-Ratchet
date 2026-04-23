"""
a1_rosetta_stripper.py — A1 Rosetta Disentanglement Skill

Transforms A2_LOW_CONTROL or A1_JARGONED concepts (which carry explanatory
or narrative overlays) into A1_ST`RIPPED kernel candidates, explicitly
dropping subjective jargon, narrative smoothing, and vibes.

Follows Spec 75 (A2_MINING_AND_ROSETTA_ARTIFACT_PACKS) and Spec 26 (BOOTPACK_A1_WIGGLE).
"""

import json
from pathlib import Path
from typing import Optional

def generate_rosetta_strip_prompt(concept_name: str, concept_desc: str, tags: list[str]) -> str:
    """
    Generates a prompt for the LLM to strip jargon from a concept.
    """
    return f"""ROSETTA DISENTANGLEMENT PROTOCOL
You are the A1 Rosetta Stripper lane.
Your task is to take a highly refined but narrative-heavy A2 concept and strip it down to a cold A1_STRIPPED kernel candidate.

INPUT CONCEPT:
Name: {concept_name}
Description: {concept_desc}
Tags: {tags}

RULES (Spec 75):
1. KERNEL LANE ONLY: Preserve only B-safe, cold-core, structural anchors.
2. NO OVERLAY: Drop all explanatory, cross-domain, or noncanon vibe words.
3. EXPLICIT ANCHOR: If a concept refers to an undefined term, explicitly mark it as UNVERIFIED.
4. AUTHORITY: The stripped concept launches with CROSS_VALIDATED authority (it was already SOURCE_CLAIM in A2).

OUTPUT FORMAT:
Respond ONLY with a JSON object matching this schema:
{{
  "stripped_name": "UPPER_SNAKE_CASE_KERNEL_NAME",
  "stripped_description": "Strict structural definition. Max 2 sentences. No filler.",
  "dropped_jargon": ["list", "of", "vibe", "words", "removed"],
  "required_anchors": ["list", "of", "other", "kernel", "terms", "depended", "upon"]
}}
"""

class A1RosettaStripper:
    def __init__(self, refinery):
        """
        refinery: instance of A2GraphRefinery
        """
        self.refinery = refinery

    def strip_concept(
        self,
        node_id: str,
        stripped_name: str,
        stripped_desc: str,
        dropped_jargon: list[str],
        required_anchors: list[str]
    ) -> Optional[str]:
        from system_v4.skills.v4_graph_builder import GraphNode, GraphEdge
        builder = self.refinery.builder

        # 1. Update existing node to mark as A1_JARGONED
        if not builder.node_exists(node_id):
            print(f"Error: Node {node_id} not found.")
            return None

        orig_name = builder.get_node(node_id).name
        builder.update_node(node_id, layer="A1_JARGONED", trust_zone="A1_JARGONED")

        # 2. Create the new A1_STRIPPED node
        stripped_id = f"A1_STRIPPED::{stripped_name}"
        if builder.node_exists(stripped_id):
            return stripped_id

        builder.add_node(GraphNode(
            id=stripped_id,
            node_type="REFINED_CONCEPT",
            name=stripped_name,
            description=stripped_desc,
            layer="A1_STRIPPED",
            trust_zone="A1_STRIPPED",
            authority="PROTO_SCAFFOLD",
            properties={
                "dropped_jargon": dropped_jargon,
                "required_anchors": required_anchors
            }
        ))
        self.refinery.log_finding(f"Created A1_STRIPPED node: {stripped_name}")

        # 3. Create edges via canonical API
        builder.add_edge(GraphEdge(
            source_id=stripped_id, target_id=node_id,
            relation="STRIPPED_FROM", attributes={}
        ))
        builder.add_edge(GraphEdge(
            source_id=node_id, target_id=stripped_id,
            relation="ROSETTA_MAP", attributes={}
        ))

        self.refinery.log_finding(
            f"ROSETTA_MAP: `{orig_name}` -> `{stripped_name}` (Dropped: {', '.join(dropped_jargon)})"
        )

        self.refinery._save()
        return stripped_id

if __name__ == "__main__":
    # Smoke test syntax
    pass
