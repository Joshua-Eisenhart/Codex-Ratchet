"""Smoke test for the append-safe context shell audit operator."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills import run_real_ratchet as rr
from system_v4.skills.a2_append_safe_context_shell_audit_operator import (
    build_a2_append_safe_context_shell_audit_report,
    run_a2_append_safe_context_shell_audit,
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

        for rel_path in (
            "work/reference_repos/external_audit/Context-Engineering/README.md",
            "work/reference_repos/external_audit/spec-kit/README.md",
            "work/reference_repos/external_audit/superpowers/README.md",
            "work/reference_repos/external_audit/mem0/README.md",
        ):
            _write_text(root / rel_path, f"{rel_path}\n")

        _write_json(
            root / "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.json",
            {
                "selected_pattern_id": "append_safe_context_shell",
                "recommended_next_slice_id": "a2-append-safe-context-shell-audit-operator",
                "selection_options": [
                    {"pattern_id": "append_safe_context_shell", "status": "selected"},
                    {"pattern_id": "scoped_memory_sidecar", "status": "blocked"},
                ],
            },
        )
        _write_json(
            root / "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_REPORT__CURRENT__v1.json",
            {
                "admissible_pattern_families": [
                    {"pattern_id": "append_safe_context_shell"},
                    {"pattern_id": "executable_spec_coupling"},
                ]
            },
        )

        for rel_path in (
            "system_v3/a2_state/INTENT_SUMMARY.md",
            "system_v3/a2_state/A2_BRAIN_SLICE__v1.md",
            "system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md",
            "system_v3/a2_state/OPEN_UNRESOLVED__v1.md",
            "system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md",
        ):
            _write_text(root / rel_path, f"# {Path(rel_path).name}\n\nsynthetic content\n")

        report, packet = build_a2_append_safe_context_shell_audit_report(root)
        _assert(report["status"] == "ok", f"unexpected synthetic status: {report['status']}")
        _assert(
            report["selector_alignment"]["aligned"] is True,
            "selector alignment should be true in synthetic case",
        )
        _assert(
            report["recommended_next_step"] == "hold_append_safe_context_shell_as_audit_only",
            f"unexpected synthetic next step: {report['recommended_next_step']}",
        )
        _assert(
            packet["preferred_append_surface_path"] == "system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md",
            "unexpected preferred append surface",
        )
        _assert(packet["allow_new_owner_surface_creation"] is False, "packet must stay bounded")

    repo_report, repo_packet = build_a2_append_safe_context_shell_audit_report(REPO_ROOT)
    _assert(repo_report["status"] == "ok", f"unexpected live status: {repo_report['status']}")
    _assert(
        repo_report["selector_alignment"]["selected_pattern_id"] == "append_safe_context_shell",
        "unexpected live selected pattern",
    )
    _assert(
        repo_report["selector_alignment"]["aligned"] is True,
        "live selector alignment should hold",
    )
    _assert(
        repo_packet["recommended_next_step"] == "hold_append_safe_context_shell_as_audit_only",
        f"unexpected live next step: {repo_packet['recommended_next_step']}",
    )

    blocked_report, blocked_packet = build_a2_append_safe_context_shell_audit_report(
        REPO_ROOT,
        {"audit_scope": "runtime_context_manager_install"},
    )
    _assert(blocked_report["status"] == "attention_required", "widened scope should fail closed")
    _assert(blocked_packet["recommended_next_step"] == "", "blocked packet should not recommend next step")

    with tempfile.TemporaryDirectory() as tmpdir:
        report_json = Path(tmpdir) / "append_safe.json"
        report_md = Path(tmpdir) / "append_safe.md"
        packet_json = Path(tmpdir) / "append_safe.packet.json"
        emitted = run_a2_append_safe_context_shell_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(report_json),
                "report_md_path": str(report_md),
                "packet_path": str(packet_json),
            }
        )
        _assert(report_json.exists(), "report json missing")
        _assert(report_md.exists(), "report markdown missing")
        _assert(packet_json.exists(), "packet json missing")
        _assert(
            emitted["recommended_next_step"] == "hold_append_safe_context_shell_as_audit_only",
            "unexpected emitted next step",
        )

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_append_safe_context_shell_audit_operator.py": (
                lambda ctx: "a2-append-safe-context-shell-audit-operator-dispatch"
            ),
        }
    )
    skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["append-safe-context-shell"],
    )
    _assert(
        any(skill.skill_id == "a2-append-safe-context-shell-audit-operator" for skill in skills),
        "append-safe context shell operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        skills,
        ["a2-append-safe-context-shell-audit-operator"],
        runtime_model="shell",
    )
    _assert(selected == "a2-append-safe-context-shell-audit-operator", f"unexpected selection: {selected}")
    _assert(not fallback, "operator unexpectedly fell back")
    _assert(dispatch is not None, "operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected reason: {reason}")

    print("PASS: a2 append safe context shell audit operator smoke")


if __name__ == "__main__":
    main()
