"""Smoke test for durable EverMem witness sync state."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import system_v4.skills.witness_evermem_sync as witness_sync_module
from system_v4.skills.witness_evermem_sync import run_witness_sync


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _witness_entry(kind: str, note: str) -> dict[str, object]:
    return {
        "recorded_at": "2026-03-21T00:00:00Z",
        "witness": {
            "kind": kind,
            "trace": [{"notes": [note]}],
            "violations": [],
        },
        "tags": {"source": "test"},
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        witness_path = tmp / "witness.json"
        state_path = tmp / "sync_state.json"
        report_json = tmp / "sync_report.json"
        report_md = tmp / "sync_report.md"
        witness_path.write_text(
            json.dumps(
                [
                    _witness_entry("intent", "first"),
                    _witness_entry("context", "second"),
                    _witness_entry("positive", "third"),
                ]
            ),
            encoding="utf-8",
        )
        request_log: list[str] = []
        fail_once_for = {"witness_000001"}
        failed_once: set[str] = set()
        original_store = witness_sync_module.EverMemClient.store_memory_result

        def fake_store(self, msg_id, sender, content, memory_types=None):
            request_log.append(msg_id)
            if msg_id in fail_once_for and msg_id not in failed_once:
                failed_once.add(msg_id)
                return {
                    "success": False,
                    "status_code": 503,
                    "error": "HTTPError: 503",
                    "body": {"error": "transient failure"},
                    "message_id": msg_id,
                }
            return {
                "success": True,
                "status_code": 201,
                "error": "",
                "body": {"ok": True},
                "message_id": msg_id,
            }

        witness_sync_module.EverMemClient.store_memory_result = fake_store
        try:
            first = run_witness_sync(
                {
                    "witness_path": str(witness_path),
                    "state_path": str(state_path),
                    "report_json_path": str(report_json),
                    "report_md_path": str(report_md),
                    "evermem_url": "http://test-evermem/api/v1",
                    "timeout_seconds": 1.0,
                }
            )
            _assert(first["previous_idx"] == 0, "first run previous_idx mismatch")
            _assert(first["new_idx"] == 1, "first run should only advance through contiguous success")
            _assert(first["synced"] == 1, "first run synced count mismatch")
            _assert(first["status"] == "partial_failure", "first run should stop on partial failure")
            _assert(first["first_error"], "first run should record an error")
            _assert(state_path.exists(), "state file not written")
            state_after_first = json.loads(state_path.read_text(encoding="utf-8"))
            _assert(state_after_first["last_sync_idx"] == 1, "state did not persist contiguous cursor")
            _assert(
                request_log == ["witness_000000", "witness_000001"],
                "unexpected request order on first run",
            )

            second = run_witness_sync(
                {
                    "witness_path": str(witness_path),
                    "state_path": str(state_path),
                    "report_json_path": str(report_json),
                    "report_md_path": str(report_md),
                    "evermem_url": "http://test-evermem/api/v1",
                    "timeout_seconds": 1.0,
                }
            )
            _assert(second["previous_idx"] == 1, "second run should resume from persisted cursor")
            _assert(second["new_idx"] == 3, "second run should finish remaining witnesses")
            _assert(second["synced"] == 2, "second run synced count mismatch")
            _assert(second["status"] == "ok", "second run should complete cleanly")
            state_after_second = json.loads(state_path.read_text(encoding="utf-8"))
            _assert(state_after_second["last_sync_idx"] == 3, "final sync cursor mismatch")
            _assert(
                request_log == [
                    "witness_000000",
                    "witness_000001",
                    "witness_000001",
                    "witness_000002",
                ],
                "resume should retry the failed witness and then continue",
            )
            _assert(report_json.exists(), "report json not written")
            _assert(report_md.exists(), "report md not written")

            missing_result = run_witness_sync(
                {
                    "witness_path": str(tmp / "missing_witness.json"),
                    "last_sync_idx": 5,
                    "state_path": str(tmp / "missing_state.json"),
                    "report_json_path": str(tmp / "missing_report.json"),
                    "report_md_path": str(tmp / "missing_report.md"),
                    "evermem_url": "http://test-evermem/api/v1",
                    "timeout_seconds": 1.0,
                }
            )
            _assert(missing_result["previous_idx"] == 5, "missing witness path should preserve prior cursor")
            _assert(missing_result["new_idx"] == 5, "missing witness path should not rewind cursor")
            _assert(missing_result["synced"] == 0, "missing witness path should not sync entries")
            _assert(missing_result["attempted_count"] == 0, "missing witness path should not attempt requests")
            _assert(
                missing_result["status"] == "missing_witness_path",
                "missing witness path should produce explicit missing status",
            )
        finally:
            witness_sync_module.EverMemClient.store_memory_result = original_store

    print("PASS: witness evermem sync durability smoke")


if __name__ == "__main__":
    main()
