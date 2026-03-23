"""Smoke test for the TopoNetX projection adapter audit."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.toponetx_projection_adapter_audit import (
    build_toponetx_projection_adapter_report,
    run_toponetx_projection_adapter_audit,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_toponetx_projection_adapter_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected TopoNetX audit status: {report['status']}")

    projection = report["projection"]
    shape = projection["projection_shape"]
    _assert(shape["node_cell_count"] == 419, "expected low-control node count to remain 419")
    _assert(
        projection["admitted_relation_entry_count"] == 244,
        "expected admitted relation entry count to be 244",
    )
    _assert(shape["edge_cell_count"] == 200, "expected deduplicated TopoNetX edge count to be 200")
    _assert(shape["two_cell_count"] == 0, "canonical two-cell count should remain 0")
    _assert(
        projection["quarantined_relation_counts"].get("OVERLAPS", 0) == 614,
        "expected OVERLAPS quarantine count to remain 614",
    )
    _assert(
        projection["candidate_triangle_count"] >= 1,
        "expected at least one candidate triangle in the low-control sidecar",
    )
    _assert(packet["allow_read_only_projection"] is True, "TopoNetX packet should allow read-only projection")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "toponetx_projection.json"
        md_path = Path(tmpdir) / "toponetx_projection.md"
        packet_path = Path(tmpdir) / "toponetx_projection.packet.json"
        emitted = run_toponetx_projection_adapter_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "TopoNetX audit json was not written")
        _assert(md_path.exists(), "TopoNetX audit markdown was not written")
        _assert(packet_path.exists(), "TopoNetX audit packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected TopoNetX json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected TopoNetX md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected TopoNetX packet path")

    print("PASS: toponetx projection adapter audit smoke")


if __name__ == "__main__":
    main()
