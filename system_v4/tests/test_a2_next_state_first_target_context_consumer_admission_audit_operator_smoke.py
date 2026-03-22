"""Smoke test for the first-target context consumer admission audit operator."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_next_state_first_target_context_consumer_admission_audit_operator import (
    build_a2_next_state_first_target_context_consumer_admission_report,
    run_a2_next_state_first_target_context_consumer_admission_audit,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bridge_report_path = root / "bridge_report.json"
        bridge_packet_path = root / "bridge_packet.json"
        target_selection_packet_path = root / "selection_packet.json"
        first_target_proof_report_path = root / "proof_report.json"
        second_target_packet_path = root / "second_target_packet.json"

        _write_json(
            bridge_report_path,
            {
                "status": "ok",
                "context_bridge_preview": {
                    "selected_witness_indices": [4, 5, 6],
                    "directive_topics": ["skill_improver_gate"],
                    "forbidden_uses": ["second target admission"],
                },
            },
        )
        _write_json(
            bridge_packet_path,
            {"status": "ok", "allow_first_target_context_only": True},
        )
        _write_json(
            target_selection_packet_path,
            {
                "recommended_target_skill_id": "a2-skill-improver-readiness-operator",
                "recommended_target_skill_path": "system_v4/skills/a2_skill_improver_readiness_operator.py",
                "recommended_allowed_targets": ["system_v4/skills/a2_skill_improver_readiness_operator.py"],
            },
        )
        _write_json(
            first_target_proof_report_path,
            {"status": "ok", "proof_completed": True, "target_skill_id": "a2-skill-improver-readiness-operator"},
        )
        _write_json(
            second_target_packet_path,
            {"status": "ok", "retain_general_gate": True, "allow_second_target_admission": False},
        )
        _write_text(
            root / "system_v4/skill_specs/skill-improver-operator/SKILL.md",
            "---\ninputs: [target_skill_path, candidate_code, test_command, context_packet]\n---\n",
        )
        _write_text(
            root / "system_v4/skills/skill_improver_operator.py",
            "def run_skill_improver(ctx):\n    return ctx.get('context_packet')\n",
        )

        report, packet = build_a2_next_state_first_target_context_consumer_admission_report(
            root,
            {
                "bridge_report_path": str(bridge_report_path),
                "bridge_packet_path": str(bridge_packet_path),
                "target_selection_packet_path": str(target_selection_packet_path),
                "first_target_proof_report_path": str(first_target_proof_report_path),
                "second_target_packet_path": str(second_target_packet_path),
            },
        )
        _assert(report["status"] == "ok", f"unexpected status: {report['status']}")
        _assert(
            report["consumer_status"] == "candidate_first_target_context_consumer_admissible",
            f"unexpected consumer status: {report['consumer_status']}",
        )
        _assert(packet["allow_context_consumer"] is True, "expected consumer to be admitted in synthetic case")

    repo_report, repo_packet = build_a2_next_state_first_target_context_consumer_admission_report(REPO_ROOT)
    _assert(repo_report["status"] == "ok", f"unexpected live repo status: {repo_report['status']}")
    _assert(
        repo_report["consumer_status"] == "candidate_first_target_context_consumer_admissible",
        f"unexpected live consumer status: {repo_report['consumer_status']}",
    )
    _assert(repo_packet["allow_context_consumer"] is True, "live repo should admit the explicit first-target context contract")
    _assert(
        repo_report["recommended_next_step"] == "hold_consumer_as_audit_only",
        f"unexpected live next step: {repo_report['recommended_next_step']}",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        bridge_report_path = root / "bridge_report.json"
        bridge_packet_path = root / "bridge_packet.json"
        target_selection_packet_path = root / "selection_packet.json"
        first_target_proof_report_path = root / "proof_report.json"
        second_target_packet_path = root / "second_target_packet.json"
        _write_json(
            bridge_report_path,
            {
                "status": "ok",
                "context_bridge_preview": {
                    "selected_witness_indices": [4, 5, 6],
                    "directive_topics": ["skill_improver_gate"],
                    "forbidden_uses": ["second target admission"],
                },
            },
        )
        _write_json(
            bridge_packet_path,
            {"status": "ok", "allow_first_target_context_only": True},
        )
        _write_json(
            target_selection_packet_path,
            {
                "recommended_target_skill_id": "a2-skill-improver-readiness-operator",
                "recommended_target_skill_path": "system_v4/skills/a2_skill_improver_readiness_operator.py",
                "recommended_allowed_targets": ["system_v4/skills/a2_skill_improver_readiness_operator.py"],
            },
        )
        _write_json(
            first_target_proof_report_path,
            {"status": "ok", "proof_completed": True, "target_skill_id": "a2-skill-improver-readiness-operator"},
        )
        _write_json(
            second_target_packet_path,
            {"status": "ok", "retain_general_gate": True, "allow_second_target_admission": False},
        )
        _write_text(
            root / "system_v4/skill_specs/skill-improver-operator/SKILL.md",
            "---\ninputs: [target_skill_path, candidate_code, test_command, context_packet]\n---\n",
        )
        _write_text(
            root / "system_v4/skills/skill_improver_operator.py",
            "def run_skill_improver(ctx):\n    return ctx.get('context_packet')\n",
        )

        json_path = root / "consumer.json"
        md_path = root / "consumer.md"
        packet_path = root / "consumer.packet.json"
        emitted = run_a2_next_state_first_target_context_consumer_admission_audit(
            {
                "repo": str(root),
                "bridge_report_path": str(bridge_report_path),
                "bridge_packet_path": str(bridge_packet_path),
                "target_selection_packet_path": str(target_selection_packet_path),
                "first_target_proof_report_path": str(first_target_proof_report_path),
                "second_target_packet_path": str(second_target_packet_path),
                "report_path": str(json_path),
                "markdown_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "consumer json was not written")
        _assert(md_path.exists(), "consumer markdown was not written")
        _assert(packet_path.exists(), "consumer packet was not written")
        _assert(
            emitted["consumer_status"] == "candidate_first_target_context_consumer_admissible",
            "unexpected emitted consumer status",
        )

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_next_state_first_target_context_consumer_admission_audit_operator.py": (
                lambda ctx: "a2-next-state-first-target-context-consumer-admission-audit-operator-dispatch"
            ),
        }
    )
    consumer_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["first-target-context-consumer"],
    )
    _assert(
        any(skill.skill_id == "a2-next-state-first-target-context-consumer-admission-audit-operator" for skill in consumer_skills),
        "consumer admission operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        consumer_skills,
        ["a2-next-state-first-target-context-consumer-admission-audit-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-next-state-first-target-context-consumer-admission-audit-operator",
        f"unexpected consumer selection: {selected}",
    )
    _assert(not fallback, "consumer operator unexpectedly fell back")
    _assert(dispatch is not None, "consumer dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected consumer reason: {reason}")

    print("PASS: a2 next-state first-target context consumer admission audit operator smoke")


if __name__ == "__main__":
    main()
