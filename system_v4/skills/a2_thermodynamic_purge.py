"""
a2_thermodynamic_purge.py — A2 Waste Channel Skill

Provides the capability to explicitly route failed candidates (high contradiction,
vibe-heavy, failed promotion, or violating A1 boundaries) into the GRAVEYARD layer,
acting as a thermodynamic heat reservoir rather than outright deleting them,
in accordance with Ratchet doctrine.
"""

from typing import Optional

class A2ThermodynamicPurge:
    def __init__(self, refinery):
        self.refinery = refinery

    def purge_concept(
        self,
        node_id: str,
        reason: str,
        violating_anchors: list[str] = None
    ) -> bool:
        """
        Demotes a concept to the GRAVEYARD. Modifies trust_zone, layer,
        and adds explicit REJECTED status to metadata.
        """
        graph = self.refinery.builder.graph
        pydantic_nodes = self.refinery.builder.pydantic_model.nodes
        
        # We allow node_id or exact name lookup
        found_id = None
        if node_id in pydantic_nodes:
            found_id = node_id
        else:
            # try name lookup
            for nid, data in pydantic_nodes.items():
                if data.name == node_id:
                    found_id = nid
                    break
                    
        if not found_id:
            print(f"Error: Node {node_id} not found in pydantic model.")
            return False

        node = pydantic_nodes[found_id]
        
        # Don't purge kernel anchors
        if node.layer in ["A1_STRIPPED", "A1_CARTRIDGE", "A0_COMPILED"]:
            print(f"Warning: Cannot purge a concept that has crossed the A1 boundary: {found_id}")
            return False

        orig_layer = node.layer
        
        # Route to waste
        node.layer = "GRAVEYARD"
        node.trust_zone = "THERMODYNAMIC_WASTE"
        node.properties["purge_reason"] = reason
        node.properties["purge_violating_anchors"] = violating_anchors or []
        node.properties["status"] = "REJECTED"
        
        self.refinery.log_finding(
            f"PURGE: Routed `{node.name}` ({orig_layer}) to GRAVEYARD. Reason: {reason}"
        )

        # Sync nx memory attributes
        if graph.has_node(found_id):
            graph.nodes[found_id]["layer"] = "GRAVEYARD"
            graph.nodes[found_id]["trust_zone"] = "THERMODYNAMIC_WASTE"
            graph.nodes[found_id]["status"] = "REJECTED"
            
        self.refinery._save()
        return True
