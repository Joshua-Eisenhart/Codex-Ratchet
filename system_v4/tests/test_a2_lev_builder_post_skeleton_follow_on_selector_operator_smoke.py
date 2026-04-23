"""Smoke test for the bounded lev-builder post-skeleton follow-on selector operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_lev_builder_post_skeleton_follow_on_selector_operator import (
    build_a2_lev_builder_post_skeleton_follow_on_selector_report,
    run_a2_lev_builder_post_skeleton_follow_on_selector,
)

SPEC_PATH = (
    REPO_ROOT
    / "system_v4/skill_specs/a2-lev-builder-post-skeleton-follow-on-selector-operator/SKILL.md"
)
EXPECTED_OPERATOR_PATH = (
    REPO_ROOT / "system_v4/skills/a2_lev_builder_post_skeleton_follow_on_selector_operator.py"
)
EXPECTED_SMOKE_PATH = (
    REPO_ROOT / "system_v4/skills/test_a2_lev_builder_post_skeleton_follow_on_selector_operator_smoke.py"
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    _assert(SPEC_PATH.exists(), f"missing spec file: {SPEC_PATH}")
    _assert(EXPECTED_OPERATOR_PATH.exists(), f"missing operator file: {EXPECTED_OPERATOR_PATH}")
    _assert(EXPECTED_SMOKE_PATH.exists(), f"missing smoke file: {EXPECTED_SMOKE_PATH}")

    spec_text = SPEC_PATH.read_text(encoding="utf-8")
    required_snippets = [
        "skill_id: a2-lev-builder-post-skeleton-follow-on-selector-operator",
        "name: a2-lev-builder-post-skeleton-follow-on-selector-operator",
        "Selector-only post-skeleton follow-on operator",
        "readiness_report_path",
        "readiness_packet_path",
        "skeleton_report_path",
        "skeleton_packet_path",
        "lev_builder_post_skeleton_follow_on_selector_report",
        "lev_builder_post_skeleton_follow_on_selector_packet",
        "A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.json",
        "A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_REPORT__CURRENT__v1.md",
        "A2_LEV_BUILDER_POST_SKELETON_FOLLOW_ON_SELECTOR_PACKET__CURRENT__v1.json",
        "a2-lev-builder-post-skeleton-readiness-operator",
        "a2-lev-builder-formalization-skeleton-operator",
        "Do not mutate registry or runner surfaces from this slice.",
        "Keep the follow-on choice explicit, bounded, and repo-held.",
    ]
    for snippet in required_snippets:
        _assert(snippet in spec_text, f"missing required spec text: {snippet}")

    report, packet = build_a2_lev_builder_post_skeleton_follow_on_selector_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected selector status: {report['status']}")
    _assert(report["audit_only"] is True, "selector should stay audit-only")
    _assert(report["nonoperative"] is True, "selector should stay nonoperative")
    _assert(report["selector_only"] is True, "selector should stay selector-only")
    _assert(report["non_migratory"] is True, "selector should stay non-migratory")
    _assert(report["do_not_promote"] is True, "selector should stay non-promotable")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::lev-formalization-placement",
        "unexpected selector cluster id",
    )
    _assert(
        report["slice_id"] == "a2-lev-builder-post-skeleton-follow-on-selector-operator",
        "unexpected selector slice id",
    )
    _assert(
        report["gate_status"] == "follow_on_selection_ready",
        f"unexpected gate status: {report['gate_status']}",
    )
    _assert(
        report["selected_follow_on_id"] == "post_skeleton_follow_on_unresolved",
        f"unexpected selected follow-on: {report['selected_follow_on_id']}",
    )
    _assert(
        report["selected_follow_on"].get("follow_on_id") == "post_skeleton_follow_on_unresolved",
        "selector did not choose the expected unresolved branch",
    )
    _assert(packet["next_step"] == "post_skeleton_follow_on_unresolved", "unexpected packet next step")
    _assert(packet["allow_registry_mutation"] is False, "packet must not allow registry mutation")
    _assert(packet["allow_runner_mutation"] is False, "packet must not allow runner mutation")
    _assert(packet["allow_runtime_claims"] is False, "packet must not allow runtime claims")
    _assert(packet["allow_migration"] is False, "packet must not allow migration")

    blocked_report, blocked_packet = build_a2_lev_builder_post_skeleton_follow_on_selector_report(
        REPO_ROOT,
        {
            "candidate": {
                "id": "too-wide-selector",
                "title": "runtime-import request",
                "type": "post_skeleton_follow_on_selection",
                "source": "test",
                "raw_input": "apply patch, migrate to production, update registry, update runner, and claim runtime-live",
                "stage_request": "post_skeleton_follow_on_selection",
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
        "wide selector request should force attention_required status",
    )
    _assert(
        blocked_report["gate_status"] == "hold_blocked",
        "wide selector request should not pass the selector gate",
    )
    _assert(
        blocked_report["selected_follow_on_id"] == "hold_at_scaffold",
        "blocked selector request should hold at scaffold",
    )
    _assert(
        blocked_packet["next_step"] == "hold_at_scaffold",
        "blocked packet should hold at scaffold",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "follow-on-selector.json"
        md_path = Path(tmpdir) / "follow-on-selector.md"
        packet_path = Path(tmpdir) / "follow-on-selector.packet.json"
        emitted = run_a2_lev_builder_post_skeleton_follow_on_selector(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "selector json was not written")
        _assert(md_path.exists(), "selector markdown was not written")
        _assert(packet_path.exists(), "selector packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected packet path")

    print("PASS: a2 lev-builder post-skeleton follow-on selector operator smoke")


if __name__ == "__main__":
    main()
