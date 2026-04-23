"""Smoke test for edge payload schema audit."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.edge_payload_schema_audit import (
    build_edge_payload_schema_report,
    run_edge_payload_schema_audit,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_edge_payload_schema_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected edge schema status: {report['status']}")
    _assert(packet["allow_sidecar_schema_only"] is True, "schema must remain sidecar-only")
    _assert("OVERLAPS" in packet["forbidden_relations"], "OVERLAPS should remain forbidden")
    rows = {row["relation"]: row for row in report["schema_rows"]}
    _assert(rows["STRUCTURALLY_RELATED"]["optional_scalar_carriers"] == ["shared_components"], "unexpected STRUCTURALLY_RELATED scalar carriers")
    _assert(rows["RELATED_TO"]["optional_scalar_carriers"] == ["shared_count"], "unexpected RELATED_TO scalar carriers")
    _assert(rows["DEPENDS_ON"]["optional_scalar_carriers"] == [], "DEPENDS_ON should have no current numeric scalar carriers")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "edge_schema.json"
        md_path = Path(tmpdir) / "edge_schema.md"
        packet_path = Path(tmpdir) / "edge_schema.packet.json"
        emitted = run_edge_payload_schema_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "edge schema json was not written")
        _assert(md_path.exists(), "edge schema markdown was not written")
        _assert(packet_path.exists(), "edge schema packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected edge schema json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected edge schema md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected edge schema packet path")

    print("PASS: edge payload schema audit smoke")


if __name__ == "__main__":
    main()
