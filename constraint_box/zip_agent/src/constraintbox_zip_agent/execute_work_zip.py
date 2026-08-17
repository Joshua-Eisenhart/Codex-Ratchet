from __future__ import annotations

from typing import Any

from .failure_wave import _manifest, _task
from .protocol import (
    TaskSpec,
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    sha256_bytes,
    strict_json_loads,
    validate_packet,
)
from .runtime import execute_packet

CLAIM_CEILING = "local_separate_execute_only;not_confirm;not_admission;not_release"
AUTH_SCHEMA = "constraintbox.work-zip-execute.v1"


def run_execute_work_zip(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    if len(task.input_paths) != 2 or len(task.output_paths) != 2:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    work_zip = workspace[task.input_paths[0]]
    auth = strict_json_loads(workspace[task.input_paths[1]], label=task.input_paths[1])
    if not isinstance(auth, dict) or auth.get("schema") != AUTH_SCHEMA:
        raise ZipJobRefusal("REFUSE_WORK_ZIP_EXECUTE_SCHEMA", "schema")
    if set(auth) != {"schema", "execute", "work_zip_sha256", "source"}:
        raise ZipJobRefusal("REFUSE_WORK_ZIP_EXECUTE_SCHEMA", "fields")
    if auth.get("source") != "separate_execute_operation":
        raise ZipJobRefusal("REFUSE_WORK_ZIP_EXECUTE_SCHEMA", "source")
    if auth.get("execute") is not True:
        raise ZipJobRefusal("HOLD_WORK_ZIP_EXECUTE_NOT_AUTHORIZED", "execute")
    if auth.get("work_zip_sha256") != sha256_bytes(work_zip):
        raise ZipJobRefusal("REFUSE_WORK_ZIP_EXECUTE_BINDING", "work_zip_sha256")
    try:
        validated = validate_packet(work_zip)
    except ZipJobRefusal as exc:
        raise ZipJobRefusal("REFUSE_WORK_ZIP_NOT_PACKET", exc.reason_code) from exc
    if "execute_work_zip_v1" in validated.manifest.allowed_operations:
        raise ZipJobRefusal("REFUSE_WORK_ZIP_EXECUTOR_RECURSION", "execute_work_zip_v1")
    result = execute_packet(work_zip)
    receipt: dict[str, Any] = {
        "schema": "constraintbox.work-zip-execute-receipt.v1",
        "work_zip_sha256": sha256_bytes(work_zip),
        "authorization_sha256": sha256_bytes(workspace[task.input_paths[1]]),
        "return_zip_sha256": result.return_zip_sha256,
        "executed": True,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    return {
        task.output_paths[0]: result.return_zip_bytes,
        task.output_paths[1]: canonical_json_bytes(receipt),
    }


def build_execute_work_zip_packet(*, work_zip: bytes, authorization: dict[str, Any]) -> bytes:
    files = {
        "00_RUN_ME_FIRST.md": b"# separate execute\n\nNot confirm. Not promotion.\n",
        "inputs/work.zip": work_zip,
        "inputs/execute_authorization.json": canonical_json_bytes(authorization),
        "tasks/00_execute.task.json": _task(
            task_id="execute-work",
            sequence=0,
            operation="execute_work_zip_v1",
            inputs=["inputs/work.zip", "inputs/execute_authorization.json"],
            outputs=["output/work.return.zip", "output/execute_receipt.json"],
        ),
    }
    return build_packet(
        _manifest(
            job_id="execute-work-zip",
            task_paths=["tasks/00_execute.task.json"],
            outputs=["output/work.return.zip", "output/execute_receipt.json"],
            operations=["execute_work_zip_v1"],
            claim_ceiling=CLAIM_CEILING,
        ),
        files,
    )
