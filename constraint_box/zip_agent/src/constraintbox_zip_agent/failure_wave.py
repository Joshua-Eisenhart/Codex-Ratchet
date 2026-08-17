from __future__ import annotations

from typing import Any

from .protocol import build_packet, canonical_json_bytes

CLAIM_CEILING = "local_deterministic_zip_execution_only;not_model_execution;not_admission;not_release"


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
    child_ids: list[str] | None = None,
    depth: int = 0,
    claim_ceiling: str = CLAIM_CEILING,
) -> dict[str, Any]:
    return {
        "schema": "constraintbox.zip_job.v1",
        "job_id": job_id,
        "task_execution_order": task_paths,
        "required_output_file_list": outputs,
        "allowed_operations": sorted(set(operations)),
        "allowed_child_job_ids": child_ids or [],
        "max_child_depth": depth,
        "claim_ceiling": claim_ceiling,
    }


def build_demo_packet() -> bytes:
    task_path = "tasks/00_canonicalize.task.json"
    output_path = "output/canonical.json"
    files = {
        "00_RUN_ME_FIRST.md": (
            b"# ConstraintBox ZIP_JOB demo\n\n"
            b"The runtime, not this prose, owns task order and authority.\n"
        ),
        "inputs/payload.json": b'{"z":3,"a":[2,1]}\n',
        task_path: _task(
            task_id="canonicalize",
            sequence=0,
            operation="canonical_json_sha256_v1",
            inputs=["inputs/payload.json"],
            outputs=[output_path],
        ),
    }
    return build_packet(
        _manifest(
            job_id="zip-agent-demo",
            task_paths=[task_path],
            outputs=[output_path],
            operations=["canonical_json_sha256_v1"],
        ),
        files,
    )


def _audit_child(
    target: bytes,
    *,
    name: str,
    operation: str,
    target_return: bytes | None = None,
) -> bytes:
    task_path = f"tasks/00_{name}.task.json"
    output_path = f"output/{name}.json"
    input_paths = ["inputs/target.zip"]
    files = {
        "00_RUN_ME_FIRST.md": (
            f"# {name}\n\nThis deterministic audit member does not mint authority.\n".encode("utf-8")
        ),
        "inputs/target.zip": target,
        task_path: _task(
            task_id=name,
            sequence=0,
            operation=operation,
            inputs=input_paths,
            outputs=[output_path],
        ),
    }
    if target_return is not None:
        files["inputs/target.return.zip"] = target_return
        input_paths.append("inputs/target.return.zip")
        files[task_path] = _task(
            task_id=name,
            sequence=0,
            operation=operation,
            inputs=input_paths,
            outputs=[output_path],
        )
    return build_packet(
        _manifest(
            job_id=f"zip-failure-{name}",
            task_paths=[task_path],
            outputs=[output_path],
            operations=[operation],
        ),
        files,
    )


def build_failure_wave_packet(target: bytes, *, target_return: bytes | None = None) -> bytes:
    children = {
        "structure": _audit_child(target, name="structure", operation="audit_packet_structure_v1"),
        "counterexample": _audit_child(
            target, name="counterexample", operation="audit_packet_mutations_v1"
        ),
        "authority-collapse": _audit_child(
            target,
            name="authority-collapse",
            operation="audit_runtime_authority_v1",
            target_return=target_return,
        ),
    }
    files: dict[str, bytes] = {
        "00_RUN_ME_FIRST.md": (
            b"# ZIP-native failure wave\n\n"
            b"Three child ZIPs run through the parent runtime. The compiled return ZIP is the result.\n"
        )
    }
    task_paths: list[str] = []
    outputs: list[str] = []
    child_task_ids: list[str] = []
    for sequence, name in enumerate(("structure", "counterexample", "authority-collapse")):
        child_path = f"children/{name}.zip"
        output_path = f"output/{name}.return.zip"
        task_path = f"tasks/{sequence:02d}_{name}.task.json"
        task_id = f"run-{name}"
        files[child_path] = children[name]
        files[task_path] = _task(
            task_id=task_id,
            sequence=sequence,
            operation="run_child_zip_v1",
            inputs=[child_path],
            outputs=[output_path],
        )
        task_paths.append(task_path)
        outputs.append(output_path)
        child_task_ids.append(task_id)

    compile_path = "tasks/03_compile.task.json"
    compile_output = "output/failure_wave.json"
    files[compile_path] = _task(
        task_id="compile",
        sequence=3,
        operation="compile_failure_wave_v1",
        inputs=list(outputs),
        outputs=[compile_output],
        depends_on=child_task_ids,
    )
    task_paths.append(compile_path)
    outputs.append(compile_output)
    child_ids = [f"zip-failure-{name}" for name in ("structure", "counterexample", "authority-collapse")]
    return build_packet(
        _manifest(
            job_id="zip-agent-failure-wave",
            task_paths=task_paths,
            outputs=outputs,
            operations=["run_child_zip_v1", "compile_failure_wave_v1"],
            child_ids=child_ids,
            depth=1,
        ),
        files,
    )
