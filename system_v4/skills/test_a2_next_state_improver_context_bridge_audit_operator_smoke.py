"""Smoke test for the next-state improver/context bridge audit operator."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills import run_real_ratchet as rr
from system_v4.skills.a2_next_state_improver_context_bridge_audit_operator import (
    build_a2_next_state_improver_context_bridge_audit_report,
    run_a2_next_state_improver_context_bridge_audit,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        probe_report_path = root / "probe_report.json"
        probe_packet_path = root / "probe_packet.json"
        witness_path = root / "witness.json"
        readiness_path = root / "readiness.json"
        first_target_path = root / "first_target.json"
        second_target_packet_path = root / "second_target_packet.json"

        _write_json(probe_report_path, {"status": "ok"})
        _write_json(
            probe_packet_path,
            {"status": "ok", "allow_improver_follow_on": True, "recommended_next_step": "candidate_next_state_improver_context_bridge"},
        )
        _write_json(readiness_path, {"status": "ok"})
        _write_json(first_target_path, {"proof_completed": True, "target_skill_id": "a2-skill-improver-readiness-operator"})
        _write_json(
            second_target_packet_path,
            {"status": "ok", "allow_second_target_admission": False, "gate_status": "hold_one_proven_target_only"},
        )
        _write_json(
            witness_path,
            [
                {
                    "recorded_at": "2026-03-22T00:56:24Z",
                    "witness": {
                        "kind": "positive",
                        "passed": True,
                        "violations": [],
                        "touched_boundaries": ["stable", "admissible"],
                        "trace": [
                            {
                                "at": "2026-03-22T00:56:24Z",
                                "op": "land_second_target_admission_hold",
                                "before_hash": "aaa",
                                "after_hash": "bbb",
                                "notes": [
                                    "keep skill-improver at one proven target only and do not widen to a second target class",
                                    "record the fail-closed hold result as real maintenance evidence",
                                ],
                            }
                        ],
                    },
                    "tags": {
                        "source": "system",
                        "phase": "POST_ACTION_REPAIR",
                        "topic": "skill_improver_gate",
                        "skill": "a2-skill-improver-second-target-admission-audit-operator",
                    },
                }
            ],
        )

        report, packet = build_a2_next_state_improver_context_bridge_audit_report(
            root,
            {
                "probe_report_path": str(probe_report_path),
                "probe_packet_path": str(probe_packet_path),
                "witness_path": str(witness_path),
                "readiness_report_path": str(readiness_path),
                "first_target_proof_report_path": str(first_target_path),
                "second_target_packet_path": str(second_target_packet_path),
            },
        )
        _assert(report["status"] == "ok", f"unexpected bridge status: {report['status']}")
        _assert(
            report["bridge_status"] == "admissible_as_first_target_context_only",
            f"unexpected bridge status: {report['bridge_status']}",
        )
        _assert(
            report["context_bridge_preview"]["first_proven_target_skill_id"] == "a2-skill-improver-readiness-operator",
            "expected first proven target in preview",
        )
        _assert(packet["allow_context_bridge"] is True, "expected context bridge to be allowed")
        _assert(packet["allow_second_target_context"] is False, "bridge must not allow second target context")

    repo_report, repo_packet = build_a2_next_state_improver_context_bridge_audit_report(REPO_ROOT)
    _assert(repo_report["status"] == "ok", f"unexpected live repo status: {repo_report['status']}")
    _assert(
        repo_report["bridge_status"] == "admissible_as_first_target_context_only",
        f"unexpected live bridge status: {repo_report['bridge_status']}",
    )
    _assert(repo_packet["allow_context_bridge"] is True, "live repo should now allow bounded context bridge")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        probe_report_path = root / "probe_report.json"
        probe_packet_path = root / "probe_packet.json"
        witness_path = root / "witness.json"
        readiness_path = root / "readiness.json"
        first_target_path = root / "first_target.json"
        second_target_packet_path = root / "second_target_packet.json"
        _write_json(probe_report_path, {"status": "ok"})
        _write_json(
            probe_packet_path,
            {"status": "ok", "allow_improver_follow_on": True, "recommended_next_step": "candidate_next_state_improver_context_bridge"},
        )
        _write_json(readiness_path, {"status": "ok"})
        _write_json(first_target_path, {"proof_completed": True, "target_skill_id": "a2-skill-improver-readiness-operator"})
        _write_json(
            second_target_packet_path,
            {"status": "ok", "allow_second_target_admission": False, "gate_status": "hold_one_proven_target_only"},
        )
        _write_json(
            witness_path,
            [
                {
                    "recorded_at": "2026-03-22T00:56:24Z",
                    "witness": {
                        "kind": "negative",
                        "passed": False,
                        "violations": ["STALE_SURFACE"],
                        "touched_boundaries": ["frontier"],
                        "trace": [
                            {
                                "at": "2026-03-22T00:56:24Z",
                                "op": "repair_surface",
                                "before_hash": "aaa",
                                "after_hash": "bbb",
                                "notes": ["replace stale surface and keep the gate fail-closed"],
                            }
                        ],
                    },
                    "tags": {"source": "system", "topic": "graph_audit_sync"},
                }
            ],
        )

        json_path = root / "bridge.json"
        md_path = root / "bridge.md"
        packet_path = root / "bridge.packet.json"
        emitted = run_a2_next_state_improver_context_bridge_audit(
            {
                "repo": str(root),
                "probe_report_path": str(probe_report_path),
                "probe_packet_path": str(probe_packet_path),
                "witness_path": str(witness_path),
                "readiness_report_path": str(readiness_path),
                "first_target_proof_report_path": str(first_target_path),
                "second_target_packet_path": str(second_target_packet_path),
                "report_path": str(json_path),
                "markdown_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "bridge json was not written")
        _assert(md_path.exists(), "bridge markdown was not written")
        _assert(packet_path.exists(), "bridge packet was not written")
        _assert(emitted["bridge_status"] == "admissible_as_first_target_context_only", "unexpected emitted bridge status")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_next_state_improver_context_bridge_audit_operator.py": (
                lambda ctx: "a2-next-state-improver-context-bridge-audit-operator-dispatch"
            ),
        }
    )
    bridge_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["next-state-improver-context-bridge"],
    )
    _assert(
        any(skill.skill_id == "a2-next-state-improver-context-bridge-audit-operator" for skill in bridge_skills),
        "a2-next-state-improver-context-bridge-audit-operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        bridge_skills,
        ["a2-next-state-improver-context-bridge-audit-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-next-state-improver-context-bridge-audit-operator",
        f"unexpected bridge selection: {selected}",
    )
    _assert(not fallback, "bridge operator unexpectedly fell back")
    _assert(dispatch is not None, "bridge dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected bridge reason: {reason}")

    print("PASS: a2 next-state improver context bridge audit operator smoke")


if __name__ == "__main__":
    main()
