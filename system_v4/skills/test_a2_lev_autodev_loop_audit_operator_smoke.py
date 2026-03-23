"""Smoke test for the bounded lev autodev loop audit operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills import run_real_ratchet as rr
from system_v4.skills.a2_lev_autodev_loop_audit_operator import (
    build_a2_lev_autodev_loop_audit_report,
    run_a2_lev_autodev_loop_audit,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_a2_lev_autodev_loop_audit_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected autodev loop audit status: {report['status']}")
    _assert(report["audit_only"] is True, "autodev loop audit should stay audit-only")
    _assert(report["nonoperative"] is True, "autodev loop audit should stay nonoperative")
    _assert(report["do_not_promote"] is True, "autodev loop audit should stay non-promotable")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::lev-autodev-exec-validation",
        "unexpected autodev loop cluster id",
    )
    _assert(
        report["first_slice"] == "a2-lev-autodev-loop-audit-operator",
        "unexpected autodev loop first slice id",
    )
    _assert(
        report["recommended_source_skill_id"] == "autodev-loop",
        "unexpected recommended source skill",
    )
    _assert(
        report["gate"]["allow_bounded_autodev_loop_audit"] is True,
        "autodev loop audit should allow the bounded audit on the live repo",
    )
    _assert(packet["allow_runtime_loop_claims"] is False, "packet must not allow runtime loop claims")
    _assert(packet["allow_cron_claims"] is False, "packet must not allow cron claims")

    blocked_report, _ = build_a2_lev_autodev_loop_audit_report(
        REPO_ROOT,
        {
            "candidate": {
                "id": "too-wide-autodev-request",
                "title": "run lev autodev and service install",
                "type": "autodev_loop_audit",
                "source": "test",
                "raw_input": "start the heartbeat, launchd, and git push after each tick",
                "stage_request": "autodev_loop_audit",
                "source_refs": [
                    "work/reference_repos/lev-os/agents/skills/autodev-loop/SKILL.md",
                ],
            }
        },
    )
    _assert(
        blocked_report["status"] == "attention_required",
        "wide autodev request should force attention_required status",
    )
    _assert(
        blocked_report["gate"]["allow_bounded_autodev_loop_audit"] is False,
        "wide autodev request should not pass the autodev gate",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "autodev.json"
        md_path = Path(tmpdir) / "autodev.md"
        packet_path = Path(tmpdir) / "autodev.packet.json"
        emitted = run_a2_lev_autodev_loop_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "autodev loop audit json was not written")
        _assert(md_path.exists(), "autodev loop audit markdown was not written")
        _assert(packet_path.exists(), "autodev loop audit packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_lev_autodev_loop_audit_operator.py": (
                lambda ctx: "a2-lev-autodev-loop-audit-operator-dispatch"
            ),
        }
    )
    autodev_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["lev-autodev-loop"],
    )
    _assert(
        any(skill.skill_id == "a2-lev-autodev-loop-audit-operator" for skill in autodev_skills),
        "autodev loop audit operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        autodev_skills,
        ["a2-lev-autodev-loop-audit-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-lev-autodev-loop-audit-operator",
        f"unexpected autodev loop audit selection: {selected}",
    )
    _assert(not fallback, "autodev loop audit operator unexpectedly fell back")
    _assert(dispatch is not None, "autodev loop audit operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected autodev loop audit reason: {reason}")

    print("PASS: a2 lev autodev loop audit operator smoke")


if __name__ == "__main__":
    main()
