"""Smoke test for the context/spec/workflow pattern audit operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_context_spec_workflow_pattern_audit_operator import (
    build_a2_context_spec_workflow_pattern_audit_report,
    run_a2_context_spec_workflow_pattern_audit,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_a2_context_spec_workflow_pattern_audit_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected audit status: {report['status']}")
    _assert(report["audit_only"] is True, "slice must stay audit-only")
    _assert(report["nonoperative"] is True, "slice must stay nonoperative")
    _assert(report["do_not_promote"] is True, "slice must stay do_not_promote")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::context-spec-workflow-memory",
        f"unexpected cluster id: {report['cluster_id']}",
    )
    _assert(
        report["slice_id"] == "a2-context-spec-workflow-pattern-audit-operator",
        f"unexpected slice id: {report['slice_id']}",
    )
    _assert(
        len(report["admissible_pattern_families"]) == 4,
        f"unexpected pattern family count: {len(report['admissible_pattern_families'])}",
    )
    _assert(
        packet["recommended_next_step"] == "hold_first_slice_as_audit_only",
        f"unexpected next step: {packet['recommended_next_step']}",
    )
    _assert(packet["allow_runtime_live_claims"] is False, "runtime live claims must stay disabled")
    _assert(packet["allow_training"] is False, "training must stay disabled")
    _assert(packet["allow_service_bootstrap"] is False, "service bootstrap must stay disabled")
    _assert(packet["allow_canonical_brain_replacement"] is False, "canonical brain replacement must stay disabled")
    _assert(packet["allow_graph_substrate_replacement"] is False, "graph replacement must stay disabled")
    _assert(packet["allow_registry_mutation"] is False, "registry mutation must stay disabled")

    blocked_report, blocked_packet = build_a2_context_spec_workflow_pattern_audit_report(
        REPO_ROOT,
        {"analysis_scope": "runtime_import_lane"},
    )
    _assert(blocked_report["status"] == "attention_required", "widened scope should fail closed")
    _assert(
        blocked_packet["admissible_pattern_family_ids"] == [],
        "blocked scope should not admit pattern families",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        report_json = Path(tmpdir) / "context.json"
        report_md = Path(tmpdir) / "context.md"
        packet_json = Path(tmpdir) / "context.packet.json"
        emitted = run_a2_context_spec_workflow_pattern_audit(
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
        _assert(emitted["report_json_path"] == str(report_json), "unexpected json path")
        _assert(emitted["report_md_path"] == str(report_md), "unexpected md path")
        _assert(emitted["packet_path"] == str(packet_json), "unexpected packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_context_spec_workflow_pattern_audit_operator.py": (
                lambda ctx: "a2-context-spec-workflow-pattern-audit-operator-dispatch"
            ),
        }
    )
    skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["context-spec-workflow"],
    )
    _assert(
        any(skill.skill_id == "a2-context-spec-workflow-pattern-audit-operator" for skill in skills),
        "context/spec/workflow slice was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        skills,
        ["a2-context-spec-workflow-pattern-audit-operator"],
        runtime_model="shell",
    )
    _assert(selected == "a2-context-spec-workflow-pattern-audit-operator", f"unexpected selection: {selected}")
    _assert(not fallback, "slice unexpectedly fell back")
    _assert(dispatch is not None, "dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected dispatch reason: {reason}")

    print("PASS: a2 context spec workflow pattern audit operator smoke")


if __name__ == "__main__":
    main()
