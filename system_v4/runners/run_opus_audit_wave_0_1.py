"""
Opus Audit — Wave 0-1 Promotions & Corrections

Executes the A2-2 promotions recommended by the Opus audit,
adds missed contradiction edges, and fixes the retrocausal description.
"""

import sys
from pathlib import Path


if __name__ == "__main__":
    REPO_ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(REPO_ROOT))

    from system_v4.skills.a2_graph_refinery import A2GraphRefinery, ExtractionMode

    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session("OPUS_AUDIT_SESSION_001")
    print(f"Started audit session: {sid}")

    # ── 1. Promote 6 concepts to A2-2 ────────────────────────────────────

    print("\n--- A2-2 Promotions ---")
    batch = refinery.promote_to_a2_2(
        source_batch_ids=[
            "BATCH_V4_SOURCE_MAP_THREAD_EXTRACT_MAX_001",
            "BATCH_V4_SOURCE_MAP_MEGABOOT_001",
            "BATCH_V4_SOURCE_MAP_29_THING_001",
            "BATCH_V4_SOURCE_MAP_GROK_TOE_001",
        ],
        refined_concepts=[
            {
                "name": "NONCLASSICAL_IMPERATIVE",
                "description": "All structure must be expressed in pure nonclassical terms. No classical semantics may survive underneath, even temporarily. This is the system's hardest constraint, referenced across every source document.",
                "source_node_ids": [
                    "A2_3::SOURCE_MAP_PASS::pure_nonclassical_retooling::8a4a92e24b6cbfaa",
                    "A2_3::SOURCE_MAP_PASS::nonclassical_state_space::fbfc0677982d4428",
                ],
            },
            {
                "name": "ELIMINATION_EPISTEMOLOGY",
                "description": "The system does not stamp 'Truth'. Constraints eliminate. Survivors are pressure-shaped by attractor basins. This governs ratchet behavior: terms survive by not being killed, not by being proven.",
                "source_node_ids": [
                    "A2_3::SOURCE_MAP_PASS::elimination_over_truth::b94861380d72d5ba",
                ],
            },
            {
                "name": "THREAD_B_EXECUTION_LOOP",
                "description": "The singular ratchet mechanism: B_Kernel + SIM constraints enforce Accept→Park→Reject→Kill on proposed terms. This is the only path from PROPOSAL_ONLY to CANONICAL_ALLOWED. Both structural and evidence ladders must advance together.",
                "source_node_ids": [
                    "A2_3::SOURCE_MAP_PASS::unitary_thread_b_ratchet::b81707ea8c50bb04",
                    "A2_3::SOURCE_MAP_PASS::evidence_ladder_sims::4828333df471f578",
                ],
            },
            {
                "name": "STRUCTURED_NONCLASSICAL_STATE",
                "description": "Runtime state carries region, phase, loop scale, boundaries, and invariants. Transform order is non-commutative. Equivalence is probe-relative, not primitive. This bridges the physics model to computation.",
                "source_node_ids": [
                    "A2_3::SOURCE_MAP_PASS::nonclassical_state_space::fbfc0677982d4428",
                    "A2_3::SOURCE_MAP_PASS::hopf_fibration_as_design_lens::4a874d9cc84ec0a0",
                ],
            },
            {
                "name": "FINITUDE_BAN",
                "description": "Completed infinity is prohibited. Universes are bounded (Bekenstein-limited), numbers are finite, and all state operations terminate. This is load-bearing for the entire framework.",
                "source_node_ids": [
                    "A2_3::SOURCE_MAP_PASS::finite_universe_compressibility::71ef60b58bfaa3d3",
                ],
            },
            {
                "name": "FOUR_LAYER_TRUST_SEPARATION",
                "description": "Strict A2→A1→A0→B layering. Context flows down; verified evidence flows up. Each layer has its own trust zone. No layer may write to a layer it does not own.",
                "source_node_ids": [
                    "A2_3::SOURCE_MAP_PASS::four_layer_trust_architecture::6e360f1b17c4343c",
                ],
            },
        ],
        new_batch_id="OPUS_AUDIT_A2_2_PROMOTION_001",
        contradictions=[
            # Contradiction 1: retrocausal says "infinite branches" but finitude bans infinity
            (
                "A2_3::SOURCE_MAP_PASS::retrocausal_multiverse_genesis::1659d7f485a7030c",
                "A2_3::SOURCE_MAP_PASS::finite_universe_compressibility::71ef60b58bfaa3d3",
                "Retrocausal concept says 'Infinite branches' but finitude concept explicitly prohibits completed infinity. Description error in retrocausal node.",
            ),
        ],
    )
    print(f"  Promoted {len(batch.node_ids)} concepts to A2-2")
    print(f"  Added 1 CONTRADICTS edge")

    # ── 2. Add jargon warning to retrocausal node ────────────────────────

    refinery.warn_jargon(
        "BATCH_V4_SOURCE_MAP_GROK_TOE_001",
        "retrocausal_multiverse_genesis description says 'Infinite branches' — violates the system's completed_infinity_ban. Should say 'finite set of possible futures'.",
    )
    print("  Added jargon warning to GROK_TOE batch")

    # ── 3. Log findings ──────────────────────────────────────────────────

    refinery.log_finding("6 concepts promoted to A2-2 from 4 source batches")
    refinery.log_finding("1 contradiction flagged: retrocausal 'infinite' vs finitude ban")
    refinery.log_finding("11 concepts held at A2-3 pending further evidence")
    refinery.log_finding("0 concepts promoted to A2-1 kernel (too early)")

    # ── 4. End session ───────────────────────────────────────────────────

    log_path = refinery.end_session()
    print(f"\nAudit session complete. Log: {log_path}")
    print(f"Total graph: {len(refinery.builder.pydantic_model.nodes)} nodes, {len(refinery.builder.pydantic_model.edges)} edges")

    from system_v4.skills.a2_graph_refinery import RefineryLayer
    print(f"  A2-3: {refinery.get_layer_node_count(RefineryLayer.A2_3_INTAKE)} nodes")
    print(f"  A2-2: {refinery.get_layer_node_count(RefineryLayer.A2_2_CANDIDATE)} nodes")
    print(f"  A2-1: {refinery.get_layer_node_count(RefineryLayer.A2_1_KERNEL)} nodes")
