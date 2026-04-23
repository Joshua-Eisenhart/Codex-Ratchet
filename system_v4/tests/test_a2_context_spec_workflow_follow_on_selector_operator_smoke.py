"""Smoke test for the context/spec/workflow follow-on selector operator."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_context_spec_workflow_follow_on_selector_operator import (
    build_a2_context_spec_workflow_follow_on_selector_report,
    run_a2_context_spec_workflow_follow_on_selector,
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
        pattern_report = root / "pattern_report.json"
        pattern_packet = root / "pattern_packet.json"
        source_selector_report = root / "source_selector_report.json"
        evermem_report = root / "evermem_report.json"
        controller_record = root / "controller.md"

        _write_json(
            pattern_report,
            {
                "status": "ok",
                "admissible_pattern_families": [
                    {"pattern_id": "append_safe_context_shell"},
                    {"pattern_id": "executable_spec_coupling"},
                    {"pattern_id": "workflow_review_discipline"},
                    {"pattern_id": "scoped_memory_sidecar"},
                ],
            },
        )
        _write_json(pattern_packet, {"recommended_next_step": "hold_first_slice_as_audit_only"})
        _write_json(
            source_selector_report,
            {
                "status": "attention_required",
                "candidate_clusters": [
                    {
                        "cluster_id": "SKILL_CLUSTER::context-spec-workflow-memory",
                        "already_landed": True,
                        "recommended_first_slice_id": "a2-context-spec-workflow-pattern-audit-operator",
                    }
                ],
            },
        )
        _write_json(evermem_report, {"status": "attention_required"})
        _write_text(controller_record, "append-safe context and low-bloat continuity matter\n")

        report, packet = build_a2_context_spec_workflow_follow_on_selector_report(
            root,
            {
                "pattern_report_path": str(pattern_report),
                "pattern_packet_path": str(pattern_packet),
                "source_selector_report_path": str(source_selector_report),
                "evermem_report_path": str(evermem_report),
                "controller_record_path": str(controller_record),
            },
        )
        _assert(report["status"] == "ok", f"unexpected synthetic status: {report['status']}")
        _assert(report["selected_pattern_id"] == "append_safe_context_shell", "unexpected selected pattern")
        _assert(
            report["recommended_next_slice_id"] == "a2-append-safe-context-shell-audit-operator",
            "unexpected selected next slice",
        )
        _assert(
            any(
                item["pattern_id"] == "scoped_memory_sidecar" and item["status"] == "blocked"
                for item in report["selection_options"]
            ),
            "expected scoped memory sidecar to be blocked in synthetic case",
        )
        _assert(packet["allow_runtime_live_claims"] is False, "selector packet must stay bounded")

    repo_report, repo_packet = build_a2_context_spec_workflow_follow_on_selector_report(REPO_ROOT)
    _assert(repo_report["status"] == "ok", f"unexpected live selector status: {repo_report['status']}")
    _assert(repo_report["selected_pattern_id"] == "append_safe_context_shell", "unexpected live selected pattern")
    _assert(
        repo_report["recommended_next_slice_id"] == "a2-append-safe-context-shell-audit-operator",
        f"unexpected live next slice: {repo_report['recommended_next_slice_id']}",
    )
    _assert(repo_packet["allow_runtime_live_claims"] is False, "live selector packet must stay bounded")

    blocked_report, blocked_packet = build_a2_context_spec_workflow_follow_on_selector_report(
        REPO_ROOT,
        {"selection_scope": "runtime_mutation_follow_on"},
    )
    _assert(blocked_report["status"] == "attention_required", "widened selector scope should fail closed")
    _assert(blocked_packet["recommended_next_slice_id"] == "", "blocked selector should not recommend a slice")

    with tempfile.TemporaryDirectory() as tmpdir:
        report_json = Path(tmpdir) / "selector.json"
        report_md = Path(tmpdir) / "selector.md"
        packet_json = Path(tmpdir) / "selector.packet.json"
        emitted = run_a2_context_spec_workflow_follow_on_selector(
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
            emitted["recommended_next_slice_id"] == "a2-append-safe-context-shell-audit-operator",
            "unexpected emitted next slice",
        )

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_context_spec_workflow_follow_on_selector_operator.py": (
                lambda ctx: "a2-context-spec-workflow-follow-on-selector-operator-dispatch"
            ),
        }
    )
    skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["context-spec-follow-on-selector"],
    )
    _assert(
        any(skill.skill_id == "a2-context-spec-workflow-follow-on-selector-operator" for skill in skills),
        "follow-on selector was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        skills,
        ["a2-context-spec-workflow-follow-on-selector-operator"],
        runtime_model="shell",
    )
    _assert(selected == "a2-context-spec-workflow-follow-on-selector-operator", f"unexpected selection: {selected}")
    _assert(not fallback, "selector unexpectedly fell back")
    _assert(dispatch is not None, "selector dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected selector reason: {reason}")

    print("PASS: a2 context spec workflow follow-on selector operator smoke")


if __name__ == "__main__":
    main()
