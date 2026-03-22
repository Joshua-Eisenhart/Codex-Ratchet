import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_graph_refinery import A2GraphRefinery
from system_v4.skills.a0_compiler import A0Compiler
from system_v4.skills.b_adjudicator import BAdjudicator
from system_v4.skills.sim_holodeck_engine import SIMHolodeckEngine
from system_v4.skills.ratchet_integrator import RatchetIntegrator

def run_pipeline():
    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session("PROTO_HOLODECK_PIPELINE")
    print(f"Session started: {sid}")

    a0 = A0Compiler(refinery)
    b_layer = BAdjudicator(refinery)
    holodeck = SIMHolodeckEngine(refinery)
    integrator = RatchetIntegrator(refinery)

    # Find all A1_CARTRIDGE nodes currently in the graph
    cartridges = []
    for nid, node in refinery.builder.pydantic_model.nodes.items():
        if node.layer == "A1_CARTRIDGE":
            cartridges.append((nid, node.name))
            
    if not cartridges:
        print("No A1_CARTRIDGE nodes found to pipeline.")
        return

    print(f"Found {len(cartridges)} cartridges. Commencing full execution pipeline...")
    
    success_count = 0
    
    for cart_id, cart_name in cartridges:
        print(f"\n--- Processing: {cart_name} ---")
        
        # 1. A0 Compilation
        print(f"  [1] Compiling A0 Block...")
        a0_id = a0.compile_cartridge(cart_id)
        if not a0_id:
            print("  -> FAILED at A0 Compilation")
            continue
            
        # 2. B Adjudication
        print(f"  [2] B-Layer Adjudicating...")
        b_id = b_layer.adjudicate_block(a0_id)
        if not b_id:
            print("  -> FAILED at B Adjudication")
            continue
            
        # Check verdict
        b_node = refinery.builder.pydantic_model.nodes.get(b_id)
        if not b_node or b_node.properties.get("b_verdict") != "ACCEPT":
            print(f"  -> B-VERDICT FAILED/PARKED: {b_node.properties.get('b_reasoning') if b_node else 'Unknown'}")
            continue
            
        # 3. SIM Holodeck Run
        print(f"  [3] Running SIM Holodeck stress simulation (Source: mock_video_frames_v1)...")
        sim_id = holodeck.run_simulation(b_id, simulation_feed="mock_video_frames_v1")
        if not sim_id:
            print("  -> FAILED SIM Empirical Evaluation")
            continue
            
        # 4. Ratchet Integration
        print(f"  [4] Ratchet Integration...")
        success = integrator.integrate(sim_id)
        
        if success:
            print(f"  -> SUCCESS! Authority escalated to RATCHETED.")
            success_count += 1
        else:
            print(f"  -> INTEGRATION FAILED.")

    print(f"\nPipeline complete. {success_count}/{len(cartridges)} concepts successfully reached CANON logic.")
    log_path = refinery.end_session()
    print(f"Log path: {log_path}")

if __name__ == "__main__":
    run_pipeline()
