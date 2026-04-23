"""Smoke test for survivor-kernel bridge backfill audit."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.survivor_kernel_bridge_backfill_audit import (
    build_survivor_kernel_bridge_backfill_report,
    run_survivor_kernel_bridge_backfill_audit,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_survivor_kernel_bridge_backfill_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected survivor backfill status: {report['status']}")
    _assert(report["allow_direct_kernel_backfill_now"] is False, "direct kernel backfill should currently fail closed")
    counts = report["survivor_source_class_counts"]
    _assert(counts["live_kernel_already_linked"] == 1, "expected one already-linked kernel survivor")
    _assert(counts["live_nonkernel_already_linked::EXTRACTED_CONCEPT"] == 34, "unexpected extracted count")
    _assert(counts["live_nonkernel_already_linked::REFINED_CONCEPT"] == 12, "unexpected refined count")
    _assert(counts["blank_source_concept_id"] == 31, "unexpected blank source count")
    _assert(report["direct_kernel_backfill_candidate_count"] == 0, "expected zero direct kernel backfill candidates")
    _assert(packet["allow_training"] is False, "packet must not allow training")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "survivor_backfill.json"
        md_path = Path(tmpdir) / "survivor_backfill.md"
        packet_path = Path(tmpdir) / "survivor_backfill.packet.json"
        emitted = run_survivor_kernel_bridge_backfill_audit(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "survivor backfill json was not written")
        _assert(md_path.exists(), "survivor backfill markdown was not written")
        _assert(packet_path.exists(), "survivor backfill packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected survivor backfill json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected survivor backfill md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected survivor backfill packet path")

    print("PASS: survivor kernel bridge backfill audit smoke")


if __name__ == "__main__":
    main()
