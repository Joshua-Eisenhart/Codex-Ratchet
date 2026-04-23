"""Smoke test for the lev-builder formalization proposal operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_lev_builder_formalization_proposal_operator import (
    build_a2_lev_builder_formalization_proposal_report,
    run_a2_lev_builder_formalization_proposal,
)
from system_v4.skills.skill_registry import SkillRegistry


SPEC_PATH = (
    REPO_ROOT
    / "system_v4/skill_specs/a2-lev-builder-formalization-proposal-operator/SKILL.md"
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    _assert(SPEC_PATH.exists(), f"missing spec file: {SPEC_PATH}")
    spec_text = SPEC_PATH.read_text(encoding="utf-8")
    for snippet in [
        "skill_id: a2-lev-builder-formalization-proposal-operator",
        "can_only_propose: true",
        "A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_REPORT__CURRENT__v1.json",
        "A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_PACKET__CURRENT__v1.json",
        "Do not migrate files.",
        "Do not generate or apply patches.",
        "Do not claim runtime import, production placement, or formalization completion.",
    ]:
        _assert(snippet in spec_text, f"missing required spec text: {snippet}")

    report, packet = build_a2_lev_builder_formalization_proposal_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected proposal status: {report['status']}")
    _assert(report["audit_only"] is True, "proposal operator should stay audit-only")
    _assert(report["nonoperative"] is True, "proposal operator should stay nonoperative")
    _assert(report["proposal_only"] is True, "proposal operator should stay proposal-only")
    _assert(report["do_not_promote"] is True, "proposal operator should stay non-promotable")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::lev-formalization-placement",
        "unexpected formalization proposal cluster",
    )
    _assert(
        report["slice_id"] == "a2-lev-builder-formalization-proposal-operator",
        "unexpected slice id",
    )
    _assert(
        report["formalization_proposal"]["proposal_target"]["proposed_skill_id"]
        == "a2-lev-builder-formalization-skeleton-operator",
        "unexpected proposed future build target",
    )
    _assert(
        report["gate"]["allow_formalization_proposal"] is True,
        "proposal gate should allow bounded proposal emission on the live repo",
    )
    _assert(packet["proposal_only"] is True, "packet should remain proposal-only")
    _assert(packet["allow_build"] is False, "proposal packet must not allow build")
    _assert(packet["allow_migration"] is False, "proposal packet must not allow migration")
    _assert(
        packet["allow_runtime_claims"] is False,
        "proposal packet must not allow runtime claims",
    )

    blocked_report, _ = build_a2_lev_builder_formalization_proposal_report(
        REPO_ROOT,
        {
            "candidate": {
                "id": "too-wide-formalization",
                "title": "runtime-import request",
                "type": "formalization_proposal",
                "source": "test",
                "raw_input": "generate patch, migrate to production, and claim integration",
                "stage_request": "formalization_proposal",
                "source_refs": [
                    "work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md",
                    "work/reference_repos/lev-os/agents/skills/arch/SKILL.md",
                    "work/reference_repos/lev-os/agents/skills/work/SKILL.md",
                ],
                "reference_refs": [
                    "work/reference_repos/lev-os/agents/skills/lev-builder/references/dsl-spec.md"
                ],
            }
        },
    )
    _assert(
        blocked_report["status"] == "attention_required",
        "wide proposal request should force attention_required status",
    )
    _assert(
        blocked_report["gate"]["allow_formalization_proposal"] is False,
        "wide proposal request should not pass the proposal gate",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "formalization-proposal.json"
        md_path = Path(tmpdir) / "formalization-proposal.md"
        packet_path = Path(tmpdir) / "formalization-proposal.packet.json"
        emitted = run_a2_lev_builder_formalization_proposal(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "proposal json was not written")
        _assert(md_path.exists(), "proposal markdown was not written")
        _assert(packet_path.exists(), "proposal packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_lev_builder_formalization_proposal_operator.py": (
                lambda ctx: "a2-lev-builder-formalization-proposal-operator-dispatch"
            ),
        }
    )
    proposal_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["formalization-proposal"],
    )
    _assert(
        any(
            skill.skill_id == "a2-lev-builder-formalization-proposal-operator"
            for skill in proposal_skills
        ),
        "formalization proposal operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        proposal_skills,
        ["a2-lev-builder-formalization-proposal-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-lev-builder-formalization-proposal-operator",
        f"unexpected proposal selection: {selected}",
    )
    _assert(not fallback, "proposal operator unexpectedly fell back")
    _assert(dispatch is not None, "proposal operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected proposal reason: {reason}")

    print("PASS: a2 lev-builder formalization proposal operator smoke")


if __name__ == "__main__":
    main()
