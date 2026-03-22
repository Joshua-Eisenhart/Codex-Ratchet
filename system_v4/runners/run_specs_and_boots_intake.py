"""
run_specs_and_boots_intake.py — Massive Fuel Batch Intake

Processes ALL system_v3/specs documents AND the BOOTPACKS through
the A2 refinery as SOURCE_DOCUMENT registrations. This is the first
pass — registering source nodes. Concept extraction happens in later
passes (A1 branches, LLM extraction, etc).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_graph_refinery import A2GraphRefinery, ExtractionMode

def run_intake():
    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session("SPECS_AND_BOOTS_MASSIVE_INTAKE")
    print(f"Session started: {sid}")

    # ── Source 1: system_v3/specs (85+ docs) ──
    specs_dir = REPO_ROOT / "system_v3" / "specs"
    spec_files = sorted([
        f for f in specs_dir.iterdir()
        if f.suffix in (".md", ".txt", ".json") and not f.name.startswith(".")
    ])

    print(f"\n=== PROCESSING {len(spec_files)} SPEC FILES ===")
    spec_count = 0
    for doc_path in spec_files:
        try:
            refinery.ingest_document(
                doc_path=str(doc_path),
                extraction_mode=ExtractionMode.SOURCE_MAP,
                batch_id=f"SPECS_V3_INTAKE",
                concepts=[]
            )
            spec_count += 1
            if spec_count % 10 == 0:
                print(f"  ... processed {spec_count}/{len(spec_files)} specs")
        except Exception as e:
            print(f"  WARN: Skipped {doc_path.name}: {e}")

    print(f"Specs done: {spec_count}/{len(spec_files)} registered")

    # ── Source 2: BOOTPACKS (the prime fuel) ──
    boots_dir = REPO_ROOT / "core_docs" / "upgrade docs" / "BOOTPACKS"
    boot_files = sorted([
        f for f in boots_dir.iterdir()
        if f.suffix in (".md", ".txt") and not f.name.startswith(".")
    ])

    print(f"\n=== PROCESSING {len(boot_files)} BOOTPACK FILES ===")
    boot_count = 0
    for doc_path in boot_files:
        try:
            refinery.ingest_document(
                doc_path=str(doc_path),
                extraction_mode=ExtractionMode.SOURCE_MAP,
                batch_id=f"BOOTPACK_PRIME_INTAKE",
                concepts=[]
            )
            boot_count += 1
        except Exception as e:
            print(f"  WARN: Skipped {doc_path.name}: {e}")

    print(f"Bootpacks done: {boot_count}/{len(boot_files)} registered")

    # ── Source 3: schemas subdir if present ──
    schemas_dir = specs_dir / "schemas"
    schema_count = 0
    if schemas_dir.exists():
        schema_files = sorted([
            f for f in schemas_dir.iterdir()
            if f.suffix in (".md", ".txt", ".json") and not f.name.startswith(".")
        ])
        print(f"\n=== PROCESSING {len(schema_files)} SCHEMA FILES ===")
        for doc_path in schema_files:
            try:
                refinery.ingest_document(
                    doc_path=str(doc_path),
                    extraction_mode=ExtractionMode.SOURCE_MAP,
                    batch_id=f"SPECS_SCHEMAS_INTAKE",
                    concepts=[]
                )
                schema_count += 1
            except Exception as e:
                print(f"  WARN: Skipped {doc_path.name}: {e}")
        print(f"Schemas done: {schema_count}/{len(schema_files)} registered")

    # ── Source 4: reports subdir if present ──
    reports_dir = specs_dir / "reports"
    report_count = 0
    if reports_dir.exists():
        report_files = sorted([
            f for f in reports_dir.iterdir()
            if f.suffix in (".md", ".txt", ".json") and not f.name.startswith(".")
        ])
        print(f"\n=== PROCESSING {len(report_files)} REPORT FILES ===")
        for doc_path in report_files:
            try:
                refinery.ingest_document(
                    doc_path=str(doc_path),
                    extraction_mode=ExtractionMode.SOURCE_MAP,
                    batch_id=f"SPECS_REPORTS_INTAKE",
                    concepts=[]
                )
                report_count += 1
            except Exception as e:
                print(f"  WARN: Skipped {doc_path.name}: {e}")
        print(f"Reports done: {report_count}/{len(report_files)} registered")

    # ── Final stats ──
    log_path = refinery.end_session()
    n = refinery.builder.pydantic_model.nodes
    e = refinery.builder.pydantic_model.edges

    total = spec_count + boot_count + schema_count + report_count
    print(f"\n{'='*60}")
    print(f"MASSIVE INTAKE COMPLETE")
    print(f"  Specs registered:     {spec_count}")
    print(f"  Bootpacks registered: {boot_count}")
    print(f"  Schemas registered:   {schema_count}")
    print(f"  Reports registered:   {report_count}")
    print(f"  TOTAL NEW SOURCES:    {total}")
    print(f"  Graph Total Nodes:    {len(n)}")
    print(f"  Graph Total Edges:    {len(e)}")
    print(f"  Session Log: {log_path}")
    print(f"{'='*60}")

if __name__ == "__main__":
    run_intake()
