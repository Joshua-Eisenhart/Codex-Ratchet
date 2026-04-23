"""
run_lower_entropy_intake.py — Lower Entropy Source Batch Intake

Processes the user-identified lower-entropy directories that need 
multiple passes through the refinery alongside the specs and boots:
  1. core_docs/upgrade docs (top-level files, excluding already-processed BOOTPACKS subdir)
  2. core_docs/a1_refined_Ratchet Fuel (axes specs, geometry manifold, physics fuel)
  3. core_docs/v4 upgrades (thread context extracts, design docs)
  4. system_v3/noncanonical_draft_specification_surface (draft spec copies)
  5. system_v3/a2_persistent_context_and_memory_surface/MODEL_CONTEXT.md
  6. system_v3/a2_persistent_context_and_memory_surface/INTENT_SUMMARY.md
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_graph_refinery import A2GraphRefinery, ExtractionMode


def collect_docs(base_dir: Path, recurse: bool = False) -> list[Path]:
    """Collect .md, .txt, .json files from a directory."""
    files = []
    if not base_dir.exists():
        return files
    pattern = "**/*" if recurse else "*"
    for f in sorted(base_dir.glob(pattern)):
        if f.is_file() and f.suffix in (".md", ".txt", ".json") and not f.name.startswith("."):
            files.append(f)
    return files


def run_intake():
    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session("LOWER_ENTROPY_MASSIVE_INTAKE")
    print(f"Session started: {sid}")

    sources = [
        # 1. Upgrade docs (top-level only, skip BOOTPACKS subdir already done)
        (
            "UPGRADE_DOCS",
            [f for f in collect_docs(REPO_ROOT / "core_docs" / "upgrade docs")
             if "BOOTPACKS" not in str(f)],
        ),
        # 2. A1 Refined Ratchet Fuel (axes specs, geometry, physics)
        (
            "A1_REFINED_FUEL",
            collect_docs(REPO_ROOT / "core_docs" / "a1_refined_Ratchet Fuel", recurse=True),
        ),
        # 3. V4 Upgrades (thread context extracts, design docs)
        (
            "V4_UPGRADES",
            collect_docs(REPO_ROOT / "core_docs" / "v4 upgrades"),
        ),
        # 4. Noncanonical Draft Spec Surface
        (
            "NONCANON_DRAFT_SPECS",
            collect_docs(REPO_ROOT / "system_v3" / "noncanonical_draft_specification_surface", recurse=True),
        ),
        # 5+6. Memory surface standalone files
        (
            "A2_MEMORY_SURFACE",
            [
                p for p in [
                    REPO_ROOT / "system_v3" / "a2_persistent_context_and_memory_surface" / "MODEL_CONTEXT.md",
                    REPO_ROOT / "system_v3" / "a2_persistent_context_and_memory_surface" / "INTENT_SUMMARY.md",
                ] if p.exists()
            ],
        ),
    ]

    grand_total = 0
    for batch_id, file_list in sources:
        if not file_list:
            print(f"\n=== {batch_id}: 0 files, skipping ===")
            continue
        print(f"\n=== {batch_id}: {len(file_list)} files ===")
        count = 0
        for doc_path in file_list:
            try:
                refinery.ingest_document(
                    doc_path=str(doc_path),
                    extraction_mode=ExtractionMode.SOURCE_MAP,
                    batch_id=batch_id,
                    concepts=[]
                )
                count += 1
                if count % 10 == 0:
                    print(f"  ... processed {count}/{len(file_list)}")
            except Exception as e:
                print(f"  WARN: Skipped {doc_path.name}: {e}")
        print(f"  Done: {count}/{len(file_list)} registered")
        grand_total += count

    log_path = refinery.end_session()
    n = refinery.builder.pydantic_model.nodes
    e = refinery.builder.pydantic_model.edges

    print(f"\n{'='*60}")
    print(f"LOWER ENTROPY INTAKE COMPLETE")
    print(f"  Total new sources registered: {grand_total}")
    print(f"  Graph Total Nodes:            {len(n)}")
    print(f"  Graph Total Edges:            {len(e)}")
    print(f"  Session Log: {log_path}")
    print(f"{'='*60}")

if __name__ == "__main__":
    run_intake()
