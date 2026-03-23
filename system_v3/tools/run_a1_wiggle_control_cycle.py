#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
AUTORATCHET = SYSTEM_V3 / "runtime" / "bootpack_b_kernel_v1" / "tools" / "autoratchet.py"
A1_AUTORATCHET_CYCLE_AUDIT = SYSTEM_V3 / "tools" / "run_a1_autoratchet_cycle_audit.py"
A1_AUTORATCHET_CONTROLLER_RESULT = SYSTEM_V3 / "tools" / "build_a1_autoratchet_controller_result.py"


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(REPO),
        check=False,
        capture_output=True,
        text=True,
    )


def _require_abs(path_value: str, field: str) -> Path:
    path = Path(str(path_value).strip())
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{field}")
    return path


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _resolve_family_slice_path_or_raise(
    *,
    family_slice_json: str,
    allow_legacy_goal_profile_mode: bool,
) -> Path | None:
    raw = str(family_slice_json).strip()
    if raw:
        return _require_abs(raw, "family_slice_json")
    if bool(allow_legacy_goal_profile_mode):
        return None
    raise SystemExit("family_slice_json_required_unless_allow_legacy_goal_profile_mode")


def _current_steps(run_dir: Path) -> int:
    campaign = _read_json(run_dir / "campaign_summary.json")
    if campaign:
        return int(campaign.get("steps_executed", 0) or 0)
    summary = _read_json(run_dir / "summary.json")
    return int(summary.get("steps_completed", 0) or 0)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run one direct A1 control cycle against the graveyard-first autoratchet runtime, "
            "audit the run, and rewrite the controller result packet."
        )
    )
    parser.add_argument("--dispatch-id", required=True)
    parser.add_argument("--role-type", default="A1_PROPOSAL")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--runs-root", required=True)
    parser.add_argument("--controller-result-json", required=True)
    parser.add_argument("--go-on-budget", type=int, required=True)
    parser.add_argument("--cycles", type=int, default=8)
    parser.add_argument(
        "--family-slice-json",
        default="",
        help="Bounded A2-derived family-slice JSON. This is the expected controller path and should outrank goal-profile policy.",
    )
    parser.add_argument(
        "--allow-legacy-goal-profile-mode",
        action="store_true",
        help="Compatibility override for profile-driven autoratchet control. Without this override, --family-slice-json is required.",
    )
    parser.add_argument("--goal-profile", default="refined_fuel")
    parser.add_argument("--goal-selection", default="interleaved")
    parser.add_argument("--debate-strategy", default="graveyard_first_then_recovery")
    parser.add_argument("--graveyard-fill-steps", type=int, default=8)
    parser.add_argument("--stall-limit-cycles", type=int, default=6)
    parser.add_argument("--max-run-bytes", type=int, default=250000000)
    parser.add_argument("--project-save-every-cycles", type=int, default=5)
    parser.add_argument(
        "--max-cycles-without-progress",
        type=int,
        default=6,
        help="Forwarded to run_a1_wiggle_soak_audit.py.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Start a fresh run. Do not use on continuation cycles.",
    )
    parser.add_argument(
        "--continue-run",
        action="store_true",
        help="Increment go_on_count from the previous controller result when rewriting it.",
    )
    args = parser.parse_args(argv)

    runs_root = _require_abs(args.runs_root, "runs_root")
    controller_result_json = _require_abs(args.controller_result_json, "controller_result_json")
    family_slice_path = _resolve_family_slice_path_or_raise(
        family_slice_json=str(args.family_slice_json),
        allow_legacy_goal_profile_mode=bool(args.allow_legacy_goal_profile_mode),
    )
    run_dir = runs_root / str(args.run_id).strip()
    audit_path = run_dir / "reports" / "a1_autoratchet_cycle_audit_report.json"

    prior_steps = 0 if bool(args.clean) else _current_steps(run_dir)
    target_steps = max(int(args.cycles), int(prior_steps) + int(args.cycles))
    graveyard_fill_steps = min(int(args.graveyard_fill_steps), int(target_steps))

    autoratchet_cmd = [
        "python3",
        str(AUTORATCHET),
        "--run-id",
        str(args.run_id).strip(),
        "--runs-root",
        str(runs_root),
        "--steps",
        str(int(target_steps)),
        "--goal-profile",
        str(args.goal_profile),
        "--goal-selection",
        str(args.goal_selection),
        "--debate-strategy",
        str(args.debate_strategy),
        "--graveyard-fill-steps",
        str(int(graveyard_fill_steps)),
    ]
    if family_slice_path is not None:
        autoratchet_cmd.extend(["--family-slice-json", str(family_slice_path)])
    if bool(args.clean):
        autoratchet_cmd.append("--clean")
    elif prior_steps > 0 or bool(args.continue_run):
        autoratchet_cmd.append("--resume")

    autoratchet_proc = _run(autoratchet_cmd)
    if autoratchet_proc.returncode != 0:
        raise SystemExit(
            "a1_autoratchet_failed\n"
            + (autoratchet_proc.stdout or "")
            + "\n--- STDERR ---\n"
            + (autoratchet_proc.stderr or "")
        )

    audit_cmd = [
        "python3",
        str(A1_AUTORATCHET_CYCLE_AUDIT),
        "--run-dir",
        str(run_dir),
        "--min-graveyard-count",
        "1",
        "--out-json",
        str(audit_path),
    ]
    audit_proc = _run(audit_cmd)
    if audit_proc.returncode not in (0, 2):
        raise SystemExit(
            "a1_autoratchet_cycle_audit_failed_to_run\n"
            + (audit_proc.stdout or "")
            + "\n--- STDERR ---\n"
            + (audit_proc.stderr or "")
        )

    result_cmd = [
        "python3",
        str(A1_AUTORATCHET_CONTROLLER_RESULT),
        "--dispatch-id",
        str(args.dispatch_id).strip(),
        "--role-type",
        str(args.role_type).strip(),
        "--run-dir",
        str(run_dir),
        "--go-on-budget",
        str(int(args.go_on_budget)),
        "--out-json",
        str(controller_result_json),
    ]
    previous_result = _read_json(controller_result_json)
    if previous_result:
        result_cmd.extend(["--previous-result-json", str(controller_result_json)])
    if bool(args.continue_run):
        result_cmd.append("--increment-go-on-count")

    result_proc = _run(result_cmd)
    if result_proc.returncode != 0:
        raise SystemExit(
            "build_a1_autoratchet_controller_result_failed\n"
            + (result_proc.stdout or "")
            + "\n--- STDERR ---\n"
            + (result_proc.stderr or "")
        )

    controller_result = _read_json(controller_result_json)
    payload = {
        "schema": "A1_AUTORATCHET_CONTROL_CYCLE_RESULT_v1",
        "status": "COMPLETED",
        "dispatch_id": str(args.dispatch_id).strip(),
        "run_id": str(args.run_id).strip(),
        "run_dir": str(run_dir),
        "controller_result_json": str(controller_result_json),
        "controller_decision": str(controller_result.get("controller_decision", "") or ""),
        "controller_decision_reason": str(controller_result.get("controller_decision_reason", "") or ""),
        "go_on_count": int(controller_result.get("go_on_count", 0) or 0),
        "go_on_budget": int(controller_result.get("go_on_budget", 0) or 0),
        "go_on_remaining": int(controller_result.get("go_on_remaining", 0) or 0),
        "cycle_audit_report_json": str(audit_path),
        "cycle_audit_status": str(controller_result.get("soak_audit_status", "") or ""),
        "goal_source": str(controller_result.get("goal_source", "") or ""),
        "planning_mode": str(controller_result.get("planning_mode", "") or ""),
        "legacy_goal_profile_mode": bool(controller_result.get("legacy_goal_profile_mode", False)),
        "compatibility_goal_profile": str(controller_result.get("compatibility_goal_profile", "") or ""),
        "legacy_goal_profile_mode_allowed": bool(args.allow_legacy_goal_profile_mode),
        "family_slice_expected": bool(controller_result.get("family_slice_expected", False)),
        "family_slice_json": str(family_slice_path) if family_slice_path is not None else "",
        "target_steps": int(target_steps),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
