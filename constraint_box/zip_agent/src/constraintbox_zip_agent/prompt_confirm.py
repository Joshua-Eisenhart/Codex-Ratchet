from __future__ import annotations

import io
import zipfile
from typing import Any

from .failure_wave import _manifest, _task
from .protocol import (
    TaskSpec,
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    sha256_bytes,
    strict_json_loads,
)

CLAIM_CEILING = "local_prompt_confirm_only;not_execution;not_admission;not_release"
CHOICE_SCHEMA = "constraintbox.prompt-confirm-choice.v1"
RECEIPT_SCHEMA = "constraintbox.prompt-confirm-receipt.v1"


def _object(raw: bytes, label: str) -> dict[str, Any]:
    value = strict_json_loads(raw, label=label)
    if not isinstance(value, dict):
        raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_SCHEMA", label)
    return value


def _materialize_work_zips(
    *,
    surface: dict[str, Any],
    selected: list[str],
) -> dict[str, bytes]:
    templates = surface.get("work_templates")
    if templates is None:
        return {}
    if not isinstance(templates, dict):
        raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_SURFACE", "work_templates")
    produced: dict[str, bytes] = {}
    for template_id in selected:
        spec = templates.get(template_id)
        if not isinstance(spec, dict):
            raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_MATERIALIZE", template_id)
        files = spec.get("files")
        if not isinstance(files, dict) or not files:
            raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_MATERIALIZE", f"{template_id}.files")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path, body in sorted(files.items()):
                if not isinstance(path, str) or not path or path.startswith("/") or ".." in path:
                    raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_MATERIALIZE", path)
                if not isinstance(body, str):
                    raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_MATERIALIZE", f"{template_id}:{path}")
                archive.writestr(path, body.encode("utf-8"))
        produced[f"output/work/{template_id}.zip"] = buffer.getvalue()
    return produced


def run_prompt_confirm(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    if len(task.input_paths) != 2:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    if "output/prompt_confirm.json" not in task.output_paths:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", "prompt_confirm")
    surface = _object(workspace[task.input_paths[0]], task.input_paths[0])
    choice = _object(workspace[task.input_paths[1]], task.input_paths[1])
    if choice.get("schema") != CHOICE_SCHEMA:
        raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_SCHEMA", "schema")
    selected = choice.get("selected_template_ids")
    if not isinstance(selected, list) or not selected or any(
        not isinstance(item, str) or not item for item in selected
    ):
        raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_SELECTION", "selected_template_ids")
    if len(selected) != len(set(selected)):
        raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_SELECTION", "duplicate")
    ready = surface.get("ready_template_options")
    if not isinstance(ready, list):
        raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_SURFACE", "ready_template_options")
    eligible = {
        row["template_id"]
        for row in ready
        if isinstance(row, dict) and isinstance(row.get("template_id"), str)
    }
    unknown = [item for item in selected if item not in eligible]
    if unknown:
        raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_SELECTION", ",".join(unknown))
    automation = surface.get("automation")
    if isinstance(automation, dict) and automation.get("execution_authorized") is True:
        raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_EXECUTION", "automation")
    if surface.get("execution_authorized") is True or choice.get("execute") is True:
        raise ZipJobRefusal("REFUSE_PROMPT_CONFIRM_EXECUTION", "execute")
    work_zips = _materialize_work_zips(surface=surface, selected=selected)
    expected_work = {f"output/work/{item}.zip" for item in selected} if work_zips else set()
    if set(task.output_paths) != {"output/prompt_confirm.json"} | expected_work:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", "work_outputs")
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "selected_template_ids": selected,
        "eligible_template_ids": sorted(eligible),
        "surface_sha256": sha256_bytes(workspace[task.input_paths[0]]),
        "choice_sha256": sha256_bytes(workspace[task.input_paths[1]]),
        "materialized_work_zip": bool(work_zips),
        "work_zip_sha256": {
            path: sha256_bytes(blob) for path, blob in sorted(work_zips.items())
        },
        "execution_authorized": False,
        "executed_work_zip": False,
        "next_operation": "separate_execute_operation",
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    produced = {path: blob for path, blob in work_zips.items()}
    produced["output/prompt_confirm.json"] = canonical_json_bytes(receipt)
    return produced


def build_prompt_confirm_packet(*, surface: dict[str, Any], choice: dict[str, Any]) -> bytes:
    selected = choice.get("selected_template_ids") if isinstance(choice, dict) else None
    outputs = ["output/prompt_confirm.json"]
    if isinstance(selected, list) and surface.get("work_templates"):
        outputs.extend(f"output/work/{item}.zip" for item in selected if isinstance(item, str))
    files = {
        "00_RUN_ME_FIRST.md": (
            b"# PROMPT_CONFIRM\n\nBinds a human template choice. May materialize work ZIPs. Does not execute.\n"
        ),
        "inputs/confirmation_surface.json": canonical_json_bytes(surface),
        "inputs/human_choice.json": canonical_json_bytes(choice),
        "tasks/00_confirm.task.json": _task(
            task_id="prompt-confirm",
            sequence=0,
            operation="compile_prompt_confirm_v1",
            inputs=["inputs/confirmation_surface.json", "inputs/human_choice.json"],
            outputs=outputs,
        ),
    }
    return build_packet(
        _manifest(
            job_id="prompt-confirm",
            task_paths=["tasks/00_confirm.task.json"],
            outputs=outputs,
            operations=["compile_prompt_confirm_v1"],
            claim_ceiling=CLAIM_CEILING,
        ),
        files,
    )
