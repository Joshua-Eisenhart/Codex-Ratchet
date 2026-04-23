"""Smoke test for the lev-builder formalization skeleton operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_lev_builder_formalization_skeleton_operator import (
    build_a2_lev_builder_formalization_skeleton_report,
    run_a2_lev_builder_formalization_skeleton,
)
from system_v4.skills.skill_registry import SkillRegistry

SPEC_PATH = (
    REPO_ROOT
    / "system_v4/skill_specs/a2-lev-builder-formalization-skeleton-operator/SKILL.md"
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    _assert(SPEC_PATH.exists(), f"missing spec file: {SPEC_PATH}")
    spec_text = SPEC_PATH.read_text(encoding="utf-8")

    required_snippets = [
        "skill_id: a2-lev-builder-formalization-skeleton-operator",
        "name: a2-lev-builder-formalization-skeleton-operator",
        "Prove the bounded lev-builder formalization scaffold bundle is landed",
        "without migration, registry, runner, or runtime-import claims",
        "A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1.json",
        "A2_LEV_BUILDER_FORMALIZATION_SKELETON_PACKET__CURRENT__v1.json",
        "A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_REPORT__CURRENT__v1.json",
        "A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json",
        "GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json",
        "lev-builder",
        "arch",
        "work",
        "Verify the bounded scaffold bundle is present:",
        "Keep the scaffold bundle explicitly bounded, repo-held, and non-runtime-live.",
        "Do not update registry or runner surfaces from inside this operator.",
        "Do not claim runtime import, production placement, formalization completion, or imported runtime ownership.",
    ]
    for snippet in required_snippets:
        _assert(snippet in spec_text, f"missing required spec text: {snippet}")

    report, packet = build_a2_lev_builder_formalization_skeleton_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected skeleton status: {report['status']}")
    _assert(report["audit_only"] is True, "skeleton operator should stay audit-only")
    _assert(report["nonoperative"] is True, "skeleton operator should stay nonoperative")
    _assert(report["scaffold_only"] is True, "skeleton operator should stay scaffold-only")
    _assert(report["non_migratory"] is True, "skeleton operator should stay non-migratory")
    _assert(report["do_not_promote"] is True, "skeleton operator should stay non-promotable")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::lev-formalization-placement",
        "unexpected formalization skeleton cluster",
    )
    _assert(
        report["slice_id"] == "a2-lev-builder-formalization-skeleton-operator",
        "unexpected skeleton slice id",
    )
    _assert(
        report["gate"]["bounded_scaffold_completed"] is True,
        "skeleton gate should confirm the landed scaffold bundle",
    )
    _assert(
        all(item["exists"] for item in report["scaffold_write_results"]),
        "all scaffold bundle paths should exist on the live repo",
    )
    _assert(packet["bounded_scaffold_completed"] is True, "packet should confirm scaffold completion")
    _assert(packet["allow_registry_mutation"] is False, "packet must not allow registry mutation")
    _assert(packet["allow_runner_mutation"] is False, "packet must not allow runner mutation")
    _assert(packet["allow_runtime_claims"] is False, "packet must not allow runtime claims")
    _assert(packet["allow_migration"] is False, "packet must not allow migration")

    blocked_report, _ = build_a2_lev_builder_formalization_skeleton_report(
        REPO_ROOT,
        {
            "candidate": {
                "id": "too-wide-skeleton",
                "title": "runtime-import request",
                "type": "formalization_skeleton",
                "source": "test",
                "raw_input": "apply patch, migrate to production, update registry, and claim integration",
                "stage_request": "formalization_skeleton",
                "source_refs": [
                    "work/reference_repos/lev-os/agents/skills/lev-builder/SKILL.md",
                    "work/reference_repos/lev-os/agents/skills/arch/SKILL.md",
                    "work/reference_repos/lev-os/agents/skills/work/SKILL.md",
                ],
            }
        },
    )
    _assert(
        blocked_report["status"] == "attention_required",
        "wide skeleton request should force attention_required status",
    )
    _assert(
        blocked_report["gate"]["bounded_scaffold_completed"] is False,
        "wide skeleton request should not pass the scaffold gate",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "formalization-skeleton.json"
        md_path = Path(tmpdir) / "formalization-skeleton.md"
        packet_path = Path(tmpdir) / "formalization-skeleton.packet.json"
        emitted = run_a2_lev_builder_formalization_skeleton(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "skeleton json was not written")
        _assert(md_path.exists(), "skeleton markdown was not written")
        _assert(packet_path.exists(), "skeleton packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_lev_builder_formalization_skeleton_operator.py": (
                lambda ctx: "a2-lev-builder-formalization-skeleton-operator-dispatch"
            ),
        }
    )
    skeleton_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["formalization-skeleton"],
    )
    _assert(
        any(
            skill.skill_id == "a2-lev-builder-formalization-skeleton-operator"
            for skill in skeleton_skills
        ),
        "formalization skeleton operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        skeleton_skills,
        ["a2-lev-builder-formalization-skeleton-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-lev-builder-formalization-skeleton-operator",
        f"unexpected skeleton selection: {selected}",
    )
    _assert(not fallback, "skeleton operator unexpectedly fell back")
    _assert(dispatch is not None, "skeleton operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected skeleton reason: {reason}")

    print("PASS: a2 lev-builder formalization skeleton operator smoke")


if __name__ == "__main__":
    main()
