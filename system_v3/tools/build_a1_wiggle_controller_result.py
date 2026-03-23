#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


FATAL_STOP_REASONS = {
    "PROJECT_SAVE_CHECKPOINT_FAILED",
    "RUN_DIR_BYTES_LIMIT",
    "STALL_LIMIT_REACHED",
}


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


def _normalized_stop_reasons(final_row: dict) -> list[str]:
    reasons: list[str] = []
    primary = str(final_row.get("autopilot_stop_reason", "") or "").strip()
    if primary:
        reasons.append(primary)
    extras = final_row.get("autopilot_stop_reasons", [])
    if isinstance(extras, list):
        for value in extras:
            text = str(value or "").strip()
            if text and text not in reasons:
                reasons.append(text)
    return reasons


def _require_abs(path_value: str, field: str) -> Path:
    path = Path(str(path_value).strip())
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{field}")
    return path


def build_result(
    *,
    dispatch_id: str,
    role_type: str,
    run_dir: Path,
    go_on_budget: int,
    previous_result: dict | None = None,
    increment_go_on_count: bool = False,
) -> dict:
    summary_path = run_dir / "summary.json"
    log_path = run_dir / "logs" / "a1_wiggle_autopilot.000.jsonl"
    audit_path = run_dir / "reports" / "a1_wiggle_soak_audit_report.json"

    summary = _read_json(summary_path)
    rows = _read_jsonl(log_path)
    cycle_rows, final_row = _latest_invocation_window(rows)
    audit_report = _read_json(audit_path)

    previous = previous_result or {}
    previous_go_on_count = int(previous.get("go_on_count", 0) or 0)
    go_on_count = previous_go_on_count + (1 if increment_go_on_count else 0)
    go_on_remaining = max(0, int(go_on_budget) - int(go_on_count))
    stop_reasons = _normalized_stop_reasons(final_row)
    audit_status = str(audit_report.get("status", "") or "").strip()
    cycles_with_progress = int(final_row.get("cycles_with_progress", 0) or 0)
    cycles_without_progress = int(final_row.get("cycles_without_progress", 0) or 0)
    last_cycle = cycle_rows[-1] if cycle_rows else {}

    decision = "MANUAL_REVIEW_REQUIRED"
    decision_reason = "missing_run_surface"
    if go_on_count >= int(go_on_budget):
        decision = "STOP"
        decision_reason = "go_on_budget_exhausted"
    elif not summary or not final_row:
        decision = "MANUAL_REVIEW_REQUIRED"
        decision_reason = "missing_run_surface"
    elif audit_status and audit_status != "PASS":
        decision = "MANUAL_REVIEW_REQUIRED"
        decision_reason = "soak_audit_failed"
    elif any(reason in FATAL_STOP_REASONS for reason in stop_reasons):
        decision = "MANUAL_REVIEW_REQUIRED"
        decision_reason = "fatal_autopilot_stop_reason"
    elif cycles_with_progress > 0 and go_on_remaining > 0:
        decision = "CONTINUE_ONE_BOUNDED_STEP"
        decision_reason = "progress_recorded_and_budget_remaining"
    else:
        decision = "STOP"
        decision_reason = "no_further_bounded_step_recommended"

    controller_message_to_send = "go on" if decision == "CONTINUE_ONE_BOUNDED_STEP" else ""
    latest_project_save_doc = str(last_cycle.get("project_save_doc_path", "") or "")
    latest_project_save_doc_audit = str(last_cycle.get("project_save_doc_audit_path", "") or "")
    return {
        "schema": "A1_WIGGLE_CONTROLLER_RESULT_v1",
        "dispatch_id": str(dispatch_id),
        "role_type": str(role_type),
        "run_dir": str(run_dir),
        "summary_json_path": str(summary_path),
        "autopilot_log_path": str(log_path),
        "soak_audit_report_path": str(audit_path),
        "go_on_count": int(go_on_count),
        "go_on_budget": int(go_on_budget),
        "go_on_remaining": int(go_on_remaining),
        "controller_decision": decision,
        "controller_decision_reason": decision_reason,
        "controller_message_to_send": controller_message_to_send,
        "autopilot_stop_reason": str(final_row.get("autopilot_stop_reason", "") or ""),
        "autopilot_stop_reasons": stop_reasons,
        "cycles_completed": int(final_row.get("cycles_completed", 0) or 0),
        "cycles_with_progress": cycles_with_progress,
        "cycles_without_progress": cycles_without_progress,
        "soak_audit_status": audit_status,
        "latest_checkpoint_status": str(last_cycle.get("checkpoint_status", "") or ""),
        "latest_project_save_doc_path": latest_project_save_doc,
        "latest_project_save_doc_audit_path": latest_project_save_doc_audit,
        "latest_inbox_sequence": int(last_cycle.get("inbox_sequence", 0) or 0),
        "read_paths": [
            str(summary_path),
            str(log_path),
            str(audit_path),
            latest_project_save_doc,
            latest_project_save_doc_audit,
        ],
        "summary_snapshot": summary,
        "latest_autopilot_result": final_row,
        "latest_cycle_snapshot": last_cycle,
        "previous_result_json": str(previous.get("result_json_path", "") or ""),
        "incremented_go_on_count": bool(increment_go_on_count),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Build one controller-readable result packet from an A1 wiggle run directory."
    )
    parser.add_argument("--dispatch-id", required=True)
    parser.add_argument("--role-type", default="A1_PROPOSAL")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--go-on-budget", type=int, required=True)
    parser.add_argument("--previous-result-json", default="")
    parser.add_argument("--increment-go-on-count", action="store_true")
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    run_dir = _require_abs(args.run_dir, "run_dir")
    out_path = _require_abs(args.out_json, "out_json")
    if not run_dir.exists():
        raise SystemExit(f"missing_run_dir:{run_dir}")
    previous_result = {}
    if str(args.previous_result_json).strip():
        previous_path = _require_abs(args.previous_result_json, "previous_result_json")
        previous_result = _read_json(previous_path)
        if not previous_result:
            raise SystemExit(f"invalid_previous_result_json:{previous_path}")

    payload = build_result(
        dispatch_id=str(args.dispatch_id).strip(),
        role_type=str(args.role_type).strip(),
        run_dir=run_dir,
        go_on_budget=int(args.go_on_budget),
        previous_result=previous_result,
        increment_go_on_count=bool(args.increment_go_on_count),
    )
    payload["result_json_path"] = str(out_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"schema": payload["schema"], "status": "CREATED", "out_json": str(out_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
