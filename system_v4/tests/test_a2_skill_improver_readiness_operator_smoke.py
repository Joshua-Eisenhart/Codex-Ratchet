"""Smoke test for the skill improver readiness audit operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_skill_improver_readiness_operator import (
    build_skill_improver_readiness_report,
    run_a2_skill_improver_readiness,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    rr.SKILL_DISPATCH.clear()
    report, packet = build_skill_improver_readiness_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected readiness status: {report['status']}")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::a2-skill-truth-maintenance",
        "unexpected cluster id",
    )
    _assert(
        report["first_slice"] == "a2-skill-improver-readiness-operator",
        "unexpected first slice id",
    )
    _assert(
        report["target_readiness"] == "bounded_ready_for_first_target",
        f"unexpected target readiness: {report['target_readiness']}",
    )
    _assert(report["audit_only"] is True, "readiness slice should stay audit-only")
    _assert(report["nonoperative"] is True, "readiness slice should stay nonoperative")
    _assert(report["do_not_promote"] is True, "readiness slice should stay non-promotable")
    _assert(
        report["implementation_flags"]["placeholder_mutation_present"] is False,
        "placeholder mutation path should be gone",
    )
    _assert(
        report["implementation_flags"]["explicit_runtime_gate_present"] is True,
        "explicit runtime gate should be detected",
    )
    _assert(
        report["proof_surfaces"]["skill_spec_exists"] is True,
        "skill-improver spec should now exist",
    )
    _assert(
        report["dispatch_binding_present"] is True,
        "readiness should verify target dispatch through live bootstrap",
    )
    _assert(
        packet["allow_live_repo_mutation"] is False,
        "readiness packet must not allow live mutation",
    )
    _assert(rr.SKILL_DISPATCH == {}, "readiness bootstrap should restore dispatch state after audit")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "skill_improver_readiness.json"
        md_path = Path(tmpdir) / "skill_improver_readiness.md"
        packet_path = Path(tmpdir) / "skill_improver_readiness.packet.json"
        emitted = run_a2_skill_improver_readiness(
            {
                "repo": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "readiness json was not written")
        _assert(md_path.exists(), "readiness markdown was not written")
        _assert(packet_path.exists(), "readiness packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected readiness json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected readiness markdown path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected readiness packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_skill_improver_readiness_operator.py": (
                lambda ctx: "a2-skill-improver-readiness-operator-dispatch"
            ),
        }
    )
    readiness_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["skill-improver-readiness"],
    )
    _assert(
        any(skill.skill_id == "a2-skill-improver-readiness-operator" for skill in readiness_skills),
        "a2-skill-improver-readiness-operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        readiness_skills,
        ["a2-skill-improver-readiness-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-skill-improver-readiness-operator",
        f"unexpected readiness selection: {selected}",
    )
    _assert(not fallback, "a2-skill-improver-readiness-operator unexpectedly fell back")
    _assert(dispatch is not None, "a2-skill-improver-readiness-operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected readiness reason: {reason}")

    print("PASS: a2 skill improver readiness operator smoke")


if __name__ == "__main__":
    main()
