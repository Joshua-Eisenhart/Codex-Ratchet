import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_graph_refinery import A2GraphRefinery
from system_v4.skills.sim_holodeck_engine import SIMHolodeckEngine
from system_v4.skills.v4_graph_builder import GraphNode

def test_holodeck():
    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session("HOLODECK_TERMINAL_TEST_2026")
    print(f"Session started: {sid}")

    # Inject a dummy B_ADJUDICATED node to test the SIM layer
    dummy_id = "B_ADJUDICATED_STATUS::TEST_OP_001"
    refinery.builder.pydantic_model.nodes[dummy_id] = GraphNode(
        id=dummy_id,
        node_type="CONCEPT",
        name="TEST_OP_001_B_STATUS",
        description="Dummy node for holodeck test",
        layer="B_ADJUDICATED",
        trust_zone="CANON_SECURE",
        authority="CANON",
        properties={"b_verdict": "ACCEPT"}
    )
    
    # Run Holodeck
    print("\n--- Running Holodeck Terminal Evaluation ---")
    holodeck = SIMHolodeckEngine(refinery)
    evidenced_id = holodeck.run_simulation(dummy_id, simulation_feed=[1, 4, 9, 16])
    
    if evidenced_id:
        print(f"\nSuccess! Generated node: {evidenced_id}")
        node = refinery.builder.pydantic_model.nodes[evidenced_id]
        print(f"Inductive Variance: {node.properties.get('inductive_variance')}")
        print(f"Deductive Variance: {node.properties.get('deductive_variance')}")
        print(f"\n--- SIM EVIDENCE PACK STRING ---")
        print(node.properties.get('evidence_pack_string'))
    else:
        print("\nFailed to generate evidentiary node.")

if __name__ == "__main__":
    test_holodeck()
