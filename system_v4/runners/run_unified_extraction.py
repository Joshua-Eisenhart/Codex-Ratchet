import sys
import json
from pathlib import Path

if __name__ == "__main__":
    REPO_ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(REPO_ROOT))

    from system_v4.skills.a2_graph_refinery import A2GraphRefinery, ExtractionMode

    # Load ledger
    ledger_path = REPO_ROOT / "system_v4" / "a2_state" / "unified_extraction_ledger.json"
    jobs = json.loads(ledger_path.read_text()) if ledger_path.exists() else []

    refinery = A2GraphRefinery(str(REPO_ROOT))
    sid = refinery.start_session()
    print(f"Started session: {sid}. Loaded {len(jobs)} jobs from ledger.")

    for job in jobs:
        doc_path = job.get("doc_path")
        if not doc_path:
            continue
            
        real_doc_path = REPO_ROOT / "system_v3" / "specs" / Path(doc_path).name
        if not real_doc_path.exists():
            print(f"Skipping missing: {doc_path}")
            continue
            
        mode_val = job.get("extraction_mode", "SOURCE_MAP")
        mode = getattr(ExtractionMode, mode_val, ExtractionMode.SOURCE_MAP)
        
        batch_id = job.get("batch_id", "BATCH_UNIFIED")
        concepts = job.get("concepts", [])
        
        print(f"Ingesting: {doc_path} ({len(concepts)} concepts)")
        refinery.ingest_document(
            doc_path=str(real_doc_path),
            extraction_mode=mode,
            batch_id=batch_id,
            concepts=concepts
        )

    log_path = refinery.end_session()
    print(f"Session ended. Log saved to: {log_path}")
    print(f"Total graph size: {len(refinery.builder.pydantic_model.nodes)} nodes, {len(refinery.builder.pydantic_model.edges)} edges")
