"""Smoke test for skill-kernel link seeding policy audit."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.skill_kernel_link_seeding_policy_audit import (
    build_skill_kernel_link_seeding_policy_report,
    run_skill_kernel_link_seeding_policy_audit,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_skill_kernel_link_seeding_policy_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected seeding policy status: {report['status']}")
    _assert(report["allow_auto_seeding_now"] is False, "skill-kernel auto-seeding should currently fail closed")
    _assert(report["registry_row_count"] == 110, "expected 110 registry rows")
    _assert(report["skill_node_count"] == 110, "expected 110 skill graph nodes")
    _assert(report["registry_concept_field_hits"] == 0, "expected no registry concept fields")
    _assert(report["skill_property_concept_field_hits"] == 0, "expected no skill property concept fields")
    edge_counts = report["skill_edge_family_counts"]
    _assert(edge_counts["RELATED_TO::SKILL"] == 246, "unexpected skill RELATED_TO count")
    _assert(edge_counts["SKILL_FOLLOWS::SKILL"] == 12, "unexpected skill FOLLOWS count")
    _assert(packet["allow_training"] is False, "packet must not allow training")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "skill_policy.json"
        md_path = Path(tmpdir) / "skill_policy.md"
        packet_path = Path(tmpdir) / "skill_policy.packet.json"
        emitted = run_skill_kernel_link_seeding_policy_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "skill policy json was not written")
        _assert(md_path.exists(), "skill policy markdown was not written")
        _assert(packet_path.exists(), "skill policy packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected skill policy json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected skill policy md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected skill policy packet path")

    print("PASS: skill kernel link seeding policy audit smoke")


if __name__ == "__main__":
    main()
