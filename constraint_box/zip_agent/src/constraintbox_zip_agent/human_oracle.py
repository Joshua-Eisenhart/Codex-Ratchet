from __future__ import annotations

import io
import zipfile
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .protocol import (
    TaskSpec,
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    runtime_source_sha256,
    sha256_bytes,
    strict_json_loads,
    validate_packet,
    validate_return_zip,
)

INPUT_PATH = "inputs/human_oracle_surface.json"
OUTPUT_PATH = "output/HUMAN_ORACLE.md"
TASK_PATH = "tasks/00_render_human_oracle.task.json"
MAP_PACKET_PATH = "inputs/map/work_cycle.packet.zip"
MAP_RETURN_PATH = "inputs/map/work_cycle.return.zip"
MAP_QUOTIENT_PATH = "output/measured_quotient.json"
OPERATION_PACKET_PATH = "inputs/map/operation_probe.packet.zip"
OPERATION_RETURN_PATH = "inputs/map/operation_probe.return.zip"
OPERATION_FIELD_PATH = "output/operation_probe_field.json"
OPERATION_EVENTS_PATH = "output/operation_probe_events.jsonl"
MAP_DELTA_OUTPUT_PATH = "output/human_oracle_map_delta.json"
UPDATED_MAP_OUTPUT_PATH = "output/human_oracle_updated_map.json"
MAP_UPDATE_TASK_PATH = "tasks/00_render_human_oracle_map_update.task.json"
REQUIRED_OPERATION_TOOL_IDS = ("jsonschema", "pydantic")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ExecutionCounts(_StrictModel):
    model_calls: int = Field(ge=0)
    agents: int = Field(ge=0)
    subagents: int = Field(ge=0)
    subsubagents: int = Field(ge=0)
    deeper_agents: int = Field(ge=0)
    tool_operations: int = Field(ge=0)
    retries: int = Field(ge=0)
    failures: int = Field(ge=0)
    source_receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class AgentRun(_StrictModel):
    agent_id: str = Field(min_length=1)
    parent_agent_id: str | None = None
    depth: int = Field(ge=0)
    status: Literal["COMPLETED", "FAILED", "HOLD", "CANCELLED"]
    model_route_id: str | None = None
    receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ModelRun(_StrictModel):
    route_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model_requested: str = Field(min_length=1)
    model_observed: str = Field(min_length=1)
    call_count: int = Field(ge=1)
    status: Literal["COMPLETED", "FAILED", "HOLD", "CANCELLED"]
    receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class PythonToolRun(_StrictModel):
    tool_id: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    call_count: int = Field(ge=1)
    status: Literal["COMPLETED", "FAILED", "HOLD", "CANCELLED"]
    receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class SkillRun(_StrictModel):
    skill_id: str = Field(min_length=1)
    call_count: int = Field(ge=1)
    status: Literal["COMPLETED", "FAILED", "HOLD", "CANCELLED"]
    receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class WaveRun(_StrictModel):
    wave_id: str = Field(min_length=1)
    profile: Literal["LEAN", "FULL"]
    status: Literal["COMPLETED", "FAILED", "HOLD", "CANCELLED"]
    receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ProcessMinimums(_StrictModel):
    profile_id: str = Field(min_length=1)
    distinct_providers: int = Field(ge=0)
    model_calls: int = Field(ge=0)
    agents: int = Field(ge=0)
    subagents: int = Field(ge=0)
    subsubagents: int = Field(ge=0)
    python_tool_calls: int = Field(ge=0)
    required_skill_ids: list[str] = Field(default_factory=list)
    required_wave_ids: list[str] = Field(default_factory=list)


class FailureItem(_StrictModel):
    reason_code: str = Field(min_length=1)
    plain_language: str = Field(min_length=1)
    impact: str = Field(min_length=1)
    next_test: str | None = None


class NextPromptOption(_StrictModel):
    option_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    prompt_text: str = Field(min_length=1)
    combines_actions: list[str] = Field(min_length=2)
    framing_mmm_ids: list[str] = Field(default_factory=list)
    preserves_raw_prompt: Literal[True]

    @model_validator(mode="after")
    def unique_actions(self) -> "NextPromptOption":
        if len(set(self.combines_actions)) != len(self.combines_actions):
            raise ValueError("combines_actions must be unique")
        return self


class HumanOracleSurface(_StrictModel):
    schema_: Literal["constraintbox.human-oracle-surface.v2"] = Field(alias="schema")
    run_id: str = Field(min_length=1)
    state: Literal[
        "HUMAN_CONFIRMATION_REQUIRED",
        "HOLD",
        "REFUSED",
        "CANCELLED",
        "COMPLETE",
    ]
    headline: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    closing_summary: str | None = Field(default=None, min_length=1)
    raw_prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    map_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    map_return_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    required_map_tool_ids: tuple[str, ...]
    execution: ExecutionCounts
    models: list[ModelRun]
    agent_runs: list[AgentRun]
    python_tools: list[PythonToolRun]
    skills: list[SkillRun]
    waves: list[WaveRun]
    minimums: ProcessMinimums
    minimums_satisfied: bool
    what_ran: list[str]
    failures_and_unknowns: list[FailureItem]
    decision_needed: str = Field(min_length=1)
    next_prompt_options: list[NextPromptOption] = Field(min_length=2)
    claim_ceiling: str = Field(min_length=1)
    execution_authorized: Literal[False]
    promotion_allowed: Literal[False]

    @model_validator(mode="after")
    def receipt_counts_are_coherent(self) -> "HumanOracleSurface":
        if self.required_map_tool_ids != REQUIRED_OPERATION_TOOL_IDS:
            raise ValueError("required_map_tool_ids must match the exact operation contract")
        if sum(row.call_count for row in self.models) != self.execution.model_calls:
            raise ValueError("model call count does not match model receipts")
        if len({row.route_id for row in self.models}) != len(self.models):
            raise ValueError("route_id values must be unique")
        if sum(row.call_count for row in self.python_tools) != self.execution.tool_operations:
            raise ValueError("Python tool call count does not match tool receipts")
        agent_ids = {row.agent_id for row in self.agent_runs}
        if len(agent_ids) != len(self.agent_runs):
            raise ValueError("agent_id values must be unique")
        for row in self.agent_runs:
            if row.depth == 0 and row.parent_agent_id is not None:
                raise ValueError("depth-zero agents cannot have a parent")
            if row.depth > 0 and row.parent_agent_id not in agent_ids:
                raise ValueError("nested agent parent must exist in agent_runs")
        actual_depth_counts = (
            sum(row.depth == 0 for row in self.agent_runs),
            sum(row.depth == 1 for row in self.agent_runs),
            sum(row.depth == 2 for row in self.agent_runs),
            sum(row.depth > 2 for row in self.agent_runs),
        )
        declared_depth_counts = (
            self.execution.agents,
            self.execution.subagents,
            self.execution.subsubagents,
            self.execution.deeper_agents,
        )
        if actual_depth_counts != declared_depth_counts:
            raise ValueError("agent depth counts do not match agent receipts")
        completed_models = [row for row in self.models if row.status == "COMPLETED"]
        completed_model_calls = sum(row.call_count for row in completed_models)
        completed_providers = {row.provider for row in completed_models}
        completed_tools = sum(
            row.call_count for row in self.python_tools if row.status == "COMPLETED"
        )
        checks = {
            "distinct_providers": len(completed_providers) >= self.minimums.distinct_providers,
            "model_calls": completed_model_calls >= self.minimums.model_calls,
            "agents": actual_depth_counts[0] >= self.minimums.agents,
            "subagents": actual_depth_counts[1] >= self.minimums.subagents,
            "subsubagents": actual_depth_counts[2] >= self.minimums.subsubagents,
            "python_tool_calls": completed_tools >= self.minimums.python_tool_calls,
            "required_skill_ids": set(self.minimums.required_skill_ids).issubset(
                {row.skill_id for row in self.skills if row.status == "COMPLETED"}
            ),
            "required_wave_ids": set(self.minimums.required_wave_ids).issubset(
                {row.wave_id for row in self.waves if row.status == "COMPLETED"}
            ),
        }
        failed = sorted(name for name, passed in checks.items() if not passed)
        if self.minimums_satisfied != (not failed):
            raise ValueError("minimums_satisfied does not match receipt-derived evidence")
        if self.state == "COMPLETE" and failed:
            raise ValueError(f"complete state cannot miss process minimums: {','.join(failed)}")
        if len({row.option_id for row in self.next_prompt_options}) != len(
            self.next_prompt_options
        ):
            raise ValueError("option_id values must be unique")
        return self


def _short(digest: str) -> str:
    return f"{digest[:8]}...{digest[-4:]}"


def _count(value: int, singular: str, plural: str | None = None) -> str:
    return f"{value} {singular if value == 1 else (plural or singular + 's')}"


def render_human_oracle(surface: HumanOracleSurface | dict[str, object]) -> bytes:
    value = (
        surface
        if isinstance(surface, HumanOracleSurface)
        else HumanOracleSurface.model_validate(surface)
    )
    counts = value.execution
    lines = [
        f"# {value.headline}",
        "",
        value.summary,
        "",
        f"**Status:** {value.state.replace('_', ' ').title()} — no work is authorized by this screen.",
        (
            "**Actually ran:** "
            f"{_count(counts.model_calls, 'model call')} · {_count(counts.agents, 'agent')} · "
            f"{_count(counts.subagents, 'subagent')} · "
            f"{_count(counts.subsubagents, 'subsubagent')} · "
            f"{_count(counts.deeper_agents, 'deeper agent')} · "
            f"{_count(counts.tool_operations, 'tool operation')} · "
            f"{_count(counts.retries, 'retry', 'retries')} · "
            f"{_count(counts.failures, 'failure', 'failures')}"
        ),
        f"**Execution receipt:** `{_short(counts.source_receipt_sha256)}`",
        "",
        "## Models actually observed",
        "",
    ]
    if value.models:
        for row in value.models:
            lines.append(
                f"- `{row.route_id}`: {row.model_observed} via {row.provider} — "
                f"{row.status.lower()}, {row.call_count} call(s), receipt `{_short(row.receipt_sha256)}`"
            )
    else:
        lines.append("- None.")
    lines.extend(["", "## Agent tree actually observed", ""])
    if value.agent_runs:
        for row in sorted(value.agent_runs, key=lambda item: (item.depth, item.agent_id)):
            parent = f", parent `{row.parent_agent_id}`" if row.parent_agent_id else ""
            route = f", route `{row.model_route_id}`" if row.model_route_id else ""
            lines.append(
                f"- depth {row.depth} · `{row.agent_id}`{parent}{route} — "
                f"{row.status.lower()}, receipt `{_short(row.receipt_sha256)}`"
            )
    else:
        lines.append("- None.")
    lines.extend(["", "## Python tools actually observed", ""])
    if value.python_tools:
        for row in value.python_tools:
            lines.append(
                f"- `{row.tool_id}` / `{row.operation}` — {row.call_count} call(s), "
                f"{row.status.lower()}, receipt `{_short(row.receipt_sha256)}`"
            )
    else:
        lines.append("- None.")
    lines.extend(["", "## Skills and waves actually observed", ""])
    for row in value.skills:
        lines.append(
            f"- skill `{row.skill_id}` — {row.call_count} call(s), {row.status.lower()}, "
            f"receipt `{_short(row.receipt_sha256)}`"
        )
    for row in value.waves:
        lines.append(
            f"- {row.profile.lower()} wave `{row.wave_id}` — {row.status.lower()}, "
            f"receipt `{_short(row.receipt_sha256)}`"
        )
    if not value.skills and not value.waves:
        lines.append("- None.")
    lines.extend(["", "## Declared process minimums", ""])
    status = "met" if value.minimums_satisfied else "not met"
    lines.append(f"- Profile `{value.minimums.profile_id}` — **{status}**")
    lines.append(
        "- Minimums: "
        f"{value.minimums.distinct_providers} provider(s), "
        f"{value.minimums.model_calls} model call(s), "
        f"{value.minimums.agents} agent(s), "
        f"{value.minimums.subagents} subagent(s), "
        f"{value.minimums.subsubagents} subsubagent(s), "
        f"{value.minimums.python_tool_calls} Python tool call(s)"
    )
    lines.extend(["", "## What ran", ""])
    lines.extend(f"- {item}" for item in value.what_ran)
    if not value.what_ran:
        lines.append("- Nothing was accepted as run evidence.")
    lines.extend(["", "## Failures and unknowns", ""])
    if value.failures_and_unknowns:
        for item in value.failures_and_unknowns:
            lines.append(f"- **{item.reason_code}:** {item.plain_language}")
            lines.append(f"  - Impact: {item.impact}")
            if item.next_test:
                lines.append(f"  - Next check: {item.next_test}")
    else:
        lines.append("- No failure was recorded. This does not prove there was none.")
    lines.extend(
        [
            "",
            "## Decision needed",
            "",
            value.decision_needed,
            "",
            "## Proposed next actions and prompts",
            "",
        ]
    )
    for index, option in enumerate(value.next_prompt_options, start=1):
        lines.extend(
            [
                f"### {index}. {option.title}",
                "",
                f"**Combines:** {'; '.join(option.combines_actions)}",
            ]
        )
        if option.framing_mmm_ids:
            lines.append(f"**MMM framing:** {', '.join(option.framing_mmm_ids)}")
        lines.extend(["", option.prompt_text, ""])
    lines.extend(
        [
            *( [value.closing_summary, ""] if value.closing_summary else [] ),
            "## Boundary",
            "",
            f"- Raw prompt: `{_short(value.raw_prompt_sha256)}`",
            f"- Consumed map snapshot: `{_short(value.map_snapshot_sha256)}`",
            f"- Bound map return: `{_short(value.map_return_sha256)}`",
            f"- Claim ceiling: {value.claim_ceiling}",
            "- Execution authorized: false",
            "- Promotion allowed: false",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def human_oracle_identity(surface: HumanOracleSurface | dict[str, object]) -> str:
    value = (
        surface
        if isinstance(surface, HumanOracleSurface)
        else HumanOracleSurface.model_validate(surface)
    )
    return sha256_bytes(
        canonical_json_bytes(value.model_dump(mode="json", by_alias=True))
    )


def _validated_surface_and_map(
    task: TaskSpec,
    workspace: dict[str, bytes],
    *,
    output_paths: list[str],
) -> tuple[HumanOracleSurface, bytes, dict[str, object], dict[str, dict[str, object]]]:
    if task.input_paths != [INPUT_PATH, MAP_PACKET_PATH, MAP_RETURN_PATH] or task.output_paths != output_paths:
        raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_PATH_CONTRACT", task.task_id)
    raw = strict_json_loads(workspace[INPUT_PATH], label=INPUT_PATH)
    try:
        surface = HumanOracleSurface.model_validate(raw)
    except ValidationError as exc:
        raise ZipJobRefusal(
            "REFUSE_HUMAN_ORACLE_SURFACE_INVALID",
            str(exc.errors(include_url=False)),
        ) from exc
    map_packet = workspace[MAP_PACKET_PATH]
    map_return = workspace[MAP_RETURN_PATH]
    from .operation_ids import KNOWN_OPERATION_IDS
    from .runtime import execute_packet

    validated_packet = validate_packet(map_packet, known_operations=set(KNOWN_OPERATION_IDS))
    if len(validated_packet.tasks) != 1 or any(
        row.operation != "probe_tool_field_v1" for row in validated_packet.tasks
    ):
        raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_MAP_OPERATION")
    if execute_packet(map_packet).return_zip_bytes != map_return:
        raise ZipJobRefusal("HOLD_HUMAN_ORACLE_MAP_REPLAY_MISMATCH")
    validate_return_zip(
        map_return,
        expected_input_sha256=sha256_bytes(map_packet),
        input_packet_bytes=map_packet,
    )
    if sha256_bytes(map_return) != surface.map_return_sha256:
        raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_MAP_RETURN_DIGEST")
    with zipfile.ZipFile(io.BytesIO(map_return), "r") as archive:
        try:
            quotient_bytes = archive.read(MAP_QUOTIENT_PATH)
        except KeyError as exc:
            raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_MAP_OUTPUT_MISSING") from exc
    if sha256_bytes(quotient_bytes) != surface.map_snapshot_sha256:
        raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_MAP_SNAPSHOT_DIGEST")
    quotient = strict_json_loads(quotient_bytes, label=MAP_QUOTIENT_PATH)
    if not isinstance(quotient, dict) or quotient.get("schema") != "constraintbox.measured_tool_quotient.v1":
        raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_MAP_SCHEMA")
    rankings = quotient.get("rankings")
    if not isinstance(rankings, list):
        raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_MAP_SCHEMA")
    by_tool = {
        row.get("tool_id"): row
        for row in rankings
        if isinstance(row, dict) and isinstance(row.get("tool_id"), str)
    }
    for tool_id in REQUIRED_OPERATION_TOOL_IDS:
        row = by_tool.get(tool_id)
        if not isinstance(row, dict) or row.get("mapping_status") != "OPERATION_MAPPED":
            raise ZipJobRefusal("HOLD_HUMAN_ORACLE_TOOL_UNMAPPED", tool_id)
        if not all(row.get(key) is True for key in ("imported", "version_match", "replay_stable", "severance_refused")):
            raise ZipJobRefusal("HOLD_HUMAN_ORACLE_TOOL_EVIDENCE_INCOMPLETE", tool_id)
    return surface, quotient_bytes, quotient, by_tool


def _validated_operation_evidence(workspace: dict[str, bytes]) -> dict[str, dict[str, object]]:
    from .operation_ids import KNOWN_OPERATION_IDS
    from .runtime import execute_packet

    operation_packet = workspace[OPERATION_PACKET_PATH]
    operation_return = workspace[OPERATION_RETURN_PATH]
    validated_packet = validate_packet(
        operation_packet, known_operations=set(KNOWN_OPERATION_IDS)
    )
    if len(validated_packet.tasks) != 1 or any(
        row.operation != "operation_probe_field_v1" for row in validated_packet.tasks
    ):
        raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_OPERATION_EVIDENCE_ROUTE")
    if execute_packet(operation_packet).return_zip_bytes != operation_return:
        raise ZipJobRefusal("HOLD_HUMAN_ORACLE_OPERATION_EVIDENCE_REPLAY_MISMATCH")
    validate_return_zip(
        operation_return,
        expected_input_sha256=sha256_bytes(operation_packet),
        input_packet_bytes=operation_packet,
    )
    with zipfile.ZipFile(io.BytesIO(operation_return), "r") as archive:
        try:
            field_bytes = archive.read(OPERATION_FIELD_PATH)
            event_bytes = archive.read(OPERATION_EVENTS_PATH)
        except KeyError as exc:
            raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_OPERATION_EVIDENCE_MISSING") from exc
    field = strict_json_loads(field_bytes, label=OPERATION_FIELD_PATH)
    if not isinstance(field, dict) or field.get("schema") != "constraintbox.operation_probe_field.v1":
        raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_OPERATION_EVIDENCE_SCHEMA")
    events = []
    for raw_line in event_bytes.splitlines():
        row = strict_json_loads(raw_line, label=OPERATION_EVENTS_PATH)
        if not isinstance(row, dict):
            raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_OPERATION_EVENT_SHAPE")
        supplied = row.get("event_id")
        body = {key: value for key, value in row.items() if key != "event_id"}
        if supplied != sha256_bytes(canonical_json_bytes(body)):
            raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_OPERATION_EVENT_ID")
        events.append(row)
    event_ids = [row["event_id"] for row in events]
    if len(set(event_ids)) != len(event_ids):
        raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_OPERATION_EVENT_DUPLICATE")
    if field.get("event_count") != len(events):
        raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_OPERATION_EVENT_COUNT")
    tool_rows = field.get("tools")
    if not isinstance(tool_rows, list):
        raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_OPERATION_EVIDENCE_SCHEMA")
    by_tool = {
        row.get("tool_id"): row
        for row in tool_rows
        if isinstance(row, dict) and isinstance(row.get("tool_id"), str)
    }
    for tool_id in REQUIRED_OPERATION_TOOL_IDS:
        row = by_tool.get(tool_id)
        if not isinstance(row, dict) or row.get("mapping_status") != "OPERATION_MAPPED":
            raise ZipJobRefusal("HOLD_HUMAN_ORACLE_OPERATION_TOOL_UNMAPPED", tool_id)
        probe = row.get("single_probe")
        if not isinstance(probe, dict) or not all(
            probe.get(key) is True
            for key in ("positive_succeeded", "replay_stable", "settled")
        ):
            raise ZipJobRefusal("HOLD_HUMAN_ORACLE_OPERATION_EVIDENCE_INCOMPLETE", tool_id)
        observed = [event for event in events if event.get("tool_id") == tool_id]
        if not any(event.get("scenario") == "boundary" for event in observed):
            raise ZipJobRefusal("HOLD_HUMAN_ORACLE_OPERATION_BOUNDARY_MISSING", tool_id)
        if not any(
            event.get("scenario") == "mutation" and event.get("status") == event.get("expected_status")
            for event in observed
        ):
            raise ZipJobRefusal("HOLD_HUMAN_ORACLE_OPERATION_MUTATION_MISSING", tool_id)
    return by_tool


def run_human_oracle(
    task: TaskSpec,
    workspace: dict[str, bytes],
) -> dict[str, bytes]:
    surface, _, _, _ = _validated_surface_and_map(
        task, workspace, output_paths=[OUTPUT_PATH]
    )
    return {OUTPUT_PATH: render_human_oracle(surface)}


def run_human_oracle_map_update(
    task: TaskSpec,
    workspace: dict[str, bytes],
) -> dict[str, bytes]:
    """Render the human form and append one map observation from the same run."""

    expected_inputs = [
        INPUT_PATH,
        MAP_PACKET_PATH,
        MAP_RETURN_PATH,
        OPERATION_PACKET_PATH,
        OPERATION_RETURN_PATH,
    ]
    output_paths = [OUTPUT_PATH, MAP_DELTA_OUTPUT_PATH, UPDATED_MAP_OUTPUT_PATH]
    if task.input_paths != expected_inputs:
        raise ZipJobRefusal("REFUSE_HUMAN_ORACLE_PATH_CONTRACT", task.task_id)
    map_task = task.model_copy(update={"input_paths": expected_inputs[:3]})
    surface, quotient_bytes, _, by_tool = _validated_surface_and_map(
        map_task, workspace, output_paths=output_paths
    )
    operation_by_tool = _validated_operation_evidence(workspace)
    report = render_human_oracle(surface)
    from .tool_field_delta import apply_map_delta, build_map_delta, make_map_fact

    boundary_facts = []
    refusal_facts = []
    replay_facts = []
    for tool_id in REQUIRED_OPERATION_TOOL_IDS:
        row = by_tool[tool_id]
        operation_row = operation_by_tool[tool_id]
        evidence_sha256 = sha256_bytes(canonical_json_bytes(operation_row))
        boundary_facts.append(
            make_map_fact(
                fact_kind="boundary",
                tool_id=tool_id,
                observed=bool(row.get("imported") and row.get("version_match")),
                evidence_sha256=evidence_sha256,
                detail="validated import and locked-version boundary",
            )
        )
        refusal_facts.append(
            make_map_fact(
                fact_kind="refusal",
                tool_id=tool_id,
                observed=bool(row.get("severance_refused")),
                evidence_sha256=evidence_sha256,
                detail="validated severance refusal",
            )
        )
        replay_facts.append(
            make_map_fact(
                fact_kind="replay",
                tool_id=tool_id,
                observed=bool(row.get("replay_stable")),
                evidence_sha256=evidence_sha256,
                detail="validated tool-field replay observation",
            )
        )
    delta = build_map_delta(
        prior_map_bytes=quotient_bytes,
        prior_packet_bytes=workspace[MAP_PACKET_PATH],
        prior_return_bytes=workspace[MAP_RETURN_PATH],
        prior_quotient_bytes=quotient_bytes,
        operation_id="render_human_oracle_map_update_v1",
        operation_result="OBSERVED",
        operation_result_bytes=report,
        required_tool_ids=list(REQUIRED_OPERATION_TOOL_IDS),
        boundary_facts=boundary_facts,
        refusal_facts=refusal_facts,
        replay_facts=replay_facts,
        source_sha256=runtime_source_sha256(),
    )
    updated_map = apply_map_delta(quotient_bytes, delta)
    return {
        OUTPUT_PATH: report,
        MAP_DELTA_OUTPUT_PATH: delta,
        UPDATED_MAP_OUTPUT_PATH: updated_map,
    }


def build_human_oracle_packet(
    surface: HumanOracleSurface | dict[str, object],
    *,
    map_packet: bytes,
    map_return: bytes,
) -> bytes:
    value = (
        surface
        if isinstance(surface, HumanOracleSurface)
        else HumanOracleSurface.model_validate(surface)
    )
    task = {
        "schema": "constraintbox.zip_task.v1",
        "task_id": "render-human-oracle",
        "sequence": 0,
        "operation": "render_human_oracle_v2",
        "input_paths": [INPUT_PATH, MAP_PACKET_PATH, MAP_RETURN_PATH],
        "output_paths": [OUTPUT_PATH],
        "depends_on": [],
        "parameters": {},
        "preload_files": [],
    }
    manifest = {
        "schema": "constraintbox.zip_job.v1",
        "job_id": f"human-oracle-{value.run_id}",
        "task_execution_order": [TASK_PATH],
        "required_output_file_list": [OUTPUT_PATH],
        "allowed_operations": ["render_human_oracle_v2"],
        "allowed_child_job_ids": [],
        "max_child_depth": 0,
        "claim_ceiling": (
            "local_deterministic_zip_execution_only;not_model_execution;"
            "not_admission;not_release"
        ),
    }
    return build_packet(
        manifest,
        {
            "00_RUN_ME_FIRST.md": (
                b"# Human oracle surface\n\n"
                b"ConstraintBox validates the structured surface and renders it. "
                b"This packet cannot authorize execution or promotion.\n"
            ),
            INPUT_PATH: canonical_json_bytes(
                value.model_dump(mode="json", by_alias=True)
            ),
            MAP_PACKET_PATH: map_packet,
            MAP_RETURN_PATH: map_return,
            TASK_PATH: canonical_json_bytes(task),
        },
    )


def build_human_oracle_map_update_packet(
    surface: HumanOracleSurface | dict[str, object],
    *,
    map_packet: bytes,
    map_return: bytes,
    operation_packet: bytes,
    operation_return: bytes,
) -> bytes:
    value = (
        surface
        if isinstance(surface, HumanOracleSurface)
        else HumanOracleSurface.model_validate(surface)
    )
    output_paths = [OUTPUT_PATH, MAP_DELTA_OUTPUT_PATH, UPDATED_MAP_OUTPUT_PATH]
    task = {
        "schema": "constraintbox.zip_task.v1",
        "task_id": "render-human-oracle-map-update",
        "sequence": 0,
        "operation": "render_human_oracle_map_update_v1",
        "input_paths": [
            INPUT_PATH,
            MAP_PACKET_PATH,
            MAP_RETURN_PATH,
            OPERATION_PACKET_PATH,
            OPERATION_RETURN_PATH,
        ],
        "output_paths": output_paths,
        "depends_on": [],
        "parameters": {},
        "preload_files": [],
    }
    manifest = {
        "schema": "constraintbox.zip_job.v1",
        "job_id": f"human-oracle-map-update-{value.run_id}",
        "task_execution_order": [MAP_UPDATE_TASK_PATH],
        "required_output_file_list": output_paths,
        "allowed_operations": ["render_human_oracle_map_update_v1"],
        "allowed_child_job_ids": [],
        "max_child_depth": 0,
        "claim_ceiling": (
            "local_append_only_map_observation;not_producer_authenticity;"
            "not_tool_rank;not_admission;not_release"
        ),
    }
    return build_packet(
        manifest,
        {
            "00_RUN_ME_FIRST.md": (
                b"# Human oracle map update\n\n"
                b"ConstraintBox replays the exact local map packet, renders the human form, "
                b"and appends one observational delta. It authorizes no work or promotion.\n"
            ),
            INPUT_PATH: canonical_json_bytes(
                value.model_dump(mode="json", by_alias=True)
            ),
            MAP_PACKET_PATH: map_packet,
            MAP_RETURN_PATH: map_return,
            OPERATION_PACKET_PATH: operation_packet,
            OPERATION_RETURN_PATH: operation_return,
            MAP_UPDATE_TASK_PATH: canonical_json_bytes(task),
        },
    )
