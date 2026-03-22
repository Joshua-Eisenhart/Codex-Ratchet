"""Smoke test for the bounded lev-builder placement audit operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_lev_builder_placement_audit_operator import (
    build_a2_lev_builder_placement_audit_report,
    run_a2_lev_builder_placement_audit,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_a2_lev_builder_placement_audit_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected placement audit status: {report['status']}")
    _assert(report["audit_only"] is True, "placement audit should stay audit-only")
    _assert(report["nonoperative"] is True, "placement audit should stay nonoperative")
    _assert(report["do_not_promote"] is True, "placement audit should stay non-promotable")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::lev-formalization-placement",
        "unexpected placement cluster id",
    )
    _assert(
        report["first_slice"] == "a2-lev-builder-placement-audit-operator",
        "unexpected first slice id",
    )
    _assert(
        report["recommended_source_skill_id"] == "lev-builder",
        "unexpected recommended source skill",
    )
    _assert(
        report["gate"]["allow_bounded_placement_audit"] is True,
        "placement audit should allow the bounded audit on the live repo",
    )
    _assert(
        packet["recommended_source_skill_id"] == "lev-builder",
        "packet did not carry the expected source skill",
    )
    _assert(packet["allow_migration"] is False, "placement packet must not allow migration")

    blocked_report, _ = build_a2_lev_builder_placement_audit_report(
        REPO_ROOT,
        {
            "candidate": {
                "id": "too-wide-placement",
                "title": "migration request",
                "type": "placement_audit",
                "source": "test",
                "raw_input": "apply patch and migrate to production",
                "stage_request": "placement_audit",
                "source_refs": [
                    "work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md",
                ],
            }
        },
    )
    _assert(
        blocked_report["status"] == "attention_required",
        "wide placement request should force attention_required status",
    )
    _assert(
        blocked_report["gate"]["allow_bounded_placement_audit"] is False,
        "wide placement request should not pass the placement gate",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "placement.json"
        md_path = Path(tmpdir) / "placement.md"
        packet_path = Path(tmpdir) / "placement.packet.json"
        emitted = run_a2_lev_builder_placement_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "placement audit json was not written")
        _assert(md_path.exists(), "placement audit markdown was not written")
        _assert(packet_path.exists(), "placement audit packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_lev_builder_placement_audit_operator.py": (
                lambda ctx: "a2-lev-builder-placement-audit-operator-dispatch"
            ),
        }
    )
    placement_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["lev-builder-placement"],
    )
    _assert(
        any(skill.skill_id == "a2-lev-builder-placement-audit-operator" for skill in placement_skills),
        "placement audit operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        placement_skills,
        ["a2-lev-builder-placement-audit-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-lev-builder-placement-audit-operator",
        f"unexpected placement audit selection: {selected}",
    )
    _assert(not fallback, "placement audit operator unexpectedly fell back")
    _assert(dispatch is not None, "placement audit operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected placement audit reason: {reason}")

    print("PASS: a2 lev-builder placement audit operator smoke")


if __name__ == "__main__":
    main()
