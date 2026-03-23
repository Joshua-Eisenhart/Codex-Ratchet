"""Smoke test for the A2 Graph Refinery nested pipeline."""

import os
from system_v4.skills.a2_graph_refinery import (
    A2GraphRefinery,
    ExtractionMode,
    RefineryLayer,
)


def test_refinery_pipeline():
    print("--- [ A2 Graph Refinery Smoke Test ] ---")
    workspace = os.path.abspath(".")
    refinery = A2GraphRefinery(workspace)

    # ── A2-3: Ingest a document ───────────────────────────────────────
    print("\n1. A2-3 Intake: Ingesting a sample source document...")
    batch_a2_3 = refinery.ingest_document(
        doc_path="core_docs/a1_refined_Ratchet Fuel/constraints.md",
        extraction_mode=ExtractionMode.TERM_CONFLICT,
        batch_id="BATCH_V4_SMOKE_001",
        concepts=[
            {
                "name": "entropic_monism",
                "description": "Identity is emergent from constraint compatibility, not primitive.",
                "tags": ["FOUNDATION", "AXIOM"],
            },
            {
                "name": "completed_infinity_ban",
                "description": "Classical completed infinites are prohibited.",
                "tags": ["FENCE", "MATH_CLASS"],
            },
            {
                "name": "dual_szilard_engine",
                "description": "Left/Right engines with structurally unequal loops.",
                "tags": ["ENGINE", "TOPOLOGY"],
            },
        ],
    )
    print(f"   Batch: {batch_a2_3.batch_id}")
    print(f"   Layer: {batch_a2_3.layer.value}")
    print(f"   Nodes created: {len(batch_a2_3.node_ids)}")
    print(f"   A2-3 total: {refinery.get_layer_node_count(RefineryLayer.A2_3_INTAKE)}")

    # ── A2-2: Refine with contradiction ───────────────────────────────
    print("\n2. A2-2 Mid-Refinement: Promoting and preserving contradictions...")
    batch_a2_2 = refinery.promote_to_a2_2(
        source_batch_ids=["BATCH_V4_SMOKE_001"],
        refined_concepts=[
            {
                "name": "identity_emergence_constraint",
                "description": "Unified reduction: identity = constraint compatibility.",
                "source_node_ids": [batch_a2_3.node_ids[1]],  # entropic_monism source
            },
            {
                "name": "engine_chirality_inequality",
                "description": "Left deductive loop != Right inductive loop.",
                "source_node_ids": [batch_a2_3.node_ids[3]],  # dual_szilard source
            },
        ],
        new_batch_id="BATCH_V4_A2MID_SMOKE_001",
        contradictions=[
            (
                batch_a2_3.node_ids[1],  # entropic_monism
                batch_a2_3.node_ids[2],  # completed_infinity_ban
                "Monism implies totality but infinity ban requires finitude.",
            ),
        ],
    )
    print(f"   Batch: {batch_a2_2.batch_id}")
    print(f"   Layer: {batch_a2_2.layer.value}")
    print(f"   Refined nodes: {len(batch_a2_2.node_ids)}")
    print(f"   Contradiction edges: 1")
    print(f"   A2-2 total: {refinery.get_layer_node_count(RefineryLayer.A2_2_CANDIDATE)}")

    # ── A2-1: Kernel promotion ────────────────────────────────────────
    print("\n3. A2-1 Kernel Promotion: Selectively admitting to innermost torus...")
    batch_a2_1 = refinery.promote_to_kernel(
        source_batch_ids=["BATCH_V4_A2MID_SMOKE_001"],
        kernel_concepts=[
            {
                "name": "KERNEL__IDENTITY_EMERGENCE",
                "description": "ADMITTED: Identity is emergent, not primitive.",
                "source_node_ids": [batch_a2_2.node_ids[0]],
            },
        ],
        new_batch_id="BATCH_V4_KERNEL_SMOKE_001",
    )
    print(f"   Batch: {batch_a2_1.batch_id}")
    print(f"   Layer: {batch_a2_1.layer.value}")
    print(f"   Kernel nodes: {len(batch_a2_1.node_ids)}")
    print(f"   A2-1 total: {refinery.get_layer_node_count(RefineryLayer.A2_1_KERNEL)}")

    # ── Summary ───────────────────────────────────────────────────────
    print("\n--- [ Layer Summary ] ---")
    summary = refinery.get_batch_summary()
    for layer, count in summary.items():
        print(f"   {layer}: {count} batch(es)")

    total_nodes = len(refinery.builder.pydantic_model.nodes)
    total_edges = len(refinery.builder.pydantic_model.edges)
    print(f"\n   Total graph: {total_nodes} nodes, {total_edges} edges")
    print("--- [ Test Complete ] ---")


if __name__ == "__main__":
    test_refinery_pipeline()
