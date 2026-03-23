#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            row = json.loads(text)
        except Exception:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _nonempty_file_count(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    count = 0
    for item in path.rglob("*"):
        if item.is_file() and item.stat().st_size > 0:
            count += 1
    return int(count)


def _latest_invocation_window(rows: list[dict]) -> tuple[list[dict], dict]:
    last_final_index = -1
    for idx in range(len(rows) - 1, -1, -1):
        if str(rows[idx].get("schema", "")) == "A1_WIGGLE_AUTOPILOT_RESULT_v1":
            last_final_index = idx
            break
    if last_final_index < 0:
        return [], {}
    final = rows[last_final_index]
    start = 0
    for idx in range(last_final_index - 1, -1, -1):
        if str(rows[idx].get("schema", "")) == "A1_WIGGLE_AUTOPILOT_RESULT_v1":
            start = idx + 1
            break
    invocation_rows = rows[start : last_final_index + 1]
    cycle_rows = [
        row for row in invocation_rows if str(row.get("schema", "")) == "A1_WIGGLE_AUTOPILOT_CYCLE_v1"
    ]
    return cycle_rows, final


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Audit append-first A1 wiggle soak run surfaces.")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument(
        "--forbid-duplicate-surfaces",
        action="store_true",
        help="Fail if snapshots/, sim/, or a1_strategies/ contain duplicate plaintext artifacts.",
    )
    ap.add_argument(
        "--max-cycles-without-progress",
        type=int,
        default=0,
        help="Optional fail threshold for cycles_without_progress from the autopilot final row. 0 disables.",
    )
    ap.add_argument("--out-json", default="")
    args = ap.parse_args(argv)

    run_dir = Path(args.run_dir).expanduser().resolve()
    summary = _read_json(run_dir / "summary.json")
    log_path = run_dir / "logs" / "a1_wiggle_autopilot.000.jsonl"
    rows = _read_jsonl(log_path)
    cycle_rows, final = _latest_invocation_window(rows)
    final_rows = [row for row in rows if str(row.get("schema", "")) == "A1_WIGGLE_AUTOPILOT_RESULT_v1"]
    final_present = bool(final)

    cycles_completed = int(final.get("cycles_completed", 0) or 0)
    cycles_without_progress = int(final.get("cycles_without_progress", 0) or 0)
    project_save_every_cycles = int(final.get("project_save_every_cycles", 0) or 0)
    checkpoint_pass_count = int(final.get("checkpoint_pass_count", 0) or 0)
    checkpoint_fail_count = int(final.get("checkpoint_fail_count", 0) or 0)
    expected_checkpoint_count = (
        cycles_completed // project_save_every_cycles if project_save_every_cycles > 0 else 0
    )

    duplicate_surface_counts = {
        "snapshots": _nonempty_file_count(run_dir / "snapshots"),
        "sim": _nonempty_file_count(run_dir / "sim"),
        "a1_strategies": _nonempty_file_count(run_dir / "a1_strategies"),
    }
    duplicate_surface_total = sum(duplicate_surface_counts.values())

    checks = [
        {
            "check_id": "WIGGLE_SUMMARY_PRESENT",
            "status": _status(bool(summary)),
            "detail": f"summary_present={bool(summary)}",
        },
        {
            "check_id": "WIGGLE_AUTOPILOT_LOG_PRESENT",
            "status": _status(log_path.exists() and len(rows) >= 1),
            "detail": f"log_path={log_path} row_count={len(rows)}",
        },
        {
            "check_id": "WIGGLE_FINAL_ROW_PRESENT",
            "status": _status(final_present),
            "detail": f"total_final_row_count={len(final_rows)} latest_final_present={final_present}",
        },
        {
            "check_id": "WIGGLE_CYCLE_COUNT_CONSISTENT",
            "status": _status(cycles_completed == len(cycle_rows)),
            "detail": f"cycles_completed={cycles_completed} cycle_row_count={len(cycle_rows)}",
        },
        {
            "check_id": "WIGGLE_APPEND_LOG_TERMINATES_WITH_RESULT",
            "status": _status(bool(rows) and str(rows[-1].get('schema', '')) == "A1_WIGGLE_AUTOPILOT_RESULT_v1"),
            "detail": f"last_schema={str(rows[-1].get('schema', '')) if rows else ''}",
        },
        {
            "check_id": "WIGGLE_PROGRESS_RECORDED",
            "status": _status(cycles_completed > 0 and int(final.get("cycles_with_progress", 0) or 0) >= 1),
            "detail": (
                f"cycles_completed={cycles_completed} "
                f"cycles_with_progress={int(final.get('cycles_with_progress', 0) or 0)}"
            ),
        },
        {
            "check_id": "WIGGLE_CHECKPOINT_CADENCE_CONSISTENT",
            "status": _status(
                project_save_every_cycles == 0
                or expected_checkpoint_count == checkpoint_pass_count + checkpoint_fail_count
            ),
            "detail": (
                f"project_save_every_cycles={project_save_every_cycles} "
                f"expected_checkpoint_count={expected_checkpoint_count} "
                f"observed={checkpoint_pass_count + checkpoint_fail_count}"
            ),
        },
        {
            "check_id": "WIGGLE_CHECKPOINTS_PASS",
            "status": _status(project_save_every_cycles == 0 or checkpoint_fail_count == 0),
            "detail": f"checkpoint_pass_count={checkpoint_pass_count} checkpoint_fail_count={checkpoint_fail_count}",
        },
        {
            "check_id": "WIGGLE_DUPLICATE_SURFACES_EMPTY",
            "status": _status((not bool(args.forbid_duplicate_surfaces)) or duplicate_surface_total == 0),
            "detail": json.dumps(duplicate_surface_counts, sort_keys=True),
        },
    ]
    if int(args.max_cycles_without_progress) > 0:
        checks.append(
            {
                "check_id": "WIGGLE_CYCLES_WITHOUT_PROGRESS_WITHIN_LIMIT",
                "status": _status(cycles_without_progress <= int(args.max_cycles_without_progress)),
                "detail": (
                    f"cycles_without_progress={cycles_without_progress} "
                    f"limit={int(args.max_cycles_without_progress)}"
                ),
            }
        )

    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    report = {
        "schema": "A1_WIGGLE_SOAK_AUDIT_REPORT_v1",
        "status": status,
        "run_dir": str(run_dir),
        "autopilot_log_path": str(log_path),
        "cycles_completed": cycles_completed,
        "cycles_with_progress": int(final.get("cycles_with_progress", 0) or 0),
        "cycles_without_progress": cycles_without_progress,
        "autopilot_stop_reason": str(final.get("autopilot_stop_reason", "") or ""),
        "project_save_every_cycles": project_save_every_cycles,
        "checkpoint_pass_count": checkpoint_pass_count,
        "checkpoint_fail_count": checkpoint_fail_count,
        "duplicate_surface_counts": duplicate_surface_counts,
        "checks": checks,
        "errors": [] if status == "PASS" else ["A1_WIGGLE_SOAK_AUDIT_FAILED"],
    }

    out_path = Path(args.out_json).expanduser().resolve() if str(args.out_json).strip() else (run_dir / "reports" / "a1_wiggle_soak_audit_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "report_path": str(out_path)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
