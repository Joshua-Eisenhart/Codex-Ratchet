"""
run_megaboot_intake.py — Prime Fuel Ingestion

Ingests the newest MEGABOOT_RATCHET_SUITE and BOOTPACK docs as 
the absolute highest authority constraint structures in the A2 graph.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_graph_refinery import A2GraphRefinery, ExtractionMode

def ingest_megaboots():
    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session("MEGABOOT_V7_INTAKE_001")
    print(f"Session started: {sid}")

    # Paths to the prime fuel
    upgrade_docs_dir = Path(REPO_ROOT) / "core_docs" / "upgrade docs" / "BOOTPACKS"
    
    docs_to_ingest = [
        ("MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md", "v7.4.9 System rules and pipeline architectures"),
        ("BOOTPACK_THREAD_B_v3.9.13.md", "Canon kernel constraints and enforcement fences"),
        ("BOOTPACK_THREAD_A_v2.60.md", "Noncanon Teacher and bridge orchestration rules"),
        ("BOOTPACK_THREAD_SIM_v2.10.md", "Deterministic evidence packaging schemas")
    ]

    for filename, description in docs_to_ingest:
        doc_path = upgrade_docs_dir / filename
        if not doc_path.exists():
            print(f"File missing, skipping: {filename}")
            continue
            
        print(f"\n--- Ingesting: {filename} ---")
        # We perform a MASS_WORK_INTAKE pass to register the source document.
        # Since these are absolute canon, they are tracked as high-authority components.
        refinery.ingest_document(
            doc_path=str(doc_path),
            extraction_mode=ExtractionMode.SOURCE_MAP,
            batch_id=f"MEGABOOT_PRIME_INTAKE_{filename.split('_')[0]}",
            concepts=[]
        )

    log_path = refinery.end_session()
    print(f"\nMegaboot Intake Complete. Log: {log_path}")

    # Print Quick Stats
    from system_v4.skills.a2_graph_refinery import RefineryLayer
    n = refinery.builder.pydantic_model.nodes
    e = refinery.builder.pydantic_model.edges
    print(f"\nGraph Stats:")
    print(f"Total nodes: {len(n)}, Total edges: {len(e)}")
    print(f"  SOURCE_CLAIMS (A2-3 Intake): {refinery.get_layer_node_count(RefineryLayer.A2_3_INTAKE)}")
    print(f"  A2-2 (Verified Extracts): {refinery.get_layer_node_count(RefineryLayer.A2_2_CANDIDATE)}")
    print(f"  KERNEL (A2-1 Definitions): {refinery.get_layer_node_count(RefineryLayer.A2_1_KERNEL)}")

if __name__ == "__main__":
    ingest_megaboots()
