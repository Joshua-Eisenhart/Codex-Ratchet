"""
ratchet_integrator.py — Core Authority Escaler

Takes concepts that have survived the entire pipeline
(A2 -> A1 -> A0 -> B -> SIM) and structurally ratchets them.
This means explicitly marking their graph nodes as RATCHETED authority,
signaling that the system can now trust and build atop them unconditionally.
"""

class RatchetIntegrator:
    def __init__(self, refinery):
        self.refinery = refinery

    def integrate(self, node_id: str) -> bool:
        """
        Escalates a SIM_EVIDENCED node and its entire parent hierarchy
        to RATCHETED authority status.
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
            print(f"Error: SIM node {node_id} not found.")
            return False

        node = pydantic_nodes[found_id]
        if node.layer != "SIM_EVIDENCED":
            print(f"Error: Node {node_id} is layer {node.layer}, expected SIM_EVIDENCED.")
            return False
            
        if node.properties.get("stress_outcome") != "PASS":
            print(f"Error: Cannot ratchet {node_id}; empirical stress test did not explicitly pass.")
            return False

        node.properties["authority"] = "RATCHETED"
        node.trust_zone = "KERNEL_CANDIDATE"
        node.properties["integration_epoch"] = "2026_03_18"
        
        name = node.name.replace("_RATCHET_CANDIDATE", "")
        self.refinery.log_finding(f"RATCHET ACTIVATED: {name} promoted to RATCHETED authority. Concept is now CANON.")
        
        self.refinery._save()
        
        if self.refinery.builder.graph.has_node(found_id):
            self.refinery.builder.graph.nodes[found_id]["authority"] = "RATCHETED"
            self.refinery.builder.graph.nodes[found_id]["trust_zone"] = "KERNEL_CANDIDATE"

        return True
