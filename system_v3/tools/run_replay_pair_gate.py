#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _status(flag: bool) -> str:
    return "PASS" if flag else "FAIL"


def _as_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def _as_hash_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str):
            out.append(item)
        else:
            out.append("")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate deterministic replay pair gate for P4.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--min-cycles", type=int, default=50)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    reports_dir = run_dir / "reports"

    replay_1 = _read_json(reports_dir / "replay_pass_1.json")
    replay_2 = _read_json(reports_dir / "replay_pass_2.json")

    status_1 = str(replay_1.get("status", "")).upper() == "PASS"
    status_2 = str(replay_2.get("status", "")).upper() == "PASS"
    cycle_count_1 = _as_int(replay_1.get("cycle_count"))
    cycle_count_2 = _as_int(replay_2.get("cycle_count"))
    cycle_hashes_1 = _as_hash_list(replay_1.get("cycle_state_hashes"))
    cycle_hashes_2 = _as_hash_list(replay_2.get("cycle_state_hashes"))
    final_state_hash_1 = str(replay_1.get("final_state_hash", ""))
    final_state_hash_2 = str(replay_2.get("final_state_hash", ""))
    event_log_hash_1 = str(replay_1.get("event_log_hash", ""))
    event_log_hash_2 = str(replay_2.get("event_log_hash", ""))

    checks = [
        {
            "check_id": "REPLAY_SCHEMA",
            "status": _status(
                replay_1.get("schema") == "REPLAY_PASS_REPORT_v1"
                and replay_2.get("schema") == "REPLAY_PASS_REPORT_v1"
            ),
            "detail": "both replay reports use schema REPLAY_PASS_REPORT_v1",
        },
        {
            "check_id": "REPLAY_STATUS_PASS",
            "status": _status(status_1 and status_2),
            "detail": f"replay_statuses={[replay_1.get('status', ''), replay_2.get('status', '')]}",
        },
        {
            "check_id": "REPLAY_CYCLE_COUNT_MIN",
            "status": _status(cycle_count_1 >= args.min_cycles and cycle_count_2 >= args.min_cycles),
            "detail": f"counts={[cycle_count_1, cycle_count_2]} min_cycles={args.min_cycles}",
        },
        {
            "check_id": "REPLAY_CYCLE_COUNT_EQUAL",
            "status": _status(cycle_count_1 == cycle_count_2 and cycle_count_1 >= 0),
            "detail": f"counts={[cycle_count_1, cycle_count_2]}",
        },
        {
            "check_id": "REPLAY_CYCLE_HASH_LENGTHS",
            "status": _status(len(cycle_hashes_1) == cycle_count_1 and len(cycle_hashes_2) == cycle_count_2),
            "detail": f"lengths={[len(cycle_hashes_1), len(cycle_hashes_2)]} counts={[cycle_count_1, cycle_count_2]}",
        },
        {
            "check_id": "REPLAY_CYCLE_HASH_SEQUENCE_EQUAL",
            "status": _status(cycle_hashes_1 == cycle_hashes_2 and len(cycle_hashes_1) > 0),
            "detail": f"hash_sequence_length={len(cycle_hashes_1)}",
        },
        {
            "check_id": "REPLAY_FINAL_STATE_HASH_EQUAL",
            "status": _status(
                bool(final_state_hash_1)
                and bool(final_state_hash_2)
                and final_state_hash_1 == final_state_hash_2
            ),
            "detail": "final_state_hash equality check",
        },
        {
            "check_id": "REPLAY_EVENT_LOG_HASH_EQUAL",
            "status": _status(
                bool(event_log_hash_1)
                and bool(event_log_hash_2)
                and event_log_hash_1 == event_log_hash_2
            ),
            "detail": "event_log_hash equality check",
        },
    ]

    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    report = {
        "schema": "REPLAY_PAIR_REPORT_v1",
        "run_id": run_dir.name,
        "status": status,
        "checks": checks,
        "min_cycles": args.min_cycles,
        "pass_ids": [replay_1.get("pass_id", ""), replay_2.get("pass_id", "")],
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }

    out_path = reports_dir / "replay_pair_report.json"
    _write_json(out_path, report)
    print(json.dumps({"status": status, "report_path": str(out_path)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
