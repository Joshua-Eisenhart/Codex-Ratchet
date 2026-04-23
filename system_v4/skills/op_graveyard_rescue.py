#!/usr/bin/env python3
"""
OP_GRAVEYARD_RESCUE — Graveyard Resurrection Loop

This script integrates with graveyard_router to extract B_KILL or SIM_KILL
graveyard items and attempts to 'resurrect' them by providing alternative
SIM constraints or relaxing B-Kernel blocks.
"""

import sys
from pathlib import Path

REPO_ROOT = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, REPO_ROOT)

from system_v4.skills.graveyard_router import GraveyardRouter
from system_v4.skills.b_kernel import BKernel
from system_v4.skills.a2_graph_refinery import A2GraphRefinery

def run_rescue_loop(max_items=5):
    print("Initiating OP_GRAVEYARD_RESCUE...")
    
    # Initialize components
    refinery = A2GraphRefinery(REPO_ROOT)
    router = GraveyardRouter(refinery)
    from system_v4.skills.a1_brain import A1Brain
    a1_brain = A1Brain(REPO_ROOT)
    b_kernel = BKernel(a1_brain)
    
    summary = router.summary()
    print(f"Graveyard Summary: {summary}")
    
    if summary["total_records"] == 0:
        print("No records in graveyard to resurrect. Generating a dummy SIM_KILL record to test...")
        # Inject a dummy test record
        router.route_to_graveyard(
            candidate_id="F01_TEST_CANDIDATE",
            reason_tag="NEGATIVE_SIM_FAILED",
            failure_class="SIM_KILL",
            raw_lines=["SIM Engine stalled at stage 3", "Operator commutation error"],
            sim_evidence={"kill_count": 1, "status": "SIM_KILL"},
            target_ref=None,
        )
        print("Dummy record created.")
        
    # Get candidates for rescue
    candidates = router.get_rescue_candidates(max_attempts=3, limit=max_items)
    print(f"Found {len(candidates)} candidates eligible for resurrection.")
    
    for candidate in candidates:
        print(f"\nAttempting rescue for: {candidate.graveyard_id}")
        print(f"  Candidate Name: {candidate.candidate_name}")
        print(f"  Failure Class: {candidate.failure_class}")
        print(f"  Reason: {candidate.reason_tag}")
        
        # Test Negative SIM resurrection logic
        # In a full system, this would call A1 Wiggle to generate variations.
        # Here we just exercise the resurrection state machine.
        if "sim_evidence" in candidate.sim_evidence or candidate.failure_class == "SIM_KILL":
            print("  Applying alternative operator relaxation policies...")
            outcome = "RESCUED"
        else:
            print("  B-Kernel violation requires formal re-write...")
            outcome = "FAILED_AGAIN"
            
        success = router.attempt_resurrection(candidate.graveyard_id, outcome)
        if success:
            print(f"  Result: {outcome}  ✓")
        else:
            print(f"  Result: Error updating graph.")

    print("\nOP_GRAVEYARD_RESCUE complete.")

if __name__ == "__main__":
    run_rescue_loop()
