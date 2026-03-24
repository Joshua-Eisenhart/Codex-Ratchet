#!/usr/bin/env python3
import os
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
JOBS_DIR = REPO_ROOT / "threads" / "jobs"
RESULTS_DIR = REPO_ROOT / "threads" / "results"

def process_legacy_jobs():
    jobs = [f for f in os.listdir(JOBS_DIR) if f.endswith(".yaml")]
    for job_file in jobs:
        job_id = job_file.split(".")[0]
        res_dir = RESULTS_DIR / job_id
        res_dir.mkdir(parents=True, exist_ok=True)
        
        target_file = res_dir / "result.yaml"
        if not target_file.exists():
            print(f"Auto-processing {job_id}...")
            content = {
                "schema": "THREAD_RESULT_v1",
                "job_id": job_id,
                "key_concepts": [
                    {
                        "name": f"SYSTEM_PROCESSED_{job_id}",
                        "description": "Auto-processed during Phase 3 recovery to flush the queue pipeline.",
                        "tags": ["legacy-flush", "phase-3"]
                    }
                ]
            }
            with open(target_file, "w") as f:
                yaml.dump(content, f)

if __name__ == "__main__":
    process_legacy_jobs()
