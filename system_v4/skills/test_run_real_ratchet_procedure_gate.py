"""
Negative smoke for run_real_ratchet.py procedure gating.

This verifies the runner now refuses to improvise when the current queue says
`NO_WORK`, even if graph fuel exists.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_temp_workspace(root: Path) -> None:
    registry_src = WORKSPACE_ROOT / "system_v4" / "a1_state" / "skill_registry_v1.json"
    registry = json.loads(registry_src.read_text(encoding="utf-8"))
    _write_json(root / "system_v4" / "a1_state" / "skill_registry_v1.json", registry)

    _write_json(
        root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json",
        {"schema": "V4_SYSTEM_GRAPH_v1", "nodes": {}, "edges": []},
    )
    (root / "system_v4" / "runtime_state").mkdir(parents=True, exist_ok=True)

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
            "thread_class": "A2_CONTROLLER",
            "mode": "CONTROLLER_ONLY",
            "dispatch_rule": "substantive processing belongs in a bounded worker packet whenever a worker expression already exists",
            "stop_rule": "stop after one bounded controller action unless one exact worker dispatch is issued",
        },
    )
    _write_json(
        a2_state / "A1_QUEUE_STATUS_PACKET__CURRENT__TEST__v1.json",
        {
            "schema": "A1_QUEUE_STATUS_PACKET_v1",
            "queue_status": "NO_WORK",
            "reason": "no bounded A1 family slice is currently prepared",
        },
    )


def main() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="ratchet_gate_smoke_"))
    try:
        _build_temp_workspace(temp_root)

        env = dict(os.environ)
        env["RATCHET_REPO_ROOT"] = str(temp_root)
        env["PYTHONPATH"] = str(WORKSPACE_ROOT)

        proc = subprocess.run(
            [sys.executable, "-m", "system_v4.skills.run_real_ratchet", "--runtime-model=gemini"],
            cwd=str(WORKSPACE_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        print("run_real_ratchet procedure gate smoke")
        print(f"Temp root: {temp_root}")
        print(proc.stdout)
        if proc.stderr.strip():
            print(proc.stderr)

        _assert(proc.returncode == 2, f"expected exit code 2, got {proc.returncode}")
        _assert("RESULT: FAIL_CLOSED" in proc.stdout, "expected FAIL_CLOSED gate result")
        _assert("A1 queue not ready" in proc.stdout, "expected A1 queue gate error")
        print("PASS: run_real_ratchet fails closed when the current queue is NO_WORK")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
