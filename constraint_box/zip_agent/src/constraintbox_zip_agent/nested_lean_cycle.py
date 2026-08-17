"""A small, model-free parent -> child -> subchild ZIP execution.

This module is deliberately a fixture around the existing public ZIP runtime.
It does not add a second executor or alter the wire protocol.  The protocol's
manifest already supplies the direct-child allowlist and maximum depth; the
lineage member below makes the parent identity and observed depth explicit and
lets this demo refuse a packet whose nested topology was forged.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from typing import Any

from .protocol import (
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    sha256_bytes,
    strict_json_loads,
    validate_packet,
    validate_return_zip,
)
from .runtime import ExecutionResult, execute_packet


CLAIM_CEILING = "local_deterministic_zip_execution_only;not_model_execution;not_admission;not_release"
LINEAGE_PATH = "inputs/lineage.json"
SUBCHILD_JOB_ID = "nested-subchild"
CHILD_JOB_ID = "nested-child"
PARENT_JOB_ID = "nested-parent"


def _task(
    *,
    task_id: str,
    sequence: int,
    operation: str,
    inputs: list[str],
    outputs: list[str],
    depends_on: list[str] | None = None,
) -> bytes:
    return canonical_json_bytes(
        {
            "schema": "constraintbox.zip_task.v1",
            "task_id": task_id,
            "sequence": sequence,
            "operation": operation,
            "input_paths": inputs,
            "output_paths": outputs,
            "depends_on": depends_on or [],
            "parameters": {},
            "preload_files": [],
        }
    )


def _manifest(
    *,
    job_id: str,
    task_paths: list[str],
    outputs: list[str],
    operations: list[str],
    child_ids: list[str],
    depth: int,
) -> dict[str, Any]:
    return {
        "schema": "constraintbox.zip_job.v1",
        "job_id": job_id,
        "task_execution_order": task_paths,
        "required_output_file_list": outputs,
        "allowed_operations": sorted(set(operations)),
        "allowed_child_job_ids": child_ids,
        "max_child_depth": depth,
        "claim_ceiling": CLAIM_CEILING,
    }


def _lineage(*, job_id: str, parent_job_id: str | None, depth: int, child_ids: list[str]) -> bytes:
    return canonical_json_bytes(
        {
            "schema": "constraintbox.nested_lineage.v1",
            "job_id": job_id,
            "parent_job_id": parent_job_id,
            "depth": depth,
            "allowed_child_job_ids": child_ids,
        }
    )


def _entries(data: bytes) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
            return {
                info.filename: archive.read(info)
                for info in archive.infolist()
                if not info.is_dir()
            }
    except (zipfile.BadZipFile, OSError) as exc:
        raise ZipJobRefusal("REFUSE_NESTED_CHILD_ZIP_INVALID") from exc


def _lineage_from_packet(packet_bytes: bytes) -> tuple[Any, dict[str, bytes], dict[str, Any]]:
    packet = validate_packet(packet_bytes)
    try:
        raw = strict_json_loads(packet.members[LINEAGE_PATH], label=LINEAGE_PATH)
    except KeyError as exc:
        raise ZipJobRefusal("REFUSE_NESTED_LINEAGE_MISSING", packet.manifest.job_id) from exc
    if not isinstance(raw, dict) or raw.get("schema") != "constraintbox.nested_lineage.v1":
        raise ZipJobRefusal("REFUSE_NESTED_LINEAGE_INVALID", packet.manifest.job_id)
    return packet, packet.members, raw


@dataclass(frozen=True)
class NestedLeanCycle:
    """The exact bytes and expected lineage for one nested demo graph."""

    packet_bytes: bytes
    parent_job_id: str
    child_job_id: str
    subchild_job_id: str
    parent_depth: int = 0
    child_depth: int = 1
    subchild_depth: int = 2

    @property
    def packet_sha256(self) -> str:
        return sha256_bytes(self.packet_bytes)


@dataclass(frozen=True)
class NestedLeanExecution:
    cycle: NestedLeanCycle
    result: ExecutionResult
    retained_child_return_sha256: str
    retained_subchild_return_sha256: str


def build_nested_lean_cycle() -> NestedLeanCycle:
    """Build a deterministic parent -> child -> subchild packet tree."""

    subchild_task = "tasks/00_measure.task.json"
    subchild = build_packet(
        _manifest(
            job_id=SUBCHILD_JOB_ID,
            task_paths=[subchild_task],
            outputs=["output/payload.json"],
            operations=["text_sha256_v1"],
            child_ids=[],
            depth=0,
        ),
        {
            "00_RUN_ME_FIRST.md": b"Model-free nested ZIP subchild.\n",
            LINEAGE_PATH: _lineage(
                job_id=SUBCHILD_JOB_ID,
                parent_job_id=CHILD_JOB_ID,
                depth=2,
                child_ids=[],
            ),
            "inputs/payload.txt": b"nested probe payload\n",
            subchild_task: _task(
                task_id="measure-payload",
                sequence=0,
                operation="text_sha256_v1",
                inputs=["inputs/payload.txt"],
                outputs=["output/payload.json"],
            ),
        },
    )

    child_task = "tasks/00_run_subchild.task.json"
    child = build_packet(
        _manifest(
            job_id=CHILD_JOB_ID,
            task_paths=[child_task],
            outputs=["output/subchild.return.zip"],
            operations=["run_child_zip_v1"],
            child_ids=[SUBCHILD_JOB_ID],
            depth=1,
        ),
        {
            "00_RUN_ME_FIRST.md": b"Model-free nested ZIP child.\n",
            LINEAGE_PATH: _lineage(
                job_id=CHILD_JOB_ID,
                parent_job_id=PARENT_JOB_ID,
                depth=1,
                child_ids=[SUBCHILD_JOB_ID],
            ),
            "children/subchild.zip": subchild,
            child_task: _task(
                task_id="run-subchild",
                sequence=0,
                operation="run_child_zip_v1",
                inputs=["children/subchild.zip"],
                outputs=["output/subchild.return.zip"],
            ),
        },
    )

    parent_task = "tasks/00_run_child.task.json"
    parent = build_packet(
        _manifest(
            job_id=PARENT_JOB_ID,
            task_paths=[parent_task],
            outputs=["output/child.return.zip"],
            operations=["run_child_zip_v1"],
            child_ids=[CHILD_JOB_ID],
            depth=2,
        ),
        {
            "00_RUN_ME_FIRST.md": b"Model-free nested ZIP parent.\n",
            LINEAGE_PATH: _lineage(
                job_id=PARENT_JOB_ID,
                parent_job_id=None,
                depth=0,
                child_ids=[CHILD_JOB_ID],
            ),
            "children/child.zip": child,
            parent_task: _task(
                task_id="run-child",
                sequence=0,
                operation="run_child_zip_v1",
                inputs=["children/child.zip"],
                outputs=["output/child.return.zip"],
            ),
        },
    )
    return NestedLeanCycle(
        packet_bytes=parent,
        parent_job_id=PARENT_JOB_ID,
        child_job_id=CHILD_JOB_ID,
        subchild_job_id=SUBCHILD_JOB_ID,
    )


def validate_nested_lean_packet(packet_bytes: bytes) -> NestedLeanCycle:
    """Validate exact IDs, parent bindings, depths, and child allowlists."""

    raw_parent_members = _entries(packet_bytes)
    if "children/child.zip" not in raw_parent_members:
        raise ZipJobRefusal("REFUSE_NESTED_CHILD_PACKET_MISSING", CHILD_JOB_ID)
    parent, parent_members, parent_lineage = _lineage_from_packet(packet_bytes)
    if parent.manifest.job_id != PARENT_JOB_ID:
        raise ZipJobRefusal("REFUSE_NESTED_PARENT_ID", parent.manifest.job_id)
    if parent_lineage != {
        "schema": "constraintbox.nested_lineage.v1",
        "job_id": PARENT_JOB_ID,
        "parent_job_id": None,
        "depth": 0,
        "allowed_child_job_ids": [CHILD_JOB_ID],
    }:
        raise ZipJobRefusal("REFUSE_NESTED_PARENT_LINEAGE")
    if parent.manifest.allowed_child_job_ids != [CHILD_JOB_ID] or parent.manifest.max_child_depth != 2:
        raise ZipJobRefusal("REFUSE_NESTED_PARENT_ALLOWLIST")

    child_bytes = parent_members.get("children/child.zip")
    if child_bytes is None:
        raise ZipJobRefusal("REFUSE_NESTED_CHILD_PACKET_MISSING", CHILD_JOB_ID)
    raw_child_members = _entries(child_bytes)
    if "children/subchild.zip" not in raw_child_members:
        raise ZipJobRefusal("REFUSE_NESTED_CHILD_PACKET_MISSING", SUBCHILD_JOB_ID)
    child, child_members, child_lineage = _lineage_from_packet(child_bytes)
    if child.manifest.job_id != CHILD_JOB_ID:
        raise ZipJobRefusal("REFUSE_NESTED_CHILD_ID", child.manifest.job_id)
    if child_lineage != {
        "schema": "constraintbox.nested_lineage.v1",
        "job_id": CHILD_JOB_ID,
        "parent_job_id": PARENT_JOB_ID,
        "depth": 1,
        "allowed_child_job_ids": [SUBCHILD_JOB_ID],
    }:
        raise ZipJobRefusal("REFUSE_NESTED_CHILD_LINEAGE")
    if child.manifest.allowed_child_job_ids != [SUBCHILD_JOB_ID] or child.manifest.max_child_depth != 1:
        raise ZipJobRefusal("REFUSE_NESTED_CHILD_ALLOWLIST")

    subchild_bytes = child_members.get("children/subchild.zip")
    if subchild_bytes is None:
        raise ZipJobRefusal("REFUSE_NESTED_CHILD_PACKET_MISSING", SUBCHILD_JOB_ID)
    subchild, _subchild_members, subchild_lineage = _lineage_from_packet(subchild_bytes)
    if subchild.manifest.job_id != SUBCHILD_JOB_ID:
        raise ZipJobRefusal("REFUSE_NESTED_SUBCHILD_ID", subchild.manifest.job_id)
    if subchild_lineage != {
        "schema": "constraintbox.nested_lineage.v1",
        "job_id": SUBCHILD_JOB_ID,
        "parent_job_id": CHILD_JOB_ID,
        "depth": 2,
        "allowed_child_job_ids": [],
    }:
        raise ZipJobRefusal("REFUSE_NESTED_SUBCHILD_LINEAGE")
    if subchild.manifest.allowed_child_job_ids or subchild.manifest.max_child_depth != 0:
        raise ZipJobRefusal("REFUSE_NESTED_SUBCHILD_ALLOWLIST")

    parent_task = parent.tasks[0]
    child_task = child.tasks[0]
    if (
        parent_task.operation != "run_child_zip_v1"
        or parent_task.input_paths != ["children/child.zip"]
        or parent_task.output_paths != ["output/child.return.zip"]
        or child_task.operation != "run_child_zip_v1"
        or child_task.input_paths != ["children/subchild.zip"]
        or child_task.output_paths != ["output/subchild.return.zip"]
    ):
        raise ZipJobRefusal("REFUSE_NESTED_TASK_BINDING")
    return NestedLeanCycle(
        packet_bytes=packet_bytes,
        parent_job_id=PARENT_JOB_ID,
        child_job_id=CHILD_JOB_ID,
        subchild_job_id=SUBCHILD_JOB_ID,
    )


def execute_nested_lean_cycle(packet_bytes: bytes | None = None) -> NestedLeanExecution:
    """Execute and verify one model-free nested ZIP graph."""

    cycle = validate_nested_lean_packet(
        build_nested_lean_cycle().packet_bytes if packet_bytes is None else packet_bytes
    )
    result = execute_packet(cycle.packet_bytes)
    validate_return_zip(result.return_zip_bytes, input_packet_bytes=cycle.packet_bytes)
    parent_return = _entries(result.return_zip_bytes)
    child_return = parent_return.get("output/child.return.zip")
    if child_return is None:
        raise ZipJobRefusal("REFUSE_NESTED_CHILD_RETURN_MISSING", cycle.child_job_id)
    child_packet = _entries(cycle.packet_bytes)["children/child.zip"]
    validate_return_zip(child_return, input_packet_bytes=child_packet)
    child_return_entries = _entries(child_return)
    subchild_return = child_return_entries.get("output/subchild.return.zip")
    if subchild_return is None:
        raise ZipJobRefusal("REFUSE_NESTED_SUBCHILD_RETURN_MISSING", cycle.subchild_job_id)
    subchild_packet = _entries(child_packet)["children/subchild.zip"]
    validate_return_zip(subchild_return, input_packet_bytes=subchild_packet)
    return NestedLeanExecution(
        cycle=cycle,
        result=result,
        retained_child_return_sha256=sha256_bytes(child_return),
        retained_subchild_return_sha256=sha256_bytes(subchild_return),
    )


def build_and_execute_nested_lean_cycle() -> NestedLeanExecution:
    """Convenience entrypoint used by the executable demo test."""

    return execute_nested_lean_cycle(build_nested_lean_cycle().packet_bytes)


__all__ = [
    "CHILD_JOB_ID",
    "LINEAGE_PATH",
    "NestedLeanCycle",
    "NestedLeanExecution",
    "PARENT_JOB_ID",
    "SUBCHILD_JOB_ID",
    "build_and_execute_nested_lean_cycle",
    "build_nested_lean_cycle",
    "execute_nested_lean_cycle",
    "validate_nested_lean_packet",
]
