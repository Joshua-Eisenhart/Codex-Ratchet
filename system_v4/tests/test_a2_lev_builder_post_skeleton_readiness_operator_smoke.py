"""Smoke test for the bounded lev-builder post-skeleton readiness operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_lev_builder_post_skeleton_readiness_operator import (
    build_a2_lev_builder_post_skeleton_readiness_report,
    run_a2_lev_builder_post_skeleton_readiness,
)
from system_v4.skills.skill_registry import SkillRegistry

SPEC_PATH = (
    REPO_ROOT
    / "system_v4/skill_specs/a2-lev-builder-post-skeleton-readiness-operator/SKILL.md"
)
EXPECTED_OPERATOR_PATH = (
    REPO_ROOT / "system_v4/skills/a2_lev_builder_post_skeleton_readiness_operator.py"
)
EXPECTED_SMOKE_PATH = (
    REPO_ROOT / "system_v4/skills/test_a2_lev_builder_post_skeleton_readiness_operator_smoke.py"
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    _assert(SPEC_PATH.exists(), f"missing spec file: {SPEC_PATH}")
    _assert(EXPECTED_SMOKE_PATH.exists(), f"missing smoke file: {EXPECTED_SMOKE_PATH}")

    spec_text = SPEC_PATH.read_text(encoding="utf-8")
    required_snippets = [
        "skill_id: a2-lev-builder-post-skeleton-readiness-operator",
        "name: a2-lev-builder-post-skeleton-readiness-operator",
        "Audit-only readiness operator that confirms the lev-builder post-skeleton slice is bounded",
        "can_write_repo: false",
        "can_only_propose: true",
        "reads_graph: true",
        "skeleton_report_path",
        "skeleton_packet_path",
        "lev_builder_post_skeleton_readiness_report",
        "lev_builder_post_skeleton_readiness_packet",
        "A2_LEV_BUILDER_POST_SKELETON_READINESS_REPORT__CURRENT__v1.json",
        "A2_LEV_BUILDER_POST_SKELETON_READINESS_REPORT__CURRENT__v1.md",
        "A2_LEV_BUILDER_POST_SKELETON_READINESS_PACKET__CURRENT__v1.json",
        "a2-lev-builder-formalization-skeleton-operator",
        "a2-lev-builder-formalization-proposal-operator",
        "a2-lev-builder-placement-audit-operator",
        "Do not claim migration permission, runtime-live status, formalization completion, or imported runtime ownership.",
        "Do not mutate files, registry, or runner surfaces from this slice.",
        "Keep the output explicit about what is bounded, ready, and still deferred.",
        "system_v4/skills/a2_lev_builder_post_skeleton_readiness_operator.py",
    ]
    for snippet in required_snippets:
        _assert(snippet in spec_text, f"missing required spec text: {snippet}")

    _assert(EXPECTED_OPERATOR_PATH.exists(), f"missing operator file: {EXPECTED_OPERATOR_PATH}")

    report, packet = build_a2_lev_builder_post_skeleton_readiness_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected readiness status: {report['status']}")
    _assert(report["audit_only"] is True, "readiness operator should stay audit-only")
    _assert(report["nonoperative"] is True, "readiness operator should stay nonoperative")
    _assert(report["do_not_promote"] is True, "readiness operator should stay non-promotable")
    _assert(report["readiness_only"] is True, "readiness operator should stay readiness-only")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::lev-formalization-placement",
        "unexpected post-skeleton cluster",
    )
    _assert(
        report["slice_id"] == "a2-lev-builder-post-skeleton-readiness-operator",
        "unexpected post-skeleton slice id",
    )
    _assert(
        report["admission_decision"] == "admit_for_selector_only",
        f"unexpected admission decision: {report['admission_decision']}",
    )
    _assert(
        report["gate"]["bounded_post_skeleton_ready"] is True,
        "readiness gate should be positively bounded on the live repo",
    )
    _assert(
        packet["next_step"] == "a2-lev-builder-post-skeleton-follow-on-selector-operator",
        f"unexpected next step: {packet['next_step']}",
    )
    _assert(packet["allow_registry_mutation"] is False, "packet must not allow registry mutation")
    _assert(packet["allow_runner_mutation"] is False, "packet must not allow runner mutation")
    _assert(packet["allow_graph_claims"] is False, "packet must not allow graph claims")
    _assert(packet["allow_runtime_claims"] is False, "packet must not allow runtime claims")
    _assert(packet["allow_a2_truth_update"] is False, "packet must not allow A2 truth update")
    _assert(packet["allow_migration"] is False, "packet must not allow migration")

    blocked_report, _ = build_a2_lev_builder_post_skeleton_readiness_report(
        REPO_ROOT,
        {
            "candidate": {
                "id": "too-wide-post-skeleton",
                "title": "runtime-import request",
                "type": "post_skeleton_readiness",
                "source": "test",
                "raw_input": "apply patch, migrate to production, update registry, update runner, and claim integration",
                "stage_request": "post_skeleton_readiness",
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
        "wide readiness request should force attention_required status",
    )
    _assert(
        blocked_report["gate"]["bounded_post_skeleton_ready"] is False,
        "wide readiness request should not pass the readiness gate",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "post-skeleton-readiness.json"
        md_path = Path(tmpdir) / "post-skeleton-readiness.md"
        packet_path = Path(tmpdir) / "post-skeleton-readiness.packet.json"
        emitted = run_a2_lev_builder_post_skeleton_readiness(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "readiness json was not written")
        _assert(md_path.exists(), "readiness markdown was not written")
        _assert(packet_path.exists(), "readiness packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_lev_builder_post_skeleton_readiness_operator.py": (
                lambda ctx: "a2-lev-builder-post-skeleton-readiness-operator-dispatch"
            ),
        }
    )
    readiness_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["post-skeleton-readiness"],
    )
    _assert(
        any(
            skill.skill_id == "a2-lev-builder-post-skeleton-readiness-operator"
            for skill in readiness_skills
        ),
        "post-skeleton readiness operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        readiness_skills,
        ["a2-lev-builder-post-skeleton-readiness-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-lev-builder-post-skeleton-readiness-operator",
        f"unexpected readiness selection: {selected}",
    )
    _assert(not fallback, "readiness operator unexpectedly fell back")
    _assert(dispatch is not None, "readiness operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected readiness reason: {reason}")

    print("PASS: a2 lev-builder post-skeleton readiness operator smoke")


if __name__ == "__main__":
    main()
