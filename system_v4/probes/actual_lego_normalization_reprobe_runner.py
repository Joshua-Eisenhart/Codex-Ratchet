#!/usr/bin/env python3
"""Run the actual-lego normalization queue as a bounded re-probe wave.

This runner is deliberately narrow:
- input is the current normalization queue;
- each unique reusable probe is run once with the current interpreter;
- outputs are the probes' normal result files plus this ignored run receipt;
- no source labels, admissions, or promotion states are changed.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
QUEUE_PATH = RESULTS_DIR / "actual_lego_normalization_queue.json"
OUT_PATH = RESULTS_DIR / "actual_lego_normalization_reprobe_runner_results.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def unique_probe_rows(queue: dict) -> list[dict]:
    rows = queue.get("rows", [])
    by_probe: dict[str, dict] = {}
    for row in rows:
        probe = row.get("reusable_probe")
        if not probe:
            continue
        by_probe.setdefault(
            probe,
            {
                "probe": probe,
                "lego_ids": [],
                "sections": set(),
                "mapping_confidences": set(),
            },
        )
        by_probe[probe]["lego_ids"].append(row.get("lego_id"))
        by_probe[probe]["sections"].add(row.get("section"))
        by_probe[probe]["mapping_confidences"].add(row.get("mapping_confidence"))
    result = []
    for row in by_probe.values():
        row["sections"] = sorted(value for value in row["sections"] if value)
        row["mapping_confidences"] = sorted(value for value in row["mapping_confidences"] if value)
        result.append(row)
    return sorted(result, key=lambda row: row["probe"])


def run_probe(row: dict, timeout_sec: int) -> dict:
    probe_path = SCRIPT_DIR / row["probe"]
    started = time.monotonic()
    if not probe_path.exists():
        return {
            **row,
            "status": "missing_probe",
            "returncode": None,
            "duration_sec": 0.0,
            "stdout_tail": "",
            "stderr_tail": f"missing probe path: {probe_path}",
        }
    completed = subprocess.run(
        [sys.executable, str(probe_path)],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        timeout=timeout_sec,
        check=False,
    )
    duration = time.monotonic() - started
    stdout_tail = completed.stdout[-4000:]
    stderr_tail = completed.stderr[-4000:]
    return {
        **row,
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "duration_sec": round(duration, 3),
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--timeout-sec", type=int, default=300)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    queue = read_json(QUEUE_PATH)
    rows = unique_probe_rows(queue)
    if args.limit:
        rows = rows[: args.limit]

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(run_probe, row, args.timeout_sec) for row in rows]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            result = results[-1]
            print(f"{result['status']}: {result['probe']} ({result['duration_sec']}s)")

    results.sort(key=lambda row: row["probe"])
    status_counts = Counter(row["status"] for row in results)
    payload = {
        "name": "actual_lego_normalization_reprobe_runner",
        "schema": "actual_lego_normalization_reprobe_runner.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "boundary": "normalization_reprobe_only_not_admission_or_promotion",
        "inputs": {"normalization_queue": str(QUEUE_PATH.relative_to(PROJECT_DIR))},
        "parameters": {
            "python": sys.executable,
            "max_workers": args.max_workers,
            "timeout_sec": args.timeout_sec,
            "limit": args.limit,
        },
        "summary": {
            "unique_probe_count": len(rows),
            "status_counts": dict(sorted(status_counts.items())),
            "failed_count": status_counts.get("failed", 0),
            "missing_probe_count": status_counts.get("missing_probe", 0),
            "promotion_allowed_count": 0,
        },
        "rows": results,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if not status_counts.get("failed") and not status_counts.get("missing_probe") else 1


if __name__ == "__main__":
    raise SystemExit(main())
