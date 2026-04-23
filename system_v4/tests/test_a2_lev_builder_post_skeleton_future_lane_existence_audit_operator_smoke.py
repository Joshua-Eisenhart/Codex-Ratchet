"""Smoke test for the bounded lev-builder future-lane existence audit operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_lev_builder_post_skeleton_future_lane_existence_audit_operator import (
    build_a2_lev_builder_post_skeleton_future_lane_existence_audit_report,
    run_a2_lev_builder_post_skeleton_future_lane_existence_audit,
)

SPEC_PATH = (
    REPO_ROOT
    / "system_v4/skill_specs/a2-lev-builder-post-skeleton-future-lane-existence-audit-operator/SKILL.md"
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    _assert(SPEC_PATH.exists(), f"missing spec file: {SPEC_PATH}")
    spec_text = SPEC_PATH.read_text(encoding="utf-8")

    required_snippets = [
        "skill_id: a2-lev-builder-post-skeleton-future-lane-existence-audit-operator",
        "name: a2-lev-builder-post-skeleton-future-lane-existence-audit-operator",
        "repo-held governance artifact",
        "bounded future-lane existence surface",
        "A2_LEV_BUILDER_POST_SKELETON_FUTURE_LANE_EXISTENCE_AUDIT_REPORT__CURRENT__v1.json",
        "A2_LEV_BUILDER_POST_SKELETON_FUTURE_LANE_EXISTENCE_AUDIT_PACKET__CURRENT__v1.json",
        "A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_REPORT__CURRENT__v1.json",
        "A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_PACKET__CURRENT__v1.json",
        "lev-builder",
        "arch",
        "work",
        "Keep the slice non-migratory, non-runtime-live, and branch-governance-only.",
        "Do not mutate registry or runner surfaces from this slice.",
        "Keep the result explicit about whether the branch remains a repo-held future lane artifact.",
    ]
    for snippet in required_snippets:
        _assert(snippet in spec_text, f"missing required spec text: {snippet}")

    report, packet = build_a2_lev_builder_post_skeleton_future_lane_existence_audit_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected future-lane audit status: {report['status']}")
    _assert(
        report["gate_status"] == "future_lane_existence_audited",
        f"unexpected future-lane gate status: {report['gate_status']}",
    )
    _assert(report["audit_only"] is True, "future-lane audit should stay audit-only")
    _assert(report["branch_governance_only"] is True, "future-lane audit should stay governance-only")
    _assert(report["nonoperative"] is True, "future-lane audit should stay nonoperative")
    _assert(report["non_migratory"] is True, "future-lane audit should stay non-migratory")
    _assert(report["do_not_promote"] is True, "future-lane audit should stay non-promotable")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::lev-formalization-placement",
        "unexpected future-lane audit cluster id",
    )
    _assert(
        report["slice_id"] == "a2-lev-builder-post-skeleton-future-lane-existence-audit-operator",
        "unexpected future-lane audit slice id",
    )
    _assert(
        report["existence_decision"] == "future_lane_exists_as_governance_artifact",
        f"unexpected existence decision: {report['existence_decision']}",
    )
    _assert(report["future_lane_exists"] is True, "default future-lane audit should recognize the artifact")
    _assert(
        report["gate"]["safe_to_continue"] is False,
        "future-lane audit should not admit a further slice by default",
    )
    _assert(
        report["gate"]["allow_bounded_future_lane_audit"] is False,
        "future-lane audit should complete the bounded governance check instead of reopening it",
    )
    _assert(
        report["gate"]["recommended_next_step"] == "hold_at_disposition",
        f"unexpected gate next step: {report['gate']['recommended_next_step']}",
    )
    _assert(
        packet["allow_bounded_future_lane_audit"] is False,
        "packet should not reopen the bounded future-lane audit after completion",
    )
    _assert(packet["allow_migration"] is False, "future-lane packet must not allow migration")
    _assert(packet["allow_runtime_claims"] is False, "future-lane packet must not allow runtime claims")
    _assert(packet["next_step"] == "hold_at_disposition", f"unexpected packet next step: {packet['next_step']}")

    blocked_report, _ = build_a2_lev_builder_post_skeleton_future_lane_existence_audit_report(
        REPO_ROOT,
        {
            "candidate": {
                "id": "too-wide-future-lane",
                "title": "runtime lane request",
                "type": "post_skeleton_future_lane_existence_audit",
                "source": "test",
                "raw_input": "apply patch, migrate to production, update registry, and claim runtime-live",
                "stage_request": "post_skeleton_future_lane_existence_audit",
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
        "wide future-lane request should force attention_required status",
    )
    _assert(
        blocked_report["gate_status"] == "future_lane_existence_blocked",
        f"unexpected blocked gate status: {blocked_report['gate_status']}",
    )
    _assert(
        blocked_report["gate"]["future_lane_exists"] is False,
        "wide future-lane request should not pass the governance gate",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "future-lane-existence.json"
        md_path = Path(tmpdir) / "future-lane-existence.md"
        packet_path = Path(tmpdir) / "future-lane-existence.packet.json"
        emitted = run_a2_lev_builder_post_skeleton_future_lane_existence_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "future-lane audit json was not written")
        _assert(md_path.exists(), "future-lane audit markdown was not written")
        _assert(packet_path.exists(), "future-lane audit packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected future-lane report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected future-lane report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected future-lane packet path")

    print("PASS: a2 lev-builder post-skeleton future-lane existence audit operator smoke")


if __name__ == "__main__":
    main()
