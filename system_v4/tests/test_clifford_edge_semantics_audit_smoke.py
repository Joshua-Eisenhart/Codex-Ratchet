"""Smoke test for clifford-edge-semantics audit."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.clifford_edge_semantics_audit import (
    build_clifford_edge_semantics_report,
    run_clifford_edge_semantics_audit,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_clifford_edge_semantics_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected clifford audit status: {report['status']}")
    _assert(report["math_sidecar_check"]["clifford"]["available"] is True, "clifford should be available")
    _assert(report["math_sidecar_check"]["kingdon"]["available"] is True, "kingdon should be available")
    _assert(packet["allow_read_only_ga_sidecar"] is True, "GA sidecar should be read-only allowed")
    _assert(packet["allow_training"] is False, "GA packet must not allow training")
    payload_truth = report["edge_payload_truth"]
    _assert(payload_truth["all_attr_keys"]["link_type"] == 144, "unexpected link_type attr count")
    _assert(payload_truth["relation_attr_counts"]["OVERLAPS"]["shared_tokens"] == 614, "unexpected overlaps shared_tokens count")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "clifford_audit.json"
        md_path = Path(tmpdir) / "clifford_audit.md"
        packet_path = Path(tmpdir) / "clifford_audit.packet.json"
        emitted = run_clifford_edge_semantics_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "clifford audit json was not written")
        _assert(md_path.exists(), "clifford audit markdown was not written")
        _assert(packet_path.exists(), "clifford audit packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected clifford audit json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected clifford audit md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected clifford audit packet path")

    print("PASS: clifford edge semantics audit smoke")


if __name__ == "__main__":
    main()
