import os
from system_v4.skills.a2_persistent_brain import A2PersistentBrain
from system_v4.skills.a1_rosetta_mapper import A1RosettaMapper

def run_context_rotation_demo():
    print("--- [ V4 Context Rotation & Rosetta Test ] ---")
    workspace = os.path.abspath(".")
    
    # Init tools
    brain = A2PersistentBrain(workspace)
    rosetta = A1RosettaMapper(workspace)
    
    print("\n1. Simulating an A2 thread mining high-entropy documents...")
    # Thread 1 starts working
    brain.append_memory_event(
        entry_type="THREAD_BOOT",
        content={"thread_id": "V4_THREAD_001", "goal": "Extract entropy loop terms"},
        tags=["BOOT", "A2"]
    )
    
    # Thread 1 proposes some jargon mappings
    print("2. A2 Thread proposes mappings (Jargon -> Kernel Object)...")
    rosetta.propose_mapping("thermodynamic sink", "S_TERM_ENTROPY_SINK", ["thread_b_archive_1"])
    rosetta.propose_mapping("left engine loop", "S_TERM_DEDUCTIVE_MACRO_LOOP", ["axis_notes_4"])
    
    # A1 acts as judge and activates them
    rosetta.activate_mapping("thermodynamic sink")
    rosetta.activate_mapping("left engine loop")
    
    brain.append_memory_event(
        entry_type="ROSETTA_UPDATE",
        content={"action": "two new terms activated"},
        tags=["ROSETTA", "A1"]
    )
    
    print("3. Validating Rosetta translation bounds...")
    kernel_term = rosetta.get_kernel_translation("left engine loop")
    print(f" > Overlay 'left engine loop' translates safely to Kernel Protocol: {kernel_term}")
    assert kernel_term == "S_TERM_DEDUCTIVE_MACRO_LOOP"
    
    print("\n4. Simulating A2 thread getting 'too hot' (context exhaustion)...")
    print("5. Executing Context Seal...")
    seal = brain.seal_context(
        source_thread_id="V4_THREAD_001",
        pending_actions=["Continue extraction of Axis 6 polarity terms"],
        next_read_set=["path/to/next/doc"],
        state_digest_hash="abcd1234efgh5678"
    )
    
    print(f" > Context Sealed successfully. Issued Seal ID: {seal['seal_id']}")
    print(f" > State Hash fixed at: {seal['state_digest_hash']}")
    
    print("\n6. Simulating a fresh V4_THREAD_002 booting up from the Seal...")
    brain.append_memory_event(
        entry_type="THREAD_BOOT",
        content={
            "thread_id": "V4_THREAD_002", 
            "resuming_from_seal": seal['seal_id'],
            "loaded_pending_actions": seal['pending_actions']
        },
        tags=["BOOT", "A2", "COLD_START"]
    )
    print(" > Fresh thread booted continuously without retaining all classical tokens from original thread.")
    print("--- [ Test Completed ] ---")

if __name__ == "__main__":
    run_context_rotation_demo()
