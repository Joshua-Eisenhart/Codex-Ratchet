"""Smoke test for the bounded PyG heterograph projection audit."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.pyg_heterograph_projection_audit import (
    build_pyg_heterograph_projection_report,
    run_pyg_heterograph_projection_audit,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_pyg_heterograph_projection_report(REPO_ROOT)
    if report["status"] == "blocked_missing_tool":
        print("SKIP: PyG heterograph projection audit blocked_missing_tool in current interpreter")
        return

    _assert(report["status"] == "ok", f"unexpected projection status: {report['status']}")
    _assert(
        report["projection_focus"] == "read_only_control_subgraph",
        "unexpected projection focus",
    )
    _assert(
        report["low_control_probe_status"]["node_count"] == 419,
        "unexpected low-control probe node count",
    )
    _assert(
        report["low_control_probe_status"]["is_sufficient_alone"] is False,
        "low-control probe should not be treated as sufficient alone",
    )
    _assert(packet["allow_training"] is False, "projection packet must not allow training yet")
    _assert(
        packet["allow_canonical_graph_replacement"] is False,
        "projection packet must not allow canonical graph replacement",
    )
    _assert(
        report["pyg_summary"]["node_store_count"] >= 4,
        "expected multiple node stores in the PyG projection",
    )
    _assert(
        report["pyg_summary"]["edge_store_count"] >= 4,
        "expected multiple edge stores in the PyG projection",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "pyg_projection.json"
        md_path = Path(tmpdir) / "pyg_projection.md"
        packet_path = Path(tmpdir) / "pyg_projection.packet.json"
        emitted = run_pyg_heterograph_projection_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "projection json was not written")
        _assert(md_path.exists(), "projection markdown was not written")
        _assert(packet_path.exists(), "projection packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected projection json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected projection md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected projection packet path")

    print("PASS: pyg heterograph projection audit smoke")


if __name__ == "__main__":
    main()
