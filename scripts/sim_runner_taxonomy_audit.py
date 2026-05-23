#!/usr/bin/env python3
"""Read-only audit of runner-facing sim classes.

This does not execute sims. It maps the corpus onto the runner admission
classes used by `adaptive_controller.py`: classical, nonclassical, bridge,
or unknown. Result `classification` stays separate.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import adaptive_controller


OUT_PATH = adaptive_controller.RESULTS / "sim_runner_taxonomy_audit_results.json"


def exists_safe(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def exact_result_file(path: Path) -> Path | None:
    stem = path.stem
    candidates = [adaptive_controller.RESULTS / f"{stem}_results.json"]
    if stem.startswith("sim_"):
        candidates.append(adaptive_controller.RESULTS / f"{stem[4:]}_results.json")
    for candidate in candidates:
        if exists_safe(candidate):
            return candidate
    return None


def row_for(path: Path) -> dict:
    stem = path.stem
    result_path = exact_result_file(path)
    try:
        source_text = path.read_text()
    except Exception:
        source_text = ""
    runner_class = adaptive_controller.runner_class_for(path, source_text=source_text)
    return {
        "sim": str(path.relative_to(adaptive_controller.ROOT)),
        "stem": stem,
        "runner_class": runner_class,
        "runner_class_reason": adaptive_controller.runner_class_reason(path, source_text=source_text),
        "classification": adaptive_controller._source_classification(source_text),
        "plan_bucket": adaptive_controller.plan_bucket(path.name),
        "plan_stage": adaptive_controller.plan_stage(path.name),
        "result_path": str(result_path.relative_to(adaptive_controller.ROOT)) if result_path else None,
        "queued_lane": adaptive_controller.infer_lane(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    sims = sorted(
        path
        for path in adaptive_controller.PROBES.glob("sim_*.py")
        if path.is_file()
        and " 2" not in path.name
        and path.stem not in adaptive_controller.QUEUE_BLACKLIST
    )
    rows = [row_for(path) for path in sims]
    runner_counts = Counter(row["runner_class"] for row in rows)
    stage_counts = Counter(row["plan_stage"] for row in rows)
    bridge_rows = [row for row in rows if row["runner_class"] == "bridge"]
    unknown_rows = [row for row in rows if row["runner_class"] == "unknown"]
    report = {
        "name": "sim_runner_taxonomy_audit",
        "generated_at": datetime.now().isoformat(),
        "strict": args.strict,
        "summary": {
            "checked": len(rows),
            "runner_class_counts": dict(runner_counts),
            "plan_stage_counts": dict(stage_counts),
            "bridge_count": len(bridge_rows),
            "unknown_count": len(unknown_rows),
            "ok": not args.strict or not unknown_rows,
        },
        "policy": {
            "execution_is_python_runner_only": True,
            "classification_is_not_runner_class": True,
            "runner_classes": ["classical", "nonclassical", "bridge", "unknown"],
        },
        "bridge_samples": bridge_rows[:50],
        "unknown_samples": unknown_rows[:50],
        "rows": rows,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"checked={len(rows)}")
    print(f"runner_class_counts={dict(runner_counts)}")
    print(f"bridge_count={len(bridge_rows)}")
    print(f"unknown_count={len(unknown_rows)}")
    if args.strict and unknown_rows:
        print("SIM RUNNER TAXONOMY AUDIT FAILED")
        return 1
    print("SIM RUNNER TAXONOMY AUDIT PASSED" if not unknown_rows else "SIM RUNNER TAXONOMY AUDIT WARN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
