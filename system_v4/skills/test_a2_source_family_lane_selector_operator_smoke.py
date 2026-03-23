"""Smoke test for the bounded source-family lane selector operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills import run_real_ratchet as rr
from system_v4.skills.a2_source_family_lane_selector_operator import (
    build_a2_source_family_lane_selection_report,
    run_a2_source_family_lane_selection,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_a2_source_family_lane_selection_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected selector status: {report['status']}")
    _assert(report["audit_only"] is True, "selector must stay audit-only")
    _assert(report["nonoperative"] is True, "selector must stay nonoperative")
    _assert(report["do_not_promote"] is True, "selector must stay do_not_promote")
    _assert(
        report["selection_state"] == "hold_no_eligible_lane",
        f"unexpected selection_state: {report['selection_state']}",
    )
    _assert(
        report["recommended_next_step"] == "hold_all_non_lev_lanes_until_explicit_reopen",
        f"unexpected recommended_next_step: {report['recommended_next_step']}",
    )
    _assert(packet["recommended_next_cluster_id"] == "", f"unexpected recommended cluster: {packet['recommended_next_cluster_id']}")
    _assert(packet["recommended_first_slice_id"] == "", f"unexpected recommended first slice: {packet['recommended_first_slice_id']}")
    _assert(packet["fallback_cluster_id"] == "", f"unexpected fallback cluster: {packet['fallback_cluster_id']}")
    _assert(
        packet["recommended_next_step"] == "hold_all_non_lev_lanes_until_explicit_reopen",
        f"unexpected packet next step: {packet['recommended_next_step']}",
    )
    _assert(packet["allow_runtime_live_claims"] is False, "selector packet must stay bounded")
    _assert(packet["allow_training"] is False, "selector packet must keep training disabled")
    _assert(packet["allow_external_runtime_import"] is False, "selector packet must keep runtime import disabled")
    _assert(packet["allow_registry_mutation"] is False, "selector packet must keep registry mutation disabled")
    _assert(
        "no bounded source-family lane is currently eligible for explicit reselection" in report["hold_reasons"],
        f"unexpected live hold reasons: {report['hold_reasons']}",
    )

    blocked_report, blocked_packet = build_a2_source_family_lane_selection_report(
        REPO_ROOT,
        {"selection_scope": "runtime_mutation_lane"},
    )
    _assert(
        blocked_report["status"] == "attention_required",
        "widened selection scope should fail closed",
    )
    _assert(
        blocked_packet["recommended_next_cluster_id"] == "",
        "blocked scope should not recommend a next cluster",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "selector.json"
        md_path = Path(tmpdir) / "selector.md"
        packet_path = Path(tmpdir) / "selector.packet.json"
        emitted = run_a2_source_family_lane_selection(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "selector json was not written")
        _assert(md_path.exists(), "selector markdown was not written")
        _assert(packet_path.exists(), "selector packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_source_family_lane_selector_operator.py": (
                lambda ctx: "a2-source-family-lane-selector-operator-dispatch"
            ),
        }
    )
    selection_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["source-family-selector"],
    )
    _assert(
        any(skill.skill_id == "a2-source-family-lane-selector-operator" for skill in selection_skills),
        "source-family selector was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        selection_skills,
        ["a2-source-family-lane-selector-operator"],
        runtime_model="shell",
    )
    _assert(selected == "a2-source-family-lane-selector-operator", f"unexpected selection: {selected}")
    _assert(not fallback, "selector unexpectedly fell back")
    _assert(dispatch is not None, "selector dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected selector reason: {reason}")

    print("PASS: a2 source-family lane selector operator smoke")


if __name__ == "__main__":
    main()
