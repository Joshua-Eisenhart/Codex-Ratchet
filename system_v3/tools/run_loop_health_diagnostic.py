#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_event_rows(run_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted((run_dir / "logs").glob("events.*.jsonl")):
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute loop health diagnostics from run event logs.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--no-pending-stall-threshold", type=int, default=5)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    reports_dir = run_dir / "reports"
    rows = _read_event_rows(run_dir)

    event_counts = Counter(row.get("event", "") for row in rows)
    reject_reason_counts = Counter(
        row.get("reason", "UNKNOWN")
        for row in rows
        if row.get("event") == "reject"
    )
    park_reason_counts = Counter(
        row.get("reason", "UNKNOWN")
        for row in rows
        if row.get("event") == "park"
    )
    sim_skip_reason_counts = Counter(
        row.get("reason", "UNKNOWN")
        for row in rows
        if row.get("event") == "sim_skip"
    )

    cycle_count = int(event_counts.get("strategy_generated", 0))
    sim_run_count = int(event_counts.get("sim_run", 0))
    sim_skip_no_pending = int(sim_skip_reason_counts.get("NO_PENDING", 0))
    a1_batch_count = int(event_counts.get("a1_batch", 0))
    accept_count = int(event_counts.get("accept", 0))

    sim_coverage_ratio = (sim_run_count / cycle_count) if cycle_count else 0.0
    stall_no_pending = (
        sim_skip_no_pending >= args.no_pending_stall_threshold
        and a1_batch_count > sim_skip_no_pending
        and accept_count == 0
    )

    top_reject = [{"reason": k, "count": v} for k, v in reject_reason_counts.most_common(10)]
    top_park = [{"reason": k, "count": v} for k, v in park_reason_counts.most_common(10)]

    status = "PASS" if not stall_no_pending else "WARN"
    report = {
        "schema": "LOOP_HEALTH_DIAGNOSTIC_v1",
        "run_id": run_dir.name,
        "status": status,
        "cycle_count": cycle_count,
        "event_counts": dict(sorted(event_counts.items())),
        "sim_run_count": sim_run_count,
        "sim_skip_no_pending_count": sim_skip_no_pending,
        "sim_coverage_ratio": round(sim_coverage_ratio, 6),
        "stall_flags": {
            "stall_no_pending_while_batches_continue": stall_no_pending,
        },
        "top_reject_reasons": top_reject,
        "top_park_reasons": top_park,
        "sim_skip_reasons": dict(sorted(sim_skip_reason_counts.items())),
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }
    out_path = reports_dir / "loop_health_diagnostic.json"
    _write_json(out_path, report)
    print(json.dumps({"status": status, "report_path": str(out_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
