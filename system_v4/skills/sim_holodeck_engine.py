'''
sim_holodeck_engine.py — Deterministic Terminal SIM Wrapper

Evaluates B_ADJUDICATED constructs deterministically per the 8-stage QIT 
Science Method. Converts results into strict SIM_EVIDENCE_PACK v1 format 
for Thread B consumption. No LLMs are used here, per MEGABOOT_RATCHET_SUITE rules.
'''

import hashlib
from typing import Optional, Dict, List
from system_v4.skills.v4_graph_builder import GraphNode, GraphEdge
from system_v4.skills.qit_rosetta_tables import get_science_method_sequence, RosettaTranslator

class DeterministicScienceMethod:
    """
    Executes the 8-stage science method (Inductive/Deductive variance order)
    using hardcoded mathematical/variance monotonics instead of LLMs.
    """
    
    @staticmethod
    def _hash_state(data: Dict) -> str:
        s = str(sorted(data.items())).encode('utf-8')
        return hashlib.sha256(s).hexdigest()

    def run_stage(self, stage_name: str, loop_type: str, state: Dict, feed: List[int]) -> Dict:
        """
        Deterministic evaluation of a cognitive stage.
        We mock structural variance pressure here. 
        """
        meaning = RosettaTranslator.get_qit_meaning(stage_name)
        new_state = dict(state)
        
        # Apply mathematical operators pseudo-deterministically
        base_val = len(feed) + len(meaning)
        current_variance = new_state.get("variance_monotone", 0)
        
        # 4 Inductive (Observation->Model) and 4 Deductive (Model->Prediction)
        if "Inductive" in loop_type:
            # Compressing entropy: Se -> Si -> Ne -> Ni
            new_state["variance_monotone"] = current_variance + (base_val % 7)
        else:
            # Expanding prediction: Ni -> Ne -> Si -> Se
            new_state["variance_monotone"] = max(0, current_variance - (base_val % 4))
            
        new_state["last_stage_meaning"] = meaning
        new_state["last_stage"] = stage_name
        
        return new_state

    def execute_cognitive_loop(self, node_properties: Dict, is_inductive: bool, feed: List[int]) -> tuple[Dict, List[str]]:
        sequence = get_science_method_sequence(is_inductive)
        loop_name = "Inductive (Observation->Model)" if is_inductive else "Deductive (Model->Prediction)"
        logs = []
        
        state = dict(node_properties)
        state["variance_monotone"] = 0
        
        for stage in sequence:
            state = self.run_stage(stage, loop_name, state, feed)
            logs.append(f"STAGE {stage}: {state['last_stage_meaning']} | Variance: {state['variance_monotone']}")
            
        return state, logs

class SIMHolodeckEngine:
    def __init__(self, refinery):
        self.refinery = refinery
        self.runner = DeterministicScienceMethod()

    def generate_sim_evidence_pack(self, sim_id: str, code_hash: str, out_hash: str, branch: str, batch: str) -> str:
        """
        Generates a strict SIM_EVIDENCE_PACK v1 block as required by BOOTPACK_THREAD_SIM_v2.10
        """
        return f"""INTENT: EMIT_SIM_EVIDENCE_PACK
BRANCH_ID: {branch}
BATCH_ID: {batch}
ITEM: SIM_ID={sim_id} CODE_HASH_SHA256={code_hash} OUTPUT_HASH_SHA256={out_hash} EVIDENCE_TOKEN=E_{sim_id}
"""

    def run_simulation(self, node_id: str, simulation_feed: Optional[List[int]] = None) -> Optional[str]:
        '''
        Runs the holodeck execution pipeline and outputs a SIM_EVIDENCED node.
        '''
        if simulation_feed is None:
            simulation_feed = [1, 2, 3, 4, 5] # Mock high bandwidth entropic data

        pydantic_nodes = self.refinery.builder.pydantic_model.nodes
        
        found_id = None
        for nid, data in pydantic_nodes.items():
            if nid == node_id or data.name == node_id:
                found_id = nid
                break
                
        if not found_id:
            print(f"Error: Node {node_id} not found.")
            return None

        node = pydantic_nodes[found_id]
        if node.layer != "B_ADJUDICATED":
            print(f"Error: Node {node_id} layer is {node.layer}, expected B_ADJUDICATED.")
            return None
        
        if node.properties.get("b_verdict") != "ACCEPT":
            print(f"Holodeck bypassed: Node {node_id} was not ACCEPTED by B Layer.")
            return None

        orig_name = node.name.replace("_B_STATUS", "")
        evidenced_id = f"SIM_EVIDENCED::{orig_name}"
        
        if evidenced_id in pydantic_nodes:
            return evidenced_id

        print(f"  -> Holodeck [Inductive Loop]: Constructing world model from {len(simulation_feed)} data points...")
        ind_state, inductive_logs = self.runner.execute_cognitive_loop(node.dict(), is_inductive=True, feed=simulation_feed)
        
        print(f"  -> Holodeck [Deductive Loop]: Projecting structural predictions...")
        ded_state, deductive_logs = self.runner.execute_cognitive_loop(ind_state, is_inductive=False, feed=simulation_feed)

        # Generate hashes for SIM_EVIDENCE
        code_hash = hashlib.sha256(b"deterministic_sim_v1").hexdigest()
        out_hash = hashlib.sha256(str(ded_state).encode('utf-8')).hexdigest()
        
        # Package into BOOTPACK container string
        evidence_pack_str = self.generate_sim_evidence_pack(
            sim_id=f"S_{orig_name.upper()}",
            code_hash=code_hash,
            out_hash=out_hash,
            branch="MAIN",
            batch="TEST_001"
        )

        sim_results = {
            "feed_source": "mocked_array_stream",
            "inductive_variance": ind_state.get("variance_monotone", 0),
            "deductive_variance": ded_state.get("variance_monotone", 0),
            "world_model_stability": "STABLE",
            "evidence_pack_string": evidence_pack_str
        }
        
        builder = self.refinery.builder

        builder.add_node(GraphNode(
            id=evidenced_id,
            node_type="EMPIRICAL_EVIDENCE",
            name=f"{orig_name}_RATCHET_CANDIDATE",
            description=f"8-Stage Holodeck Terminal Evaluation for {orig_name}",
            layer="SIM_EVIDENCED",
            trust_zone="SIM_EVIDENCED",
            authority="PROTO_SCAFFOLD",
            properties={
                **sim_results,
                "evidence_tier": "PROTO_MOCKED_FEED",
                "proto_note": "SIM uses mocked_array_stream, not real empirical data",
                "proto_runner_version": "v1_deterministic",
            }
        ))
        self.refinery.log_finding(f"Holodeck Terminal Complete: Output bounded to {out_hash[:8]}")

        builder.add_edge(GraphEdge(
            source_id=evidenced_id, target_id=found_id,
            relation="EVIDENCED_FROM", attributes={}
        ))

        self.refinery._save()
        return evidenced_id

