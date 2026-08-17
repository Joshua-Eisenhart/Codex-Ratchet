from __future__ import annotations

from dataclasses import dataclass

from .operation_ids import KNOWN_OPERATION_IDS
from .operations import run_local_operation
from .protocol import (
    TaskSpec,
    ZipJobRefusal,
    canonical_json_bytes,
    deterministic_zip,
    runtime_source_sha256,
    sha256_bytes,
    validate_packet,
    validate_return_zip,
)


@dataclass(frozen=True)
class ExecutionResult:
    job_id: str
    input_packet_sha256: str
    return_zip_sha256: str
    return_zip_bytes: bytes
    task_count: int


def _task_receipt(task: TaskSpec, workspace: dict[str, bytes], outputs: dict[str, bytes]) -> bytes:
    return canonical_json_bytes(
        {
            "schema": "constraintbox.zip_task_receipt.v1",
            "task_id": task.task_id,
            "sequence": task.sequence,
            "operation": task.operation,
            "depends_on": task.depends_on,
            "input_sha256": {path: sha256_bytes(workspace[path]) for path in task.input_paths},
            "preload_sha256": {path: sha256_bytes(workspace[path]) for path in task.preload_files},
            "output_sha256": {path: sha256_bytes(outputs[path]) for path in sorted(outputs)},
            "disposition": "TASK_EXECUTED_LOCAL",
            "claim_ceiling": "deterministic_local_operation_only;not_model_execution;not_admission",
        }
    )


def _run_child(
    task: TaskSpec,
    workspace: dict[str, bytes],
    *,
    allowed_child_job_ids: set[str],
    depth: int,
    root_depth_limit: int,
) -> dict[str, bytes]:
    if len(task.input_paths) != 1 or len(task.output_paths) != 1:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    if depth + 1 > root_depth_limit:
        raise ZipJobRefusal("REFUSE_CHILD_DEPTH_LIMIT", task.task_id)
    child_bytes = workspace[task.input_paths[0]]
    child = validate_packet(child_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    if child.manifest.job_id not in allowed_child_job_ids:
        raise ZipJobRefusal("REFUSE_CHILD_JOB_NOT_ALLOWLISTED", child.manifest.job_id)
    child_depth_limit = min(root_depth_limit, depth + 1 + child.manifest.max_child_depth)
    result = execute_packet(child_bytes, _depth=depth + 1, _root_depth_limit=child_depth_limit)
    return {task.output_paths[0]: result.return_zip_bytes}


def execute_packet(
    packet_bytes: bytes,
    *,
    _depth: int = 0,
    _root_depth_limit: int | None = None,
) -> ExecutionResult:
    packet = validate_packet(packet_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    root_depth_limit = packet.manifest.max_child_depth if _root_depth_limit is None else _root_depth_limit
    if _depth > root_depth_limit:
        raise ZipJobRefusal("REFUSE_CHILD_DEPTH_LIMIT", packet.manifest.job_id)

    workspace = dict(packet.members)
    produced: dict[str, bytes] = {}
    receipt_entries: dict[str, bytes] = {}
    completed: set[str] = set()
    declared_children: set[str] = set()
    source_before = runtime_source_sha256()
    for task in packet.tasks:
        if task.operation == "run_child_zip_v1":
            if len(task.input_paths) != 1:
                raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
            child = validate_packet(workspace[task.input_paths[0]], known_operations=set(KNOWN_OPERATION_IDS))
            declared_children.add(child.manifest.job_id)
    if declared_children != set(packet.manifest.allowed_child_job_ids):
        raise ZipJobRefusal("REFUSE_CHILD_DECLARATION_MISMATCH")
    for task in packet.tasks:
        if not set(task.depends_on).issubset(completed):
            raise ZipJobRefusal("REFUSE_DEPENDENCY_NOT_COMPLETED", task.task_id)
        if task.preload_files:
            raise ZipJobRefusal("HOLD_MODEL_CONNECTOR_UNBOUND", task.task_id)
        if task.parameters:
            raise ZipJobRefusal("REFUSE_OPERATION_PARAMETERS_UNSUPPORTED", task.task_id)
        if task.operation == "run_child_zip_v1":
            outputs = _run_child(
                task,
                workspace,
                allowed_child_job_ids=set(packet.manifest.allowed_child_job_ids),
                depth=_depth,
                root_depth_limit=root_depth_limit,
            )
        else:
            outputs = run_local_operation(task, workspace)
        if set(outputs) != set(task.output_paths):
            raise ZipJobRefusal("REFUSE_OPERATION_OUTPUT_SET_MISMATCH", task.task_id)
        for path, data in outputs.items():
            if not isinstance(data, bytes):
                raise ZipJobRefusal("REFUSE_OPERATION_NON_BYTES_OUTPUT", path)
            workspace[path] = data
            produced[path] = data
        receipt_path = f"receipts/{task.sequence:02d}_{task.task_id}.json"
        receipt_entries[receipt_path] = _task_receipt(task, workspace, outputs)
        completed.add(task.task_id)

    required = set(packet.manifest.required_output_file_list)
    if set(produced) != required:
        raise ZipJobRefusal("REFUSE_RUNTIME_REQUIRED_OUTPUT_SET_MISMATCH")
    source_after = runtime_source_sha256()
    if source_before != source_after:
        raise ZipJobRefusal("HOLD_RETURN_RUNTIME_SOURCE_DRIFT", "mid_run")
    body_entries = {**produced, **receipt_entries}
    return_manifest = {
        "schema": "constraintbox.zip_return.v1",
        "job_id": packet.manifest.job_id,
        "input_packet_sha256": packet.packet_sha256,
        "runtime_source_sha256": source_after,
        "task_execution_order": [task.task_id for task in packet.tasks],
        "required_output_file_list": packet.manifest.required_output_file_list,
        "file_sha256_registry": {
            path: sha256_bytes(data) for path, data in sorted(body_entries.items())
        },
        "disposition": "ZIP_JOB_EXECUTED_LOCAL",
        "claim_ceiling": packet.manifest.claim_ceiling,
    }
    return_entries = dict(body_entries)
    return_entries["RETURN_MANIFEST.json"] = canonical_json_bytes(return_manifest)
    return_bytes = deterministic_zip(return_entries)
    validate_return_zip(
        return_bytes,
        expected_input_sha256=packet.packet_sha256,
        input_packet_bytes=packet_bytes,
    )
    return ExecutionResult(
        job_id=packet.manifest.job_id,
        input_packet_sha256=packet.packet_sha256,
        return_zip_sha256=sha256_bytes(return_bytes),
        return_zip_bytes=return_bytes,
        task_count=len(packet.tasks),
    )
