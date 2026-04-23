"""Smoke test for the bounded next-state signal adaptation audit operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_next_state_signal_adaptation_audit_operator import (
    build_a2_next_state_signal_adaptation_audit_report,
    run_a2_next_state_signal_adaptation_audit,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_a2_next_state_signal_adaptation_audit_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected next-state adaptation audit status: {report['status']}")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::next-state-signal-adaptation",
        "unexpected cluster id",
    )
    _assert(
        report["first_slice"] == "a2-next-state-signal-adaptation-audit-operator",
        "unexpected first slice id",
    )
    _assert(report["audit_only"] is True, "next-state adaptation audit should stay audit-only")
    _assert(report["nonoperative"] is True, "next-state adaptation audit should stay nonoperative")
    _assert(report["do_not_promote"] is True, "next-state adaptation audit should stay non-promotable")
    _assert(
        packet["allow_bounded_pattern_mining"] is True,
        "next-state adaptation audit should allow bounded pattern mining",
    )
    _assert(
        packet["allow_runtime_import_claims"] is False,
        "next-state adaptation audit should not allow runtime import claims",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "next_state_signal_adaptation_audit.json"
        md_path = Path(tmpdir) / "next_state_signal_adaptation_audit.md"
        packet_path = Path(tmpdir) / "next_state_signal_adaptation_audit.packet.json"
        emitted = run_a2_next_state_signal_adaptation_audit(
            {
                "repo": str(REPO_ROOT),
                "report_path": str(json_path),
                "markdown_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "next-state adaptation audit json was not written")
        _assert(md_path.exists(), "next-state adaptation audit markdown was not written")
        _assert(packet_path.exists(), "next-state adaptation audit packet was not written")
        _assert(emitted["report_path"] == str(json_path), "unexpected next-state adaptation audit json path")
        _assert(emitted["markdown_path"] == str(md_path), "unexpected next-state adaptation audit markdown path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected next-state adaptation audit packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_next_state_signal_adaptation_audit_operator.py": (
                lambda ctx: "a2-next-state-signal-adaptation-audit-operator-dispatch"
            ),
        }
    )
    next_state_signal_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["next-state-signals"],
    )
    _assert(
        any(skill.skill_id == "a2-next-state-signal-adaptation-audit-operator" for skill in next_state_signal_skills),
        "a2-next-state-signal-adaptation-audit-operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        next_state_signal_skills,
        ["a2-next-state-signal-adaptation-audit-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-next-state-signal-adaptation-audit-operator",
        f"unexpected next-state adaptation audit selection: {selected}",
    )
    _assert(not fallback, "a2-next-state-signal-adaptation-audit-operator unexpectedly fell back")
    _assert(dispatch is not None, "a2-next-state-signal-adaptation-audit-operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected next-state adaptation audit reason: {reason}")

    print("PASS: a2 next-state signal adaptation audit operator smoke")


if __name__ == "__main__":
    main()
