"""Smoke test for the skill-improver second-target admission audit operator."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_skill_improver_second_target_admission_audit_operator import (
    build_skill_improver_second_target_admission_report,
    run_a2_skill_improver_second_target_admission_audit,
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


def _fake_registry() -> dict[str, dict]:
    return {
        "a2-skill-improver-readiness-operator": {
            "status": "active",
            "skill_type": "maintenance",
            "source_type": "operator_module",
            "source_path": "system_v4/skills/a2_skill_improver_readiness_operator.py",
            "capabilities": {"can_only_propose": True, "is_phase_runner": True},
            "adapters": {"codex": "system_v4/skill_specs/a2-skill-improver-readiness-operator/SKILL.md", "dispatch_binding": "python_module"},
            "tags": ["audit-mode", "truth-maintenance"],
            "related_skills": ["skill-improver-operator"],
        },
        "a2-maintenance-second-candidate-operator": {
            "status": "active",
            "skill_type": "maintenance",
            "source_type": "operator_module",
            "source_path": "system_v4/skills/a2_maintenance_second_candidate_operator.py",
            "capabilities": {"can_only_propose": True, "is_phase_runner": True},
            "adapters": {"codex": "system_v4/skill_specs/a2-maintenance-second-candidate-operator/SKILL.md", "dispatch_binding": "python_module"},
            "tags": ["audit-mode", "truth-maintenance"],
            "related_skills": ["skill-improver-operator"],
        },
        "a2-brain-surface-refresher": {
            "status": "active",
            "skill_type": "maintenance",
            "source_type": "operator_module",
            "source_path": "system_v4/skills/a2_brain_surface_refresher.py",
            "capabilities": {"can_only_propose": True, "is_phase_runner": True},
            "adapters": {"codex": "system_v4/skill_specs/a2-brain-surface-refresher/SKILL.md", "dispatch_binding": "python_module"},
            "tags": ["audit-mode", "truth-maintenance", "surface-refresh", "owner-law"],
            "related_skills": ["skill-improver-operator"],
        },
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write_json(root / "system_v4/a1_state/skill_registry_v1.json", _fake_registry())
        _write_json(root / "system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json", {"target_readiness": "bounded_ready_for_first_target"})
        _write_json(
            root / "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_REPORT__CURRENT__v1.json",
            {"status": "ok", "recommended_target": {"skill_id": "a2-skill-improver-readiness-operator"}},
        )
        _write_json(
            root / "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json",
            {"recommended_target_skill_id": "a2-skill-improver-readiness-operator"},
        )
        _write_json(
            root / "system_v4/a2_state/audit_logs/SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json",
            {"proof_completed": True, "target_skill_id": "a2-skill-improver-readiness-operator"},
        )
        _write_text(root / "system_v4/skills/a2_skill_improver_readiness_operator.py", "def x():\n    return 1\n")
        _write_text(root / "system_v4/skills/test_a2_skill_improver_readiness_operator_smoke.py", "print('ok')\n")
        _write_text(root / "system_v4/skill_specs/a2-skill-improver-readiness-operator/SKILL.md", "# spec\n")
        _write_text(root / "system_v4/skills/a2_maintenance_second_candidate_operator.py", "def x():\n    return 2\n")
        _write_text(root / "system_v4/skills/test_a2_maintenance_second_candidate_operator_smoke.py", "print('ok')\n")
        _write_text(root / "system_v4/skill_specs/a2-maintenance-second-candidate-operator/SKILL.md", "# spec\n")
        _write_text(root / "system_v4/skills/a2_brain_surface_refresher.py", "def x():\n    return 3\n")
        _write_text(root / "system_v4/skills/test_a2_brain_surface_refresher_smoke.py", "print('ok')\n")
        _write_text(root / "system_v4/skill_specs/a2-brain-surface-refresher/SKILL.md", "# spec\n")

        report, packet = build_skill_improver_second_target_admission_report(root)
        _assert(report["status"] == "ok", f"unexpected status: {report['status']}")
        _assert(
            report["gate_status"] == "candidate_second_target_admissible",
            f"unexpected gate status: {report['gate_status']}",
        )
        _assert(
            report["recommended_second_target"]["skill_id"] == "a2-maintenance-second-candidate-operator",
            "expected bounded second candidate to be recommended",
        )
        _assert(packet["allow_second_target_admission"] is True, "expected second target admission to be allowed")
        _assert(packet["do_not_promote"] is True, "expected do_not_promote in packet")

    repo_report, _ = build_skill_improver_second_target_admission_report(REPO_ROOT)
    _assert(repo_report["status"] == "ok", f"unexpected live repo status: {repo_report['status']}")
    _assert(
        repo_report["gate_status"] == "hold_one_proven_target_only",
        f"unexpected live repo gate status: {repo_report['gate_status']}",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _write_json(root / "system_v4/a1_state/skill_registry_v1.json", _fake_registry())
        _write_json(root / "system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json", {"target_readiness": "bounded_ready_for_first_target"})
        _write_json(
            root / "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_REPORT__CURRENT__v1.json",
            {"status": "ok", "recommended_target": {"skill_id": "a2-skill-improver-readiness-operator"}},
        )
        _write_json(
            root / "system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json",
            {"recommended_target_skill_id": "a2-skill-improver-readiness-operator"},
        )
        _write_json(
            root / "system_v4/a2_state/audit_logs/SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json",
            {"proof_completed": True, "target_skill_id": "a2-skill-improver-readiness-operator"},
        )
        _write_text(root / "system_v4/skills/a2_skill_improver_readiness_operator.py", "def x():\n    return 1\n")
        _write_text(root / "system_v4/skills/test_a2_skill_improver_readiness_operator_smoke.py", "print('ok')\n")
        _write_text(root / "system_v4/skill_specs/a2-skill-improver-readiness-operator/SKILL.md", "# spec\n")
        _write_text(root / "system_v4/skills/a2_maintenance_second_candidate_operator.py", "def x():\n    return 2\n")
        _write_text(root / "system_v4/skills/test_a2_maintenance_second_candidate_operator_smoke.py", "print('ok')\n")
        _write_text(root / "system_v4/skill_specs/a2-maintenance-second-candidate-operator/SKILL.md", "# spec\n")
        _write_text(root / "system_v4/skills/a2_brain_surface_refresher.py", "def x():\n    return 3\n")
        _write_text(root / "system_v4/skills/test_a2_brain_surface_refresher_smoke.py", "print('ok')\n")
        _write_text(root / "system_v4/skill_specs/a2-brain-surface-refresher/SKILL.md", "# spec\n")

        json_path = root / "report.json"
        md_path = root / "report.md"
        packet_path = root / "packet.json"
        emitted = run_a2_skill_improver_second_target_admission_audit(
            {
                "repo_root": str(root),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "report json was not written")
        _assert(md_path.exists(), "report markdown was not written")
        _assert(packet_path.exists(), "packet json was not written")
        _assert(emitted["gate_status"] == "candidate_second_target_admissible", "unexpected emitted gate status")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_skill_improver_second_target_admission_audit_operator.py": (
                lambda ctx: "a2-skill-improver-second-target-admission-audit-operator-dispatch"
            ),
        }
    )
    probe_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["second-target-admission"],
    )
    _assert(
        any(skill.skill_id == "a2-skill-improver-second-target-admission-audit-operator" for skill in probe_skills),
        "a2-skill-improver-second-target-admission-audit-operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        probe_skills,
        ["a2-skill-improver-second-target-admission-audit-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-skill-improver-second-target-admission-audit-operator",
        f"unexpected selection: {selected}",
    )
    _assert(not fallback, "unexpected fallback")
    _assert(dispatch is not None, "dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected reason: {reason}")

    repo_packet = json.loads(
        (REPO_ROOT / "system_v4/a2_state/audit_logs/SKILL_IMPROVER_SECOND_TARGET_ADMISSION_PACKET__CURRENT__v1.json").read_text(
            encoding="utf-8"
        )
    )
    _assert(repo_packet["allow_second_target_admission"] is False, "live repo should fail closed")
    _assert(repo_packet["retain_general_gate"] is True, "live repo should retain general gate")

    print("PASS: a2 skill improver second target admission audit operator smoke")


if __name__ == "__main__":
    main()
