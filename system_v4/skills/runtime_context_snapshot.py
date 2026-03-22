"""
runtime_context_snapshot.py

Capture the current controller/queue/runtime state as a first-class CONTEXT
witness, even when the live runner is not currently executing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from system_v4.skills.witness_recorder import WitnessRecorder


WITNESS_REL_PATH = "system_v4/a2_state/witness_corpus_v1.json"


def _latest_current_json(state_dir: Path, pattern: str) -> Optional[Path]:
    matches = sorted(state_dir.glob(pattern))
    return matches[-1] if matches else None


def _load_json(path: Optional[Path]) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def record_current_runtime_context(repo_root: str) -> dict[str, Any]:
    repo = Path(repo_root)
    a2_state = repo / "system_v3" / "a2_state"
    controller_spine_path = _latest_current_json(
        a2_state, "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__*.json"
    )
    controller_handoff_path = _latest_current_json(
        a2_state, "A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__*.json"
    )
    a1_queue_path = _latest_current_json(
        a2_state, "A1_QUEUE_STATUS_PACKET__CURRENT__*.json"
    )

    controller_spine = _load_json(controller_spine_path)
    controller_handoff = _load_json(controller_handoff_path)
    a1_queue = _load_json(a1_queue_path)

    queue_status = str(a1_queue.get("queue_status", ""))
    dispatch_id = str(a1_queue.get("dispatch_id", ""))
    target_role = str(a1_queue.get("target_a1_role", ""))
    gate_status = str(controller_spine.get("launch_gate_status", ""))
    handoff_mode = str(controller_handoff.get("mode", ""))
    ready_packet = str(a1_queue.get("ready_packet_json", ""))

    context_text = (
        f"Controller gate={gate_status}. "
        f"Controller mode={handoff_mode}. "
        f"A1 queue status={queue_status}. "
        f"Dispatch ID={dispatch_id}. "
        f"Target role={target_role}. "
        f"Ready packet={ready_packet}."
    )

    recorder = WitnessRecorder(repo / WITNESS_REL_PATH)
    for entry in reversed(recorder.contexts()):
        note = ""
        trace = entry.get("witness", {}).get("trace", [])
        if trace and isinstance(trace[0], dict):
            notes = trace[0].get("notes", [])
            if notes:
                note = str(notes[0])
        if (
            note == context_text
            and entry.get("tags", {}).get("topic") == "queue_controller_state"
        ):
            return {
                "witness_path": WITNESS_REL_PATH,
                "recorded": False,
                "reason": "duplicate_current_snapshot",
                "queue_status": queue_status,
                "dispatch_id": dispatch_id,
            }

    recorder.record_context(
        context_text=context_text,
        source="system",
        tags={
            "phase": "CONTROL_SNAPSHOT",
            "topic": "queue_controller_state",
            "queue_status": queue_status,
            "dispatch_id": dispatch_id,
        },
    )
    total = recorder.flush()
    return {
        "witness_path": WITNESS_REL_PATH,
        "recorded": True,
        "queue_status": queue_status,
        "dispatch_id": dispatch_id,
        "total_witnesses": total,
    }


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    result = record_current_runtime_context(str(repo))
    assert "witness_path" in result
    print("PASS: runtime_context_snapshot self-test")
