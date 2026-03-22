"""Smoke test for the bounded lev architecture fitness operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_lev_architecture_fitness_operator import (
    build_a2_lev_architecture_fitness_report,
    run_a2_lev_architecture_fitness,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_a2_lev_architecture_fitness_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected architecture fitness status: {report['status']}")
    _assert(report["audit_only"] is True, "architecture fitness should stay audit-only")
    _assert(report["nonoperative"] is True, "architecture fitness should stay nonoperative")
    _assert(report["do_not_promote"] is True, "architecture fitness should stay non-promotable")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::lev-architecture-fitness-review",
        "unexpected architecture fitness cluster id",
    )
    _assert(
        report["first_slice"] == "a2-lev-architecture-fitness-operator",
        "unexpected architecture fitness first slice id",
    )
    _assert(
        report["recommended_source_skill_id"] == "arch",
        "unexpected architecture fitness source skill",
    )
    _assert(
        report["gate"]["allow_bounded_architecture_fitness_audit"] is True,
        "architecture fitness should allow the bounded audit on the live repo",
    )
    _assert(packet["allow_full_adr_generation"] is False, "packet must not allow full ADR generation")
    _assert(packet["allow_migration"] is False, "packet must not allow migration claims")
    _assert(packet["allow_patch_application"] is False, "packet must not allow patch application")

    blocked_report, _ = build_a2_lev_architecture_fitness_report(
        REPO_ROOT,
        {
            "candidate": {
                "id": "too-wide-arch-request",
                "title": "migrate and generate full review artifacts",
                "type": "architecture_fitness_audit",
                "source": "test",
                "raw_input": "generate full ADR and C4, apply patch, migrate to production, update registry, and git commit",
                "stage_request": "architecture_fitness_audit",
                "source_refs": [
                    "work/reference_repos/lev-os/agents/skills/arch/SKILL.md",
                ],
                "candidate_approaches": [
                    "one",
                    "two",
                ],
            }
        },
    )
    _assert(
        blocked_report["status"] == "attention_required",
        "wide architecture request should force attention_required status",
    )
    _assert(
        blocked_report["gate"]["allow_bounded_architecture_fitness_audit"] is False,
        "wide architecture request should not pass the architecture gate",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "arch.json"
        md_path = Path(tmpdir) / "arch.md"
        packet_path = Path(tmpdir) / "arch.packet.json"
        emitted = run_a2_lev_architecture_fitness(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "architecture fitness json was not written")
        _assert(md_path.exists(), "architecture fitness markdown was not written")
        _assert(packet_path.exists(), "architecture fitness packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_lev_architecture_fitness_operator.py": (
                lambda ctx: "a2-lev-architecture-fitness-operator-dispatch"
            ),
        }
    )
    arch_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["lev-architecture-fitness"],
    )
    _assert(
        any(skill.skill_id == "a2-lev-architecture-fitness-operator" for skill in arch_skills),
        "architecture fitness operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        arch_skills,
        ["a2-lev-architecture-fitness-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-lev-architecture-fitness-operator",
        f"unexpected architecture fitness selection: {selected}",
    )
    _assert(not fallback, "architecture fitness operator unexpectedly fell back")
    _assert(dispatch is not None, "architecture fitness operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected architecture fitness reason: {reason}")

    print("PASS: a2 lev architecture fitness operator smoke")


if __name__ == "__main__":
    main()
