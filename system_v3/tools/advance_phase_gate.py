#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple


PHASE_ORDER = [
    "P0_SPEC_LOCK",
    "P1_ARTIFACT_GRAMMAR",
    "P2_B_CONFORMANCE",
    "P3_A0_COMPILER",
    "P4_A1_TO_B_SMOKE",
    "P5_SIM_EVIDENCE_LOOP",
    "P6_LONG_RUN_DISCIPLINE",
    "P7_RELEASE_CANDIDATE",
]


def _read_json(path: Path, fallback: dict | None = None) -> dict:
    if not path.exists():
        return {} if fallback is None else fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _status_is_pass(obj: dict) -> bool:
    return str(obj.get("status", "")).upper() == "PASS"


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


def _phase_eval(run_dir: Path) -> Dict[str, Tuple[bool, str]]:
    reports = run_dir / "reports"
    manifest = _read_json(run_dir / "RUN_MANIFEST_v1.json")
    spec_lock = _read_json(reports / "spec_lock_report.json")
    artifact_grammar = _read_json(reports / "artifact_grammar_report.json")
    conformance = _read_json(reports / "conformance_results.json")
    a0_compile = _read_json(reports / "a0_compile_report.json")
    replay1 = _read_json(reports / "replay_pass_1.json")
    replay2 = _read_json(reports / "replay_pass_2.json")
    replay_pair = _read_json(reports / "replay_pair_report.json")
    evidence = _read_json(reports / "evidence_ingest_report.json")
    graveyard = _read_json(reports / "graveyard_integrity_report.json")
    write_guard = _read_json(reports / "long_run_write_guard_report.json")
    checklist = _read_json(reports / "release_checklist_v1.json")

    p0 = (
        manifest.get("schema") == "RUN_MANIFEST_v1" and _status_is_pass(spec_lock),
        "manifest+spec_lock",
    )
    p1 = (_status_is_pass(artifact_grammar), "artifact_grammar")
    p2 = (
        _status_is_pass(conformance)
        and int(conformance.get("totals", {}).get("mismatch_count", 1)) == 0
        and len(conformance.get("missing_rule_families", [])) == 0,
        "conformance_results",
    )
    p3 = (_status_is_pass(a0_compile), "a0_compile")

    replay_cycle_count_1 = _as_int(replay1.get("cycle_count"))
    replay_cycle_count_2 = _as_int(replay2.get("cycle_count"))
    replay_cycle_hashes_1 = _as_hash_list(replay1.get("cycle_state_hashes"))
    replay_cycle_hashes_2 = _as_hash_list(replay2.get("cycle_state_hashes"))

    replay_final_hash_ok = (
        replay1.get("final_state_hash", "")
        and replay2.get("final_state_hash", "")
        and replay1.get("final_state_hash") == replay2.get("final_state_hash")
        and replay1.get("event_log_hash", "")
        and replay2.get("event_log_hash", "")
        and replay1.get("event_log_hash") == replay2.get("event_log_hash")
    )
    replay_cycle_ok = (
        replay_cycle_count_1 >= 50
        and replay_cycle_count_2 >= 50
        and replay_cycle_count_1 == replay_cycle_count_2
        and len(replay_cycle_hashes_1) == replay_cycle_count_1
        and len(replay_cycle_hashes_2) == replay_cycle_count_2
        and replay_cycle_hashes_1 == replay_cycle_hashes_2
        and len(replay_cycle_hashes_1) > 0
    )
    p4 = (
        _status_is_pass(replay1)
        and _status_is_pass(replay2)
        and _status_is_pass(replay_pair)
        and bool(replay_final_hash_ok)
        and bool(replay_cycle_ok),
        "replay_pair",
    )
    p5 = (_status_is_pass(evidence) and _status_is_pass(graveyard), "evidence+graveyard")
    p6 = (_status_is_pass(write_guard), "write_guard")

    checklist_phase_status = checklist.get("phase_status", {})
    checklist_refs = checklist.get("artifact_refs", [])
    checklist_loop_health_required = bool(checklist.get("loop_health_required", False))
    checklist_loop_health_status = str(checklist.get("loop_health_status", "")).upper()
    checklist_loop_health_allow_warn = bool(checklist.get("loop_health_allow_warn", False))
    loop_health_ok = True
    if checklist_loop_health_required:
        allowed = {"PASS", "WARN"} if checklist_loop_health_allow_warn else {"PASS"}
        loop_health_ok = checklist_loop_health_status in allowed
    p7_ok = (
        bool(checklist_phase_status)
        and all(checklist_phase_status.get(p) == "PASS" for p in PHASE_ORDER[:-1])
        and bool(checklist.get("final_state_hash"))
        and bool(checklist.get("final_event_log_hash"))
        and len(checklist_refs) > 0
        and bool(loop_health_ok)
    )
    p7 = (p7_ok, "release_checklist")

    return {
        "P0_SPEC_LOCK": p0,
        "P1_ARTIFACT_GRAMMAR": p1,
        "P2_B_CONFORMANCE": p2,
        "P3_A0_COMPILER": p3,
        "P4_A1_TO_B_SMOKE": p4,
        "P5_SIM_EVIDENCE_LOOP": p5,
        "P6_LONG_RUN_DISCIPLINE": p6,
        "P7_RELEASE_CANDIDATE": p7,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Advance deterministic phase gate status for a run.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--require-phase", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    phase_eval = _phase_eval(run_dir)

    phase_status = {
        phase: ("PASS" if phase_eval[phase][0] else "PENDING")
        for phase in PHASE_ORDER
    }
    completed: list[str] = []
    for phase in PHASE_ORDER:
        if phase_status[phase] == "PASS":
            completed.append(phase)
        else:
            break
    current_phase = "COMPLETE" if len(completed) == len(PHASE_ORDER) else PHASE_ORDER[len(completed)]

    phase_transition = {
        "schema": "PHASE_TRANSITION_REPORT_v1",
        "run_id": run_dir.name,
        "current_phase": current_phase,
        "completed_phases": completed,
        "phase_gate_status": phase_status,
        "phase_gate_reasons": {k: v[1] for k, v in phase_eval.items()},
        "updated_utc": "UNCHANGED_BY_GATE_EVAL",
    }
    transition_path = run_dir / "reports" / "phase_transition_report.json"
    _write_json(transition_path, phase_transition)

    checklist_path = run_dir / "reports" / "release_checklist_v1.json"
    checklist = _read_json(checklist_path, fallback={"schema": "RELEASE_CHECKLIST_v1", "run_id": run_dir.name})
    checklist["phase_status"] = phase_status
    _write_json(checklist_path, checklist)

    out = {
        "run_id": run_dir.name,
        "current_phase": current_phase,
        "completed_count": len(completed),
        "status": "PASS" if current_phase == "COMPLETE" else "PENDING",
    }
    print(json.dumps(out, sort_keys=True))

    if args.require_phase:
        required = args.require_phase
        if phase_status.get(required) != "PASS":
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
