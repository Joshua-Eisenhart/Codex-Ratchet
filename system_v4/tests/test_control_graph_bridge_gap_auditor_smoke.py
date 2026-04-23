"""Smoke test for the control graph bridge-gap auditor."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.control_graph_bridge_gap_auditor import (
    build_control_graph_bridge_gap_report,
    run_control_graph_bridge_gap_audit,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_control_graph_bridge_gap_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected bridge-gap status: {report['status']}")
    _assert(
        report["bridge_summary"]["missing_bridge_family_count"] >= 1,
        "expected at least one missing bridge family",
    )

    bridge_rows = {(row["source_type"], row["target_type"]): row for row in report["bridge_rows"]}
    _assert(
        bridge_rows[("SKILL", "KERNEL_CONCEPT")]["bridge_status"] == "missing",
        "skill->kernel should currently be missing",
    )
    _assert(
        bridge_rows[("SIM_EVIDENCED", "B_SURVIVOR")]["bridge_status"] == "present",
        "sim->survivor should currently be present",
    )
    _assert(
        bridge_rows[("B_SURVIVOR", "KERNEL_CONCEPT")]["bridge_status"] == "weak_signal",
        "survivor->kernel should currently be a weak signal",
    )
    _assert(packet["allow_training"] is False, "bridge-gap packet must not allow training")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "bridge_gap.json"
        md_path = Path(tmpdir) / "bridge_gap.md"
        packet_path = Path(tmpdir) / "bridge_gap.packet.json"
        emitted = run_control_graph_bridge_gap_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "bridge-gap json was not written")
        _assert(md_path.exists(), "bridge-gap markdown was not written")
        _assert(packet_path.exists(), "bridge-gap packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected bridge-gap json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected bridge-gap md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected bridge-gap packet path")

    print("PASS: control graph bridge-gap auditor smoke")


if __name__ == "__main__":
    main()
