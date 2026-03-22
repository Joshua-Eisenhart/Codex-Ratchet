"""Smoke test for the bounded lev-os/agents promotion operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_lev_agents_promotion_operator import (
    build_a2_lev_agents_promotion_report,
    run_a2_lev_agents_promotion,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_a2_lev_agents_promotion_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected promotion audit status: {report['status']}")
    _assert(report["audit_only"] is True, "promotion audit should stay audit-only")
    _assert(report["do_not_promote"] is True, "promotion audit should stay non-promotable")
    _assert(report["curated_skill_count"] == 61, "unexpected curated skill count")
    _assert(report["library_skill_count"] == 574, "unexpected library skill count")
    _assert(report["total_skill_count"] == 635, "unexpected total skill count")
    _assert(report["landed_lev_cluster_count"] == 7, "unexpected landed lev cluster count")
    _assert(report["parked_lev_cluster_count"] == 1, "unexpected parked lev cluster count")
    _assert(
        report["has_current_unopened_cluster"] is False,
        "expected no current unopened lev cluster after architecture-fitness landing",
    )
    _assert(
        report["recommended_next_cluster"] == {},
        "expected no recommended next cluster after exhausting the current lev set",
    )
    _assert(
        packet["has_current_unopened_cluster"] is False,
        "packet should record no current unopened lev cluster",
    )
    _assert(
        packet["recommended_first_slice_id"] == "",
        "expected empty recommended first slice when no unopened lev cluster remains",
    )
    _assert(packet["allow_imported_runtime_claims"] is False, "promotion packet must stay bounded")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "promotion.json"
        md_path = Path(tmpdir) / "promotion.md"
        packet_path = Path(tmpdir) / "promotion.packet.json"
        emitted = run_a2_lev_agents_promotion(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "promotion json was not written")
        _assert(md_path.exists(), "promotion markdown was not written")
        _assert(packet_path.exists(), "promotion packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_lev_agents_promotion_operator.py": (
                lambda ctx: "a2-lev-agents-promotion-operator-dispatch"
            ),
        }
    )
    promotion_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["lev-agents-promotion"],
    )
    _assert(
        any(skill.skill_id == "a2-lev-agents-promotion-operator" for skill in promotion_skills),
        "promotion operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        promotion_skills,
        ["a2-lev-agents-promotion-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-lev-agents-promotion-operator",
        f"unexpected promotion selection: {selected}",
    )
    _assert(not fallback, "promotion operator unexpectedly fell back")
    _assert(dispatch is not None, "promotion operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected promotion reason: {reason}")

    print("PASS: a2 lev agents promotion operator smoke")


if __name__ == "__main__":
    main()
