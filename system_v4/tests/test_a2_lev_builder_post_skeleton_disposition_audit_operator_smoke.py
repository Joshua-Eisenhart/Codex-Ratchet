"""Smoke test for the bounded lev-builder post-skeleton disposition audit operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_lev_builder_post_skeleton_disposition_audit_operator import (
    build_a2_lev_builder_post_skeleton_disposition_audit_report,
    run_a2_lev_builder_post_skeleton_disposition_audit,
)

SPEC_PATH = (
    REPO_ROOT
    / "system_v4/skill_specs/a2-lev-builder-post-skeleton-disposition-audit-operator/SKILL.md"
)
EXPECTED_OPERATOR_PATH = (
    REPO_ROOT / "system_v4/skills/a2_lev_builder_post_skeleton_disposition_audit_operator.py"
)
EXPECTED_SMOKE_PATH = (
    REPO_ROOT / "system_v4/skills/test_a2_lev_builder_post_skeleton_disposition_audit_operator_smoke.py"
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
        "skill_id: a2-lev-builder-post-skeleton-disposition-audit-operator",
        "name: a2-lev-builder-post-skeleton-disposition-audit-operator",
        "Audit-only post-skeleton disposition operator",
        "selector_report_path",
        "selector_packet_path",
        "readiness_report_path",
        "lev_builder_post_skeleton_disposition_audit_report",
        "lev_builder_post_skeleton_disposition_audit_packet",
        "A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_REPORT__CURRENT__v1.json",
        "A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_REPORT__CURRENT__v1.md",
        "A2_LEV_BUILDER_POST_SKELETON_DISPOSITION_AUDIT_PACKET__CURRENT__v1.json",
        "a2-lev-builder-post-skeleton-follow-on-selector-operator",
        "Do not widen the audit into completeness, execution readiness, or patch application.",
    ]
    for snippet in required_snippets:
        _assert(snippet in spec_text, f"missing required spec text: {snippet}")

    report, packet = build_a2_lev_builder_post_skeleton_disposition_audit_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected audit status: {report['status']}")
    _assert(report["audit_only"] is True, "disposition audit should stay audit-only")
    _assert(report["nonoperative"] is True, "disposition audit should stay nonoperative")
    _assert(report["do_not_promote"] is True, "disposition audit should stay non-promotable")
    _assert(
        report["gate_status"] == "disposition_ready",
        f"unexpected gate status: {report['gate_status']}",
    )
    _assert(
        report["disposition"] == "retain_unresolved_branch",
        f"unexpected disposition: {report['disposition']}",
    )
    _assert(
        report["recommended_next_step"] == "a2-lev-builder-post-skeleton-future-lane-existence-audit-operator",
        "unexpected next step for disposition audit",
    )
    _assert(
        report["selected_branch_under_audit"] == "post_skeleton_follow_on_unresolved",
        "unexpected selected branch under audit",
    )
    _assert(packet["allow_runtime_claims"] is False, "packet must not allow runtime claims")
    _assert(packet["allow_migration"] is False, "packet must not allow migration")
    _assert(
        packet["next_step"] == "a2-lev-builder-post-skeleton-future-lane-existence-audit-operator",
        "unexpected packet next step",
    )

    blocked_report, blocked_packet = build_a2_lev_builder_post_skeleton_disposition_audit_report(
        REPO_ROOT,
        {
            "candidate": {
                "id": "too-wide-disposition",
                "title": "runtime-import request",
                "type": "post_skeleton_disposition_audit",
                "source": "test",
                "raw_input": "claim runtime-live, formalization complete, update registry, and migrate to production",
                "stage_request": "post_skeleton_disposition_audit",
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
        "wide disposition request should force attention_required status",
    )
    _assert(
        blocked_report["gate_status"] == "hold_at_selector",
        "wide disposition request should not pass the gate",
    )
    _assert(
        blocked_packet["next_step"] == "hold_at_selector",
        "blocked packet should hold at selector",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "disposition-audit.json"
        md_path = Path(tmpdir) / "disposition-audit.md"
        packet_path = Path(tmpdir) / "disposition-audit.packet.json"
        emitted = run_a2_lev_builder_post_skeleton_disposition_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "audit json was not written")
        _assert(md_path.exists(), "audit markdown was not written")
        _assert(packet_path.exists(), "audit packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected packet path")

    print("PASS: a2 lev-builder post-skeleton disposition audit operator smoke")


if __name__ == "__main__":
    main()
