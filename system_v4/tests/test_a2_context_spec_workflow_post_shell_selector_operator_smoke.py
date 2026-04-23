"""Smoke test for the context/spec/workflow post-shell selector operator."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_context_spec_workflow_post_shell_selector_operator import (
    build_a2_context_spec_workflow_post_shell_selector_report,
    run_a2_context_spec_workflow_post_shell_selector,
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
        _write_json(
            root / "system_v4/a2_state/audit_logs/A2_APPEND_SAFE_CONTEXT_SHELL_AUDIT_REPORT__CURRENT__v1.json",
            {
                "status": "ok",
                "slice_id": "a2-append-safe-context-shell-audit-operator",
                "recommended_next_step": "hold_append_safe_context_shell_as_audit_only",
            },
        )
        _write_json(
            root / "system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.json",
            {
                "status": "ok",
                "selected_pattern_id": "append_safe_context_shell",
                "recommended_next_slice_id": "a2-append-safe-context-shell-audit-operator",
            },
        )
        _write_json(
            root / "system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.json",
            {"status": "attention_required"},
        )

        report, packet = build_a2_context_spec_workflow_post_shell_selector_report(root)
        _assert(report["status"] == "ok", f"unexpected synthetic status: {report['status']}")
        _assert(report["selected_option_id"] == "hold_after_append_safe_shell", "unexpected selected option")
        _assert(
            report["standby_next_slice_id"] == "a2-executable-spec-coupling-audit-operator",
            "unexpected standby next slice",
        )
        _assert(
            report["recommended_next_step"] == "hold_cluster_after_append_safe_shell",
            f"unexpected synthetic next step: {report['recommended_next_step']}",
        )
        _assert(packet["allow_multi_pattern_widening"] is False, "packet must stay bounded")

    repo_report, repo_packet = build_a2_context_spec_workflow_post_shell_selector_report(REPO_ROOT)
    _assert(repo_report["status"] == "ok", f"unexpected live status: {repo_report['status']}")
    _assert(repo_report["selected_option_id"] == "hold_after_append_safe_shell", "unexpected live selected option")
    _assert(
        repo_report["standby_next_slice_id"] == "a2-executable-spec-coupling-audit-operator",
        f"unexpected live standby slice: {repo_report['standby_next_slice_id']}",
    )
    _assert(
        repo_packet["recommended_next_step"] == "hold_cluster_after_append_safe_shell",
        f"unexpected live next step: {repo_packet['recommended_next_step']}",
    )

    blocked_report, blocked_packet = build_a2_context_spec_workflow_post_shell_selector_report(
        REPO_ROOT,
        {"selection_scope": "runtime_continuation_selector"},
    )
    _assert(blocked_report["status"] == "attention_required", "widened scope should fail closed")
    _assert(blocked_packet["recommended_next_step"] == "", "blocked packet should not recommend next step")

    with tempfile.TemporaryDirectory() as tmpdir:
        report_json = Path(tmpdir) / "post_shell_selector.json"
        report_md = Path(tmpdir) / "post_shell_selector.md"
        packet_json = Path(tmpdir) / "post_shell_selector.packet.json"
        emitted = run_a2_context_spec_workflow_post_shell_selector(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(report_json),
                "report_md_path": str(report_md),
                "packet_path": str(packet_json),
            }
        )
        _assert(report_json.exists(), "selector json missing")
        _assert(report_md.exists(), "selector markdown missing")
        _assert(packet_json.exists(), "selector packet missing")
        _assert(
            emitted["standby_next_slice_id"] == "a2-executable-spec-coupling-audit-operator",
            "unexpected emitted standby next slice",
        )

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_context_spec_workflow_post_shell_selector_operator.py": (
                lambda ctx: "a2-context-spec-workflow-post-shell-selector-operator-dispatch"
            ),
        }
    )
    skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["context-spec-post-shell-selector"],
    )
    _assert(
        any(skill.skill_id == "a2-context-spec-workflow-post-shell-selector-operator" for skill in skills),
        "post-shell selector was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        skills,
        ["a2-context-spec-workflow-post-shell-selector-operator"],
        runtime_model="shell",
    )
    _assert(selected == "a2-context-spec-workflow-post-shell-selector-operator", f"unexpected selection: {selected}")
    _assert(not fallback, "selector unexpectedly fell back")
    _assert(dispatch is not None, "selector dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected reason: {reason}")

    print("PASS: a2 context spec workflow post shell selector operator smoke")


if __name__ == "__main__":
    main()
