#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


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
    campaign_path = run_dir / "campaign_summary.json"
    audit_path = run_dir / "reports" / "a1_autoratchet_cycle_audit_report.json"

    summary = _read_json(summary_path)
    campaign_summary = _read_json(campaign_path)
    audit_report = _read_json(audit_path)

    previous = previous_result or {}
    previous_go_on_count = int(previous.get("go_on_count", 0) or 0)
    go_on_count = previous_go_on_count + (1 if increment_go_on_count else 0)
    go_on_remaining = max(0, int(go_on_budget) - int(go_on_count))

    state_metrics = campaign_summary.get("state_metrics", {}) if isinstance(campaign_summary.get("state_metrics", {}), dict) else {}
    audit_status = str(audit_report.get("status", "") or "").strip()
    halt_reason = str(campaign_summary.get("halt_reason", "") or "").strip()
    semantic_gate_status = str((campaign_summary.get("a1_semantic_gate") or {}).get("status", "") or "").strip()
    goal_source = str(campaign_summary.get("goal_source", "") or "").strip()
    planning_mode = str(campaign_summary.get("planning_mode", "") or "").strip()
    legacy_goal_profile_mode = goal_source != "family_slice"
    compatibility_goal_profile = str(campaign_summary.get("compatibility_goal_profile", "") or "").strip()
    family_slice_expected = bool(audit_report.get("family_slice_expected", False))
    family_slice_obligations_status = str(audit_report.get("family_slice_obligations_status", "") or "").strip()
    family_slice_id = str(audit_report.get("family_slice_id", "") or "").strip()
    operator_policy_sources = [
        str(x).strip()
        for x in (audit_report.get("operator_policy_sources", []) or [])
        if str(x).strip()
    ]

    decision = "MANUAL_REVIEW_REQUIRED"
    decision_reason = "missing_run_surface"
    if not summary or not campaign_summary:
        decision = "MANUAL_REVIEW_REQUIRED"
        decision_reason = "missing_run_surface"
    elif audit_status and audit_status != "PASS":
        decision = "MANUAL_REVIEW_REQUIRED"
        decision_reason = "autoratchet_cycle_audit_failed"
    elif legacy_goal_profile_mode:
        decision = "MANUAL_REVIEW_REQUIRED"
        decision_reason = "legacy_goal_profile_mode"
    elif family_slice_expected and family_slice_obligations_status != "PASS":
        decision = "MANUAL_REVIEW_REQUIRED"
        decision_reason = "family_slice_obligations_failed"
    elif go_on_count >= int(go_on_budget):
        decision = "STOP"
        decision_reason = "go_on_budget_exhausted"
    elif halt_reason == "GOALS_COMPLETE":
        decision = "STOP"
        decision_reason = "goals_complete"
    elif semantic_gate_status == "PASS":
        decision = "STOP"
        decision_reason = "semantic_gate_passed"
    elif int(campaign_summary.get("steps_executed", 0) or 0) >= 1 and go_on_remaining > 0:
        decision = "CONTINUE_ONE_BOUNDED_STEP"
        decision_reason = "campaign_progress_and_budget_remaining"
    else:
        decision = "STOP"
        decision_reason = "no_further_bounded_step_recommended"

    return {
        "schema": "A1_AUTORATCHET_CONTROLLER_RESULT_v1",
        "dispatch_id": str(dispatch_id),
        "role_type": str(role_type),
        "run_dir": str(run_dir),
        "summary_json_path": str(summary_path),
        "campaign_summary_json_path": str(campaign_path),
        "autoratchet_cycle_audit_report_path": str(audit_path),
        "go_on_count": int(go_on_count),
        "go_on_budget": int(go_on_budget),
        "go_on_remaining": int(go_on_remaining),
        "controller_decision": decision,
        "controller_decision_reason": decision_reason,
        "controller_message_to_send": "go on" if decision == "CONTINUE_ONE_BOUNDED_STEP" else "",
        "soak_audit_status": audit_status,
        "halt_reason": halt_reason,
        "steps_completed": int(summary.get("steps_completed", 0) or 0),
        "steps_executed": int(campaign_summary.get("steps_executed", 0) or 0),
        "graveyard_count": int(state_metrics.get("killed_unique_count", 0) or 0),
        "sim_registry_count": int(state_metrics.get("sim_registry_count", 0) or 0),
        "canonical_term_count": int(state_metrics.get("canonical_term_count", 0) or 0),
        "a1_semantic_gate_status": semantic_gate_status,
        "goal_source": goal_source,
        "planning_mode": planning_mode,
        "legacy_goal_profile_mode": legacy_goal_profile_mode,
        "compatibility_goal_profile": compatibility_goal_profile,
        "family_slice_expected": family_slice_expected,
        "family_slice_id": family_slice_id,
        "family_slice_obligations_status": family_slice_obligations_status,
        "operator_policy_sources": operator_policy_sources,
        "summary_snapshot": summary,
        "campaign_summary": campaign_summary,
        "audit_report": audit_report,
        "previous_result_json": str(previous.get("result_json_path", "") or ""),
        "incremented_go_on_count": bool(increment_go_on_count),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build one controller-readable result packet from an A1 autoratchet run.")
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
