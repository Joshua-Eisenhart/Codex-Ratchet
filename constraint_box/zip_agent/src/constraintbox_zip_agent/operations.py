from __future__ import annotations

from typing import Callable

from .protocol import TaskSpec, ZipJobRefusal, canonical_json_bytes, sha256_bytes, strict_json_loads

Operation = Callable[[TaskSpec, dict[str, bytes]], dict[str, bytes]]


def _one_in_one_out(task: TaskSpec) -> tuple[str, str]:
    if len(task.input_paths) != 1 or len(task.output_paths) != 1:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    return task.input_paths[0], task.output_paths[0]


def canonical_json_sha256(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    source_path, output_path = _one_in_one_out(task)
    value = strict_json_loads(workspace[source_path], label=source_path)
    canonical = canonical_json_bytes(value)
    return {
        output_path: canonical_json_bytes(
            {
                "schema": "constraintbox.canonical_json_sha256.v1",
                "input_path": source_path,
                "input_sha256": sha256_bytes(workspace[source_path]),
                "canonical_json": canonical.decode("ascii"),
                "canonical_sha256": sha256_bytes(canonical),
            }
        )
    }


def text_sha256(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    source_path, output_path = _one_in_one_out(task)
    try:
        text = workspace[source_path].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ZipJobRefusal("REFUSE_TEXT_NOT_UTF8", source_path) from exc
    return {
        output_path: canonical_json_bytes(
            {
                "schema": "constraintbox.text_sha256.v1",
                "input_path": source_path,
                "text_length": len(text),
                "text_sha256": sha256_bytes(workspace[source_path]),
            }
        )
    }


def run_local_operation(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    operations: dict[str, Operation] = {
        "canonical_json_sha256_v1": canonical_json_sha256,
        "text_sha256_v1": text_sha256,
    }
    if task.operation in operations:
        return operations[task.operation](task, workspace)
    if task.operation.startswith("audit_") or task.operation == "compile_failure_wave_v1":
        from .self_audit import run_audit_operation

        return run_audit_operation(task, workspace)
    if task.operation == "probe_tool_field_v1":
        from .tool_field import run_tool_field

        if len(task.input_paths) != 4:
            raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
        return run_tool_field(
            workspace[task.input_paths[0]],
            workspace[task.input_paths[1]],
            workspace[task.input_paths[2]],
            workspace[task.input_paths[3]],
        )
    if task.operation == "compile_prompt_handshake_v1":
        from .prompt_handshake import run_prompt_handshake

        return run_prompt_handshake(task, workspace)
    if task.operation == "run_provider_call_v1":
        from .provider_task import run_provider_call

        return run_provider_call(task, workspace)
    if task.operation == "run_md_agent_roster_v1":
        from .md_agent_roster import run_md_agent_roster

        return run_md_agent_roster(task, workspace)
    if task.operation == "run_zip_python_tool_v1":
        from .zip_python_tool import run_zip_python_tool

        return run_zip_python_tool(task, workspace)
    if task.operation == "compile_prompt_confirm_v1":
        from .prompt_confirm import run_prompt_confirm

        return run_prompt_confirm(task, workspace)
    if task.operation == "compile_council_loop_v1":
        from .council_zip import run_council_loop_compile

        return run_council_loop_compile(task, workspace)
    if task.operation == "execute_work_zip_v1":
        from .execute_work_zip import run_execute_work_zip

        return run_execute_work_zip(task, workspace)
    if task.operation == "append_project_ledger_v1":
        from .project_ledger import run_append_project_ledger

        return run_append_project_ledger(task, workspace)
    if task.operation == "compile_preprompt_v1":
        from .preprompt import run_compile_preprompt

        return run_compile_preprompt(task, workspace)
    if task.operation == "render_human_oracle_v2":
        from .human_oracle import run_human_oracle

        return run_human_oracle(task, workspace)
    if task.operation == "render_human_oracle_map_update_v1":
        from .human_oracle import run_human_oracle_map_update

        return run_human_oracle_map_update(task, workspace)
    if task.operation == "compile_execution_evidence_v1":
        from .execution_evidence import run_compile_execution_evidence_v1

        return run_compile_execution_evidence_v1(task, workspace)
    if task.operation == "operation_probe_field_v1":
        from .operation_probe_field import run_operation_probe_field_from_zip

        return run_operation_probe_field_from_zip(task, workspace)
    if task.operation in {"run_cb_minilev_operation_v1", "probe_cb_minilev_operation_v1"}:
        from .minilev_operation_probe import run_minilev_zip_operation

        return run_minilev_zip_operation(
            task,
            workspace,
            cohort=task.operation == "probe_cb_minilev_operation_v1",
        )
    if task.operation == "compile_provider_nested_inventory_v1":
        from .provider_nested_council import run_compile_provider_nested_inventory

        return run_compile_provider_nested_inventory(task, workspace)
    raise ZipJobRefusal("REFUSE_OPERATION_NOT_LOCAL", task.operation)
