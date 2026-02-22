#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


BASE_REQUIRED_ARTIFACTS = [
    "reports/spec_lock_report.json",
    "reports/artifact_grammar_report.json",
    "reports/conformance_report.json",
    "reports/a0_compile_report.json",
    "reports/phase_transition_report.json",
    "reports/replay_pass_1.json",
    "reports/replay_pass_2.json",
    "reports/replay_pair_report.json",
    "reports/evidence_ingest_report.json",
    "reports/graveyard_integrity_report.json",
    "reports/long_run_write_guard_report.json",
    "reports/release_checklist_v1.json",
]


def _read_json(path: Path, fallback: dict | None = None) -> dict:
    if not path.exists():
        return {} if fallback is None else fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {} if fallback is None else fallback


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize P7 release-candidate checklist for a run.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--require-loop-health", action="store_true")
    parser.add_argument("--allow-loop-health-warn", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    reports_dir = run_dir / "reports"

    phase_transition = _read_json(reports_dir / "phase_transition_report.json")
    replay_1 = _read_json(reports_dir / "replay_pass_1.json")
    replay_2 = _read_json(reports_dir / "replay_pass_2.json")
    loop_health = _read_json(reports_dir / "loop_health_diagnostic.json")

    phase_status = phase_transition.get("phase_gate_status", {})
    p0_to_p6_ok = all(
        phase_status.get(phase) == "PASS"
        for phase in [
            "P0_SPEC_LOCK",
            "P1_ARTIFACT_GRAMMAR",
            "P2_B_CONFORMANCE",
            "P3_A0_COMPILER",
            "P4_A1_TO_B_SMOKE",
            "P5_SIM_EVIDENCE_LOOP",
            "P6_LONG_RUN_DISCIPLINE",
        ]
    )

    final_state_hash = ""
    final_event_log_hash = ""
    if replay_1.get("status") == "PASS" and replay_2.get("status") == "PASS":
        if (
            replay_1.get("final_state_hash")
            and replay_1.get("final_state_hash") == replay_2.get("final_state_hash")
        ):
            final_state_hash = str(replay_1.get("final_state_hash"))
        if (
            replay_1.get("event_log_hash")
            and replay_1.get("event_log_hash") == replay_2.get("event_log_hash")
        ):
            final_event_log_hash = str(replay_1.get("event_log_hash"))

    loop_health_status = str(loop_health.get("status", "")).upper()
    loop_health_ok = True
    if args.require_loop_health:
        allowed_status = {"PASS", "WARN"} if args.allow_loop_health_warn else {"PASS"}
        loop_health_ok = loop_health_status in allowed_status

    required_artifacts = list(BASE_REQUIRED_ARTIFACTS)
    if args.require_loop_health:
        required_artifacts.append("reports/loop_health_diagnostic.json")

    missing_artifacts: list[str] = []
    artifact_refs: list[dict] = []
    for rel_path in required_artifacts:
        abs_path = run_dir / rel_path
        if not abs_path.exists():
            missing_artifacts.append(rel_path)
            continue
        artifact_refs.append({"path": str(abs_path), "role": "gate_artifact"})

    checklist_path = reports_dir / "release_checklist_v1.json"
    checklist = _read_json(
        checklist_path,
        fallback={
            "schema": "RELEASE_CHECKLIST_v1",
            "run_id": run_dir.name,
            "candidate_id": run_dir.name,
            "waivers": [],
        },
    )
    checklist["schema"] = "RELEASE_CHECKLIST_v1"
    checklist["run_id"] = run_dir.name
    checklist["candidate_id"] = run_dir.name
    checklist["phase_status"] = phase_status
    checklist["final_state_hash"] = final_state_hash
    checklist["final_event_log_hash"] = final_event_log_hash
    checklist["loop_health_required"] = bool(args.require_loop_health)
    checklist["loop_health_status"] = loop_health_status
    checklist["loop_health_allow_warn"] = bool(args.allow_loop_health_warn)
    checklist["artifact_refs"] = artifact_refs
    checklist["approved_utc"] = "UNCHANGED_BY_GATE_EVAL"
    checklist["waivers"] = checklist.get("waivers", [])

    _write_json(checklist_path, checklist)

    status = "PASS" if (
        p0_to_p6_ok
        and len(missing_artifacts) == 0
        and bool(final_state_hash)
        and bool(final_event_log_hash)
        and loop_health_ok
    ) else "FAIL"
    out = {
        "status": status,
        "checklist_path": str(checklist_path),
        "missing_artifacts": missing_artifacts,
        "loop_health_status": loop_health_status,
        "loop_health_required": bool(args.require_loop_health),
    }
    print(json.dumps(out, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
