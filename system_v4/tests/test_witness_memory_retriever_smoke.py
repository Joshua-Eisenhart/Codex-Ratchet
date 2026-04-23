"""Smoke test for the bounded witness memory retriever."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.witness_memory_retriever import (  # noqa: E402
    build_witness_memory_retriever_report,
    run_witness_memory_retriever,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        witness_path = root / "system_v4/a2_state/witness_corpus_v1.json"
        sync_report_path = root / "system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json"
        _write_json(
            witness_path,
            {
                "entries": [
                    {
                        "recorded_at": "2026-03-21T00:00:00Z",
                        "witness": {
                            "kind": "intent",
                            "passed": True,
                            "trace": [
                                {
                                    "notes": [
                                        "Bounded witness seam retrieval should stay narrow and source-bound."
                                    ]
                                }
                            ],
                        },
                        "tags": {"topic": "witness seam", "phase": "TEST"},
                    }
                ]
            },
        )
        _write_json(sync_report_path, {"status": "ok"})

        fake_result = {
            "success": True,
            "status_code": 200,
            "error": "",
            "memories": [
                {
                    "memory_id": "mem_001",
                    "score": 0.91,
                    "content": "bounded witness seam retrieval result",
                    "sender": "ratchet",
                }
            ],
        }
        with mock.patch(
            "system_v4.skills.witness_memory_retriever.EverMemClient.search_result",
            return_value=fake_result,
        ):
            report, packet = build_witness_memory_retriever_report(
                root,
                {
                    "witness_path": str(witness_path),
                    "sync_report_path": str(sync_report_path),
                },
            )
            _assert(report["status"] == "ok", f"unexpected status: {report['status']}")
            _assert(report["query_source"] == "latest_witness_trace", f"unexpected query source: {report['query_source']}")
            _assert(report["retrieval"]["memory_count"] == 1, "expected one returned memory")
            _assert(report["gate"]["allow_bootstrap_claims"] is False, "bootstrap claims must stay false")
            _assert(packet["next_step"] == "evaluate_bootstrap_unresolved", f"unexpected next step: {packet['next_step']}")

            json_path = root / "witness_retriever.json"
            md_path = root / "witness_retriever.md"
            packet_path = root / "witness_retriever.packet.json"
            emitted = run_witness_memory_retriever(
                {
                    "repo_root": str(root),
                    "witness_path": str(witness_path),
                    "sync_report_path": str(sync_report_path),
                    "report_json_path": str(json_path),
                    "report_md_path": str(md_path),
                    "packet_path": str(packet_path),
                }
            )
            _assert(json_path.exists(), "report json was not written")
            _assert(md_path.exists(), "report markdown was not written")
            _assert(packet_path.exists(), "packet json was not written")
            _assert(emitted["report_json_path"] == str(json_path), "unexpected report path")

    print("PASS: witness memory retriever smoke")


if __name__ == "__main__":
    main()
