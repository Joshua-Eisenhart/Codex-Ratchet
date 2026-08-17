from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .failure_wave import _manifest, _task
from .project_ledger import ProjectLedger
from .protocol import (
    TaskSpec,
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    sha256_bytes,
    strict_json_loads,
)

CLAIM_CEILING = "append_only_project_memory;not_admission;not_release"
DEFAULT_LEDGER = Path(__file__).resolve().parents[2] / "project_state"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ProjectDiscovery(_StrictModel):
    mode: Literal["NEW", "EXISTING"]
    required_question_ids: list[str] = Field(default_factory=list)
    answered_question_ids: list[str] = Field(default_factory=list)
    required_document_ids: list[str] = Field(default_factory=list)
    submitted_document_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_sets(self) -> "ProjectDiscovery":
        groups = (
            self.required_question_ids,
            self.answered_question_ids,
            self.required_document_ids,
            self.submitted_document_ids,
        )
        if any(len(values) != len(set(values)) for values in groups):
            raise ValueError("project discovery identifiers must be unique")
        if not set(self.answered_question_ids).issubset(self.required_question_ids):
            raise ValueError("answered questions must be declared")
        if not set(self.submitted_document_ids).issubset(self.required_document_ids):
            raise ValueError("submitted documents must be declared")
        if self.mode == "NEW" and not (
            self.required_question_ids or self.required_document_ids
        ):
            raise ValueError("a new project must declare discovery requirements")
        return self


class ModelRoute(_StrictModel):
    route_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model_requested: str = Field(min_length=1)
    budget_label: str = Field(min_length=1)
    status: Literal["QUALIFIED", "HOLD", "REFUSED"]
    qualification_receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class PrepromptRunConfiguration(_StrictModel):
    schema_: Literal["constraintbox.preprompt-run-configuration.v1"] = Field(
        alias="schema"
    )
    run_id: str = Field(min_length=1)
    prompt_round_index: int = Field(ge=0)
    minimum_prompt_rounds: int = Field(ge=2, le=16)
    project: ProjectDiscovery
    model_routes: list[ModelRoute] = Field(min_length=1)
    mini_mmm_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_run_data(self) -> "PrepromptRunConfiguration":
        route_ids = [row.route_id for row in self.model_routes]
        if len(route_ids) != len(set(route_ids)):
            raise ValueError("route identifiers must be unique")
        if len(self.mini_mmm_ids) != len(set(self.mini_mmm_ids)):
            raise ValueError("mini MMM identifiers must be unique")
        return self


class ToolQualification(_StrictModel):
    schema_: Literal["constraintbox.preprompt-tool-qualification.v1"] = Field(
        alias="schema"
    )
    status: Literal["QUALIFIED", "HOLD", "REFUSED"]
    tested_operation_ids: list[str]
    failed_operation_ids: list[str]
    receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def unique_tool_data(self) -> "ToolQualification":
        if len(self.tested_operation_ids) != len(set(self.tested_operation_ids)):
            raise ValueError("tested operation identifiers must be unique")
        if len(self.failed_operation_ids) != len(set(self.failed_operation_ids)):
            raise ValueError("failed operation identifiers must be unique")
        if not set(self.failed_operation_ids).issubset(self.tested_operation_ids):
            raise ValueError("failed operations must have been tested")
        if self.status == "QUALIFIED" and self.failed_operation_ids:
            raise ValueError("a qualified tool set cannot contain failed operations")
        return self


def _validate(model: type[_StrictModel], raw: bytes, label: str) -> _StrictModel:
    value = strict_json_loads(raw, label=label)
    try:
        return model.model_validate(value)
    except ValidationError as exc:
        raise ZipJobRefusal(
            "REFUSE_PREPROMPT_SCHEMA", f"{label}:{exc.errors(include_url=False)}"
        ) from exc


def compile_preprompt(
    *,
    ledger_root: Path,
    owner_prompt: bytes,
    run_configuration: PrepromptRunConfiguration,
    tool_qualification: ToolQualification,
) -> dict[str, Any]:
    ledger = ProjectLedger(ledger_root)
    verified = ledger.verify(verify_objects=False)
    events = [row["event"] for row in ledger._rows()]
    plans = [event for event in events if event["event_type"] == "PLAN_REVISION"]
    progress = [event for event in events if event["event_type"] == "PROGRESS_UPDATE"]
    latest_plan = (
        plans[-1]["material"]["text"]
        if plans and plans[-1]["material"].get("kind") == "verbatim_text"
        else ""
    )
    latest_progress = (
        progress[-1]["material"]["text"]
        if progress and progress[-1]["material"].get("kind") == "verbatim_text"
        else ""
    )
    project = run_configuration.project
    missing_questions = sorted(
        set(project.required_question_ids) - set(project.answered_question_ids)
    )
    missing_documents = sorted(
        set(project.required_document_ids) - set(project.submitted_document_ids)
    )
    route_holds = sorted(
        row.route_id for row in run_configuration.model_routes if row.status != "QUALIFIED"
    )
    if missing_questions or missing_documents:
        stage = "PROJECT_DISCOVERY_REQUIRED"
        next_operation = "answer_questions_or_submit_documents"
    elif route_holds or tool_qualification.status != "QUALIFIED":
        stage = "PREFLIGHT_HOLD"
        next_operation = "repair_or_replace_unqualified_routes_and_tools"
    elif run_configuration.prompt_round_index + 1 < run_configuration.minimum_prompt_rounds:
        stage = "PROMPT_REFINEMENT_REQUIRED"
        next_operation = "generate_and_compare_next_prompt_options"
    else:
        stage = "BOOT_PROBE_REQUIRED"
        next_operation = "run_content_tool_format_and_identity_boot_probes"
    return {
        "schema": "constraintbox.preprompt.v2",
        "run_id": run_configuration.run_id,
        "stage": stage,
        "owner_prompt_sha256": sha256_bytes(owner_prompt),
        "owner_prompt_text": owner_prompt.decode("utf-8", errors="replace"),
        "ledger_head_sha256": verified["head_sha256"],
        "ledger_event_count": verified["event_count"],
        "current_plan": latest_plan,
        "current_progress": latest_progress,
        "prompt_round": {
            "current_index": run_configuration.prompt_round_index,
            "minimum_rounds": run_configuration.minimum_prompt_rounds,
        },
        "project_discovery": {
            "mode": project.mode,
            "missing_question_ids": missing_questions,
            "missing_document_ids": missing_documents,
        },
        "model_routes": [
            row.model_dump(mode="json") for row in run_configuration.model_routes
        ],
        "route_holds": route_holds,
        "mini_mmm_ids": run_configuration.mini_mmm_ids,
        "tool_qualification": tool_qualification.model_dump(mode="json", by_alias=True),
        "boot_evidence_required": {
            "content_bytes_bound": True,
            "model_identity_bound": True,
            "python_tool_token_returned": True,
            "declared_output_format_passed": True,
            "mmm_read_proved": False,
            "claim": (
                "These checks can prove delivery and bounded use of supplied material; "
                "they cannot prove complete cognitive reading."
            ),
        },
        "execution_authorized": False,
        "next_operation": next_operation,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def run_compile_preprompt(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    if len(task.input_paths) != 3 or len(task.output_paths) != 2:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    intent_path, run_path, tool_path = task.input_paths
    intent = strict_json_loads(workspace[intent_path], label=intent_path)
    if not isinstance(intent, dict) or set(intent) != {
        "schema",
        "owner_prompt",
        "ledger_root",
    }:
        raise ZipJobRefusal("REFUSE_PREPROMPT_SCHEMA", "intent")
    if intent.get("schema") != "constraintbox.preprompt-intent.v2":
        raise ZipJobRefusal("REFUSE_PREPROMPT_SCHEMA", "intent.schema")
    owner = intent.get("owner_prompt")
    if not isinstance(owner, str) or not owner:
        raise ZipJobRefusal("REFUSE_PREPROMPT_SCHEMA", "owner_prompt")
    root = Path(str(intent.get("ledger_root") or DEFAULT_LEDGER))
    if not root.is_absolute():
        raise ZipJobRefusal("REFUSE_PREPROMPT_ROOT", str(root))
    run_configuration = _validate(
        PrepromptRunConfiguration, workspace[run_path], run_path
    )
    tool_qualification = _validate(ToolQualification, workspace[tool_path], tool_path)
    assert isinstance(run_configuration, PrepromptRunConfiguration)
    assert isinstance(tool_qualification, ToolQualification)
    compiled = compile_preprompt(
        ledger_root=root,
        owner_prompt=owner.encode("utf-8"),
        run_configuration=run_configuration,
        tool_qualification=tool_qualification,
    )
    return {
        task.output_paths[0]: canonical_json_bytes(compiled),
        task.output_paths[1]: compiled["current_plan"].encode("utf-8"),
    }


def build_preprompt_packet(
    *,
    owner_prompt: str,
    run_configuration: PrepromptRunConfiguration | dict[str, object],
    tool_qualification: ToolQualification | dict[str, object],
    ledger_root: Path | None = None,
) -> bytes:
    run_value = (
        run_configuration
        if isinstance(run_configuration, PrepromptRunConfiguration)
        else PrepromptRunConfiguration.model_validate(run_configuration)
    )
    tool_value = (
        tool_qualification
        if isinstance(tool_qualification, ToolQualification)
        else ToolQualification.model_validate(tool_qualification)
    )
    intent = {
        "schema": "constraintbox.preprompt-intent.v2",
        "owner_prompt": owner_prompt,
        "ledger_root": str(ledger_root or DEFAULT_LEDGER),
    }
    input_paths = [
        "inputs/preprompt_intent.json",
        "inputs/run_configuration.json",
        "inputs/tool_qualification.json",
    ]
    files = {
        "00_RUN_ME_FIRST.md": (
            b"# CB-run preprompt\n\n"
            b"Shows receipt-bound project, route, tool, and prompt-stage facts. "
            b"It does not execute work.\n"
        ),
        input_paths[0]: canonical_json_bytes(intent),
        input_paths[1]: canonical_json_bytes(
            run_value.model_dump(mode="json", by_alias=True)
        ),
        input_paths[2]: canonical_json_bytes(
            tool_value.model_dump(mode="json", by_alias=True)
        ),
        "tasks/00_preprompt.task.json": _task(
            task_id="compile-preprompt",
            sequence=0,
            operation="compile_preprompt_v1",
            inputs=input_paths,
            outputs=["output/preprompt.json", "output/current_plan.md"],
        ),
    }
    return build_packet(
        _manifest(
            job_id=f"cb-preprompt-{run_value.run_id}",
            task_paths=["tasks/00_preprompt.task.json"],
            outputs=["output/preprompt.json", "output/current_plan.md"],
            operations=["compile_preprompt_v1"],
            claim_ceiling=CLAIM_CEILING,
        ),
        files,
    )
