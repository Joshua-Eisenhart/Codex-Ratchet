"""Smoke test for the next-state first-target context consumer proof operator."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_next_state_first_target_context_consumer_proof_operator import (
    build_a2_next_state_first_target_context_consumer_proof_report,
    run_a2_next_state_first_target_context_consumer_proof,
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
        target_skill_path = root / "system_v4/skills/a2_skill_improver_readiness_operator.py"
        target_skill_path.parent.mkdir(parents=True, exist_ok=True)
        target_skill_path.write_text("VALUE = 1\n", encoding="utf-8")

        smoke_path = root / "system_v4/skills/test_a2_skill_improver_readiness_operator_smoke.py"
        _write_text(
            smoke_path,
            "from pathlib import Path\n"
            "import sys\n"
            "target = Path(__file__).with_name('a2_skill_improver_readiness_operator.py')\n"
            "code = target.read_text(encoding='utf-8')\n"
            "sys.exit(0 if 'VALUE = 1' in code else 1)\n",
        )

        consumer_report_path = root / "consumer_report.json"
        consumer_packet_path = root / "consumer_packet.json"
        bridge_report_path = root / "bridge_report.json"
        bridge_packet_path = root / "bridge_packet.json"
        target_selection_packet_path = root / "target_selection_packet.json"
        first_target_proof_report_path = root / "first_target_proof_report.json"

        _write_json(
            consumer_report_path,
            {
                "status": "ok",
                "proposed_consumer_packet_preview": {
                    "directive_topics": ["skill_improver_gate"],
                    "selected_witness_indices": [1, 2],
                    "forbidden_uses": ["second target admission"],
                },
            },
        )
        _write_json(
            consumer_packet_path,
            {
                "status": "ok",
                "allow_context_consumer": True,
                "retain_general_gate": True,
            },
        )
        _write_json(
            bridge_report_path,
            {
                "status": "ok",
                "context_bridge_preview": {
                    "allowed_context_uses": ["metadata-only maintenance context"],
                    "directive_topics": ["skill_improver_gate"],
                    "selected_witness_indices": [1, 2],
                },
            },
        )
        _write_json(
            bridge_packet_path,
            {
                "status": "ok",
                "allow_context_bridge": True,
                "retained_second_target_gate": "hold_one_proven_target_only",
            },
        )
        _write_json(
            target_selection_packet_path,
            {
                "recommended_target_skill_id": "a2-skill-improver-readiness-operator",
                "recommended_target_skill_path": "system_v4/skills/a2_skill_improver_readiness_operator.py",
                "recommended_target_smoke_path": "system_v4/skills/test_a2_skill_improver_readiness_operator_smoke.py",
                "recommended_allowed_targets": ["system_v4/skills/a2_skill_improver_readiness_operator.py"],
                "recommended_test_command": ["python3", "system_v4/skills/test_a2_skill_improver_readiness_operator_smoke.py"],
            },
        )
        _write_json(
            first_target_proof_report_path,
            {
                "status": "ok",
                "proof_completed": True,
                "target_skill_id": "a2-skill-improver-readiness-operator",
            },
        )

        report, packet = build_a2_next_state_first_target_context_consumer_proof_report(
            root,
            {
                "consumer_report_path": str(consumer_report_path),
                "consumer_packet_path": str(consumer_packet_path),
                "bridge_report_path": str(bridge_report_path),
                "bridge_packet_path": str(bridge_packet_path),
                "target_selection_packet_path": str(target_selection_packet_path),
                "first_target_proof_report_path": str(first_target_proof_report_path),
            },
        )
        _assert(report["status"] == "ok", f"unexpected synthetic status: {report['status']}")
        _assert(report["proof_completed"] is True, "synthetic proof should complete")
        _assert(
            report["skill_improver_result"]["context_contract_status"] == "metadata_only_context_loaded",
            "synthetic proof did not load metadata-only context",
        )
        _assert(report["skill_improver_result"]["write_permitted"] is False, "synthetic proof widened writes")
        _assert(packet["allow_metadata_only_context_consumer_proof"] is True, "synthetic packet should admit proof")

    repo_report, repo_packet = build_a2_next_state_first_target_context_consumer_proof_report(REPO_ROOT)
    _assert(repo_report["status"] == "ok", f"unexpected live repo status: {repo_report['status']}")
    _assert(repo_report["proof_completed"] is True, "live proof should complete")
    _assert(
        repo_report["skill_improver_result"]["context_contract_status"] == "metadata_only_context_loaded",
        "live proof did not load metadata-only context",
    )
    _assert(repo_report["skill_improver_result"]["write_permitted"] is False, "live proof widened writes")
    _assert(
        repo_report["recommended_next_step"] == "hold_consumer_proof_as_metadata_only",
        f"unexpected live next step: {repo_report['recommended_next_step']}",
    )
    _assert(repo_packet["allow_metadata_only_context_consumer_proof"] is True, "live packet should admit proof")

    with tempfile.TemporaryDirectory() as tmpdir:
        report_json = Path(tmpdir) / "proof.json"
        report_md = Path(tmpdir) / "proof.md"
        packet_json = Path(tmpdir) / "proof.packet.json"
        emitted = run_a2_next_state_first_target_context_consumer_proof(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(report_json),
                "report_md_path": str(report_md),
                "packet_path": str(packet_json),
            }
        )
        _assert(report_json.exists(), "proof json missing")
        _assert(report_md.exists(), "proof markdown missing")
        _assert(packet_json.exists(), "proof packet missing")
        _assert(emitted["proof_completed"] is True, "emitted proof should complete")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_next_state_first_target_context_consumer_proof_operator.py": (
                lambda ctx: "a2-next-state-first-target-context-consumer-proof-operator-dispatch"
            ),
        }
    )
    proof_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["next-state-context-consumer-proof"],
    )
    _assert(
        any(skill.skill_id == "a2-next-state-first-target-context-consumer-proof-operator" for skill in proof_skills),
        "proof operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        proof_skills,
        ["a2-next-state-first-target-context-consumer-proof-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-next-state-first-target-context-consumer-proof-operator",
        f"unexpected proof selection: {selected}",
    )
    _assert(not fallback, "proof operator unexpectedly fell back")
    _assert(dispatch is not None, "proof dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected proof reason: {reason}")

    print("PASS: a2 next-state first-target context consumer proof operator smoke")


if __name__ == "__main__":
    main()
