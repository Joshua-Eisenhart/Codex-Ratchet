"""Smoke test for the bounded skill improver target selector operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_skill_improver_target_selector_operator import (
    build_skill_improver_target_selection_report,
    run_a2_skill_improver_target_selector,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_skill_improver_target_selection_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected selector status: {report['status']}")
    _assert(report["audit_only"] is True, "selector should stay audit-only")
    _assert(report["do_not_promote"] is True, "selector should stay non-promotable")
    _assert(
        report["slice_id"] == "a2-skill-improver-target-selector-operator",
        "unexpected selector slice id",
    )
    _assert(
        report["readiness_gate_status"] == "bounded_ready_for_first_target",
        "selector did not see the current readiness gate",
    )
    _assert(report["candidate_count"] > 0, "selector did not find any candidates")
    _assert(
        report["recommended_target"].get("skill_id") == "a2-skill-improver-readiness-operator",
        "selector did not choose the expected first target",
    )
    _assert(
        packet["recommended_target_skill_id"] == "a2-skill-improver-readiness-operator",
        "packet did not carry the expected target",
    )
    _assert(packet["allow_live_repo_mutation"] is False, "selector packet must stay non-mutating")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "selector.json"
        md_path = Path(tmpdir) / "selector.md"
        packet_path = Path(tmpdir) / "selector.packet.json"
        emitted = run_a2_skill_improver_target_selector(
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
            "system_v4/skills/a2_skill_improver_target_selector_operator.py": (
                lambda ctx: "a2-skill-improver-target-selector-operator-dispatch"
            ),
        }
    )
    selector_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["skill-improver-target-selection"],
    )
    _assert(
        any(skill.skill_id == "a2-skill-improver-target-selector-operator" for skill in selector_skills),
        "selector operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        selector_skills,
        ["a2-skill-improver-target-selector-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-skill-improver-target-selector-operator",
        f"unexpected selector selection: {selected}",
    )
    _assert(not fallback, "selector unexpectedly fell back")
    _assert(dispatch is not None, "selector dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected selector reason: {reason}")

    print("PASS: a2 skill improver target selector operator smoke")


if __name__ == "__main__":
    main()
