"""Reproduce a nested input escaping ConstraintBoxController without a record."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from constraintbox.contracts import TaskRequest
from constraintbox.controller import (
    AgentProposalProfile,
    ConstraintBoxController,
    FiniteConstraintProfile,
    StrictJsonProfile,
)
from constraintbox.ledger import HashChainLedger


PROFILES = {
    "strict": StrictJsonProfile,
    "proposal": AgentProposalProfile,
    "finite": FiniteConstraintProfile,
}


def _line_count(path: Path) -> int:
    return len(path.read_bytes().splitlines()) if path.exists() else 0


def _payload(depth: int) -> bytes:
    return b'{"a":' + b"[" * depth + b"]" * depth + b"}"


def reproduce(control_depth: int = 200, deep_depth: int = 2000) -> dict[str, Any]:
    temp = Path(tempfile.mkdtemp(prefix="claimgate-e5-controller-"))
    controls: dict[str, dict[str, Any]] = {}
    deep: dict[str, dict[str, Any]] = {}
    try:
        for profile_id, profile_type in PROFILES.items():
            ledger_path = temp / f"{profile_id}.jsonl"
            controller = ConstraintBoxController(
                {
                    "strict": StrictJsonProfile(),
                    "proposal": AgentProposalProfile(),
                    "finite": FiniteConstraintProfile(),
                },
                temp / "runs",
                HashChainLedger(ledger_path),
                max_payload_bytes=1_048_576,
            )

            before = _line_count(ledger_path)
            control_record = controller.run(
                TaskRequest(
                    request_id=f"e5-control-{profile_id}",
                    task_kind=profile_id,
                    payload=_payload(control_depth),
                )
            )
            controls[profile_id] = {
                "disposition": getattr(control_record, "disposition", None),
                "record_built": control_record is not None,
                "ledger_gained": _line_count(ledger_path) == before + 1,
            }

            before = _line_count(ledger_path)
            deep_record = None
            raised = None
            try:
                deep_record = controller.run(
                    TaskRequest(
                        request_id=f"e5-deep-{profile_id}",
                        task_kind=profile_id,
                        payload=_payload(deep_depth),
                    )
                )
            except Exception as exc:
                raised = type(exc).__name__
            deep[profile_id] = {
                "exception": raised,
                "record_built": deep_record is not None,
                "ledger_gained": _line_count(ledger_path) != before,
            }

        control_ok = all(
            row["record_built"]
            and row["disposition"] is not None
            and row["ledger_gained"]
            for row in controls.values()
        )
        deep_ok = all(
            row["exception"] == "RecursionError"
            and not row["record_built"]
            and not row["ledger_gained"]
            for row in deep.values()
        )
        admitted = control_ok and deep_ok
        return {
            "admitted": admitted,
            "control_depth": control_depth,
            "control_bytes": len(_payload(control_depth)),
            "deep_depth": deep_depth,
            "deep_bytes": len(_payload(deep_depth)),
            "controls": controls,
            "deep": deep,
        }
    finally:
        shutil.rmtree(temp)
