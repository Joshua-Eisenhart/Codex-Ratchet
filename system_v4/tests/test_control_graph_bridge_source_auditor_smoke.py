"""Smoke test for the control graph bridge-source auditor."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.control_graph_bridge_source_auditor import (
    build_control_graph_bridge_source_report,
    run_control_graph_bridge_source_audit,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_control_graph_bridge_source_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected bridge-source status: {report['status']}")

    rows = {row["bridge_family"]: row for row in report["bridge_source_rows"]}
    _assert(
        rows["SKILL -> KERNEL_CONCEPT"]["derivation_status"] == "heuristic_only",
        "skill->kernel should still be heuristic-only",
    )
    _assert(
        rows["B_SURVIVOR -> KERNEL_CONCEPT"]["derivation_status"] == "partial_property_trace",
        "survivor->kernel should be partial_property_trace",
    )
    _assert(
        rows["SIM_EVIDENCED -> KERNEL_CONCEPT"]["derivation_status"] == "chain_partial",
        "sim->kernel should be chain_partial",
    )
    _assert(
        rows["B_OUTCOME -> KERNEL_CONCEPT"]["derivation_status"] == "not_derivable_now",
        "b_outcome->kernel should not be derivable now",
    )
    _assert(packet["allow_training"] is False, "bridge-source packet must not allow training")
    _assert(
        "toponetx-projection-adapter-audit" in packet["recommended_next_slice_ids"],
        "TopoNetX follow-on should be recommended",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "bridge_source.json"
        md_path = Path(tmpdir) / "bridge_source.md"
        packet_path = Path(tmpdir) / "bridge_source.packet.json"
        emitted = run_control_graph_bridge_source_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "bridge-source json was not written")
        _assert(md_path.exists(), "bridge-source markdown was not written")
        _assert(packet_path.exists(), "bridge-source packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected bridge-source json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected bridge-source md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected bridge-source packet path")

    print("PASS: control graph bridge-source auditor smoke")


if __name__ == "__main__":
    main()
