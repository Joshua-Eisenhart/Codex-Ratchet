#!/usr/bin/env python3
"""
Ingest GPT Pro thread results into the A2 graph refinery.

Reads YAML/markdown results from threads/results/JOB_xxx/,
processes them through the A2 refinery pipeline, and marks
jobs as PROCESSED in the queue.

Usage:
    python3 threads/ingest_results.py              # Process all COMPLETE jobs
    python3 threads/ingest_results.py JOB_003      # Process specific job
    python3 threads/ingest_results.py --dry-run     # Show what would be ingested
"""

import json
import sys
import time
import yaml
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

RESULTS_DIR = REPO_ROOT / "threads" / "results"
JOBS_DIR = REPO_ROOT / "threads" / "jobs"


def utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_yaml_front_matter(path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter from a markdown/yaml file."""
    content = path.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            front = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return front, body
    # Pure YAML file
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            return data, ""
    except yaml.YAMLError:
        pass
    return {}, content


def find_result_files(job_id: str) -> list[Path]:
    """Find all result files for a job."""
    job_dir = RESULTS_DIR / job_id
    if not job_dir.exists():
        return []
    files = []
    for ext in ("*.yaml", "*.yml", "*.md", "*.json"):
        files.extend(job_dir.glob(ext))
    return sorted(files)


def ingest_into_refinery(job_id: str, result_files: list[Path], dry_run: bool = False) -> dict:
    """Ingest result files into the A2 refinery graph."""
    from system_v4.skills.a2_graph_refinery import (
        A2GraphRefinery,
        ExtractionMode,
    )

    if dry_run:
        return {
            "job_id": job_id,
            "files": [str(f) for f in result_files],
            "would_ingest": len(result_files),
            "dry_run": True,
        }

    refinery = A2GraphRefinery(str(REPO_ROOT))
    session_id = refinery.start_session(f"INGEST_{job_id}_{utc_iso()[:10]}")
    
    total_concepts = 0
    total_docs = 0

    for result_file in result_files:
        front, body = load_yaml_front_matter(result_file)
        
        # Skip non-result files
        if front.get("schema") != "THREAD_RESULT_v1" and not front.get("job_id"):
            # Try loading as pure data
            if result_file.suffix in (".yaml", ".yml"):
                try:
                    data = yaml.safe_load(result_file.read_text())
                    if isinstance(data, dict):
                        front = data
                except yaml.YAMLError:
                    continue
        
        # Extract concepts from the result
        concepts = []
        
        # Handle structured concept lists
        if "key_concepts" in front:
            for concept in front["key_concepts"]:
                if isinstance(concept, dict):
                    concepts.append({
                        "name": concept.get("name", "unnamed"),
                        "description": concept.get("definition", concept.get("description", "")),
                        "tags": concept.get("tags", []),
                    })
                elif isinstance(concept, str):
                    concepts.append({
                        "name": concept,
                        "description": "",
                        "tags": [],
                    })

        # Handle findings/gaps from audit reports
        if "findings" in front:
            for finding in front["findings"]:
                if isinstance(finding, dict):
                    concepts.append({
                        "name": f"FINDING: {finding.get('title', 'untitled')}",
                        "description": finding.get("description", str(finding)),
                        "tags": ["audit-finding", f"job:{job_id}"],
                    })

        # Handle mapping results from bridge jobs
        if "mappings" in front:
            for mapping in front["mappings"]:
                if isinstance(mapping, dict):
                    concepts.append({
                        "name": f"BRIDGE: {mapping.get('source', '?')} → {mapping.get('target', '?')}",
                        "description": f"Type: {mapping.get('mapping_type', '?')}, Confidence: {mapping.get('confidence', '?')}",
                        "tags": ["bridge-mapping", f"job:{job_id}"],
                    })

        # If body has content but no structured concepts, treat as raw text ingestion
        if not concepts and body:
            concepts.append({
                "name": f"THREAD_RESULT:{result_file.stem}",
                "description": body[:2000],  # Cap at 2000 chars
                "tags": [f"job:{job_id}", "raw-result"],
            })

        if concepts:
            batch = refinery.process_extracted_simple(
                doc_path=str(result_file),
                concepts=concepts,
            )
            total_concepts += len(concepts)
            total_docs += 1
            refinery.log_finding(f"Ingested {len(concepts)} concepts from {result_file.name}")

    log_path = refinery.end_session()

    return {
        "job_id": job_id,
        "files_processed": total_docs,
        "concepts_ingested": total_concepts,
        "session_log": log_path,
        "dry_run": False,
    }


def main():
    dry_run = "--dry-run" in sys.argv
    specific_job = None
    for arg in sys.argv[1:]:
        if arg.startswith("JOB_"):
            specific_job = arg

    # Find jobs with results
    if specific_job:
        job_ids = [specific_job]
    else:
        job_ids = sorted(d.name for d in RESULTS_DIR.iterdir() if d.is_dir() and d.name.startswith("JOB_"))

    if not job_ids:
        print("No results found to ingest.")
        return

    print(f"{'[DRY RUN] ' if dry_run else ''}Processing {len(job_ids)} job(s)...")
    
    for job_id in job_ids:
        files = find_result_files(job_id)
        if not files:
            print(f"  {job_id}: no result files found, skipping")
            continue
        
        print(f"  {job_id}: {len(files)} result file(s)")
        result = ingest_into_refinery(job_id, files, dry_run=dry_run)
        print(f"    → {result.get('concepts_ingested', 0)} concepts ingested")
        
        if result.get("session_log"):
            print(f"    → Session log: {result['session_log']}")


if __name__ == "__main__":
    main()
