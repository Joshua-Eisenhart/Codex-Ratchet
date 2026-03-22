"""Smoke test for recording a current runtime/control context snapshot."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from system_v4.skills.runtime_context_snapshot import record_current_runtime_context


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_runtime_context_snapshot_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        a2_state = root / "system_v3" / "a2_state"
        _write_json(
            a2_state / "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__TEST__v1.json",
            {
                "schema": "A2_CONTROLLER_LAUNCH_SPINE_v1",
                "launch_gate_status": "LAUNCH_READY",
                "mode": "CONTROLLER_ONLY",
                "current_a1_queue_status": "A1_QUEUE_STATUS: NO_WORK",
            },
        )
        _write_json(
            a2_state / "A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__TEST__v1.json",
            {
                "schema": "A2_CONTROLLER_LAUNCH_HANDOFF_v1",
                "mode": "CONTROLLER_ONLY",
            },
        )
        _write_json(
            a2_state / "A1_QUEUE_STATUS_PACKET__CURRENT__TEST__v1.json",
            {
                "schema": "A1_QUEUE_STATUS_PACKET_v1",
                "queue_status": "NO_WORK",
                "dispatch_id": "A1_DISPATCH__TEST__v1",
                "target_a1_role": "A1_PROPOSAL",
                "ready_packet_json": "system_v3/a2_state/A1_WORKER_LAUNCH_PACKET__CURRENT__TEST__v1.json",
            },
        )

        result = record_current_runtime_context(td)
        assert result["recorded"] is True

        witness_path = root / "system_v4" / "a2_state" / "witness_corpus_v1.json"
        corpus = json.loads(witness_path.read_text(encoding="utf-8"))
        assert len(corpus) == 1
        entry = corpus[0]
        assert entry["witness"]["kind"] == "context"
        assert entry["tags"]["topic"] == "queue_controller_state"
        note = entry["witness"]["trace"][0]["notes"][0]
        assert "A1 queue status=NO_WORK." in note
        assert "Dispatch ID=A1_DISPATCH__TEST__v1." in note

    print("PASS: test_runtime_context_snapshot_smoke")


if __name__ == "__main__":
    test_runtime_context_snapshot_smoke()
