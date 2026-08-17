"""Compile receipt-level execution evidence into the human surface shape.

This module is deliberately independent of :mod:`human_oracle`.  It is the
lower-level compiler that turns one run envelope into the fields consumed by
that surface.  A caller supplies *events*, not totals: one provider call, one
agent, one Python-tool invocation, or one lifecycle receipt per list item.
Totals are derived here and an event whose digest does not bind its canonical
body is refused.

The compiler records evidence.  It does not authorize execution, select a
provider, evaluate semantic correctness, or prove that an MMM or skill was
understood.  Provider and model strings are carried as run data only.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .protocol import (
    SHA256_RE,
    TaskSpec,
    ZipJobRefusal,
    canonical_json_bytes,
    sha256_bytes,
    strict_json_loads,
)


INPUT_SCHEMA = "constraintbox.execution-evidence-input.v1"
OUTPUT_SCHEMA = "constraintbox.human-oracle-surface.v2"
CLAIM_CEILING = (
    "receipt_compilation_only;not_semantic_admission;not_execution;"
    "not_mmm_cognition;not_promotion"
)

_STATUSES = frozenset({"COMPLETED", "FAILED", "HOLD", "CANCELLED"})
_DIGEST = "receipt_sha256"

# These are never valid on an event.  The compiler must see one event per
# operation and derive the aggregate itself.  ``minimums`` is intentionally
# excluded from this check because it is a run-data contract, not an observed
# count.
_AGGREGATE_KEYS = frozenset(
    {
        "counts",
        "execution",
        "model_calls",
        "model_count",
        "agent_count",
        "agents_count",
        "subagents_count",
        "subsubagents_count",
        "deeper_agents",
        "tool_operations",
        "tool_calls",
        "tool_count",
        "retry_count",
        "failure_count",
        "hold_count",
        "cancellation_count",
        "call_count",
        "calls",
        "count",
        "total_calls",
        "total_agents",
        "total_tools",
    }
)

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema",
        "run_id",
        "raw_prompt_sha256",
        "map_snapshot_sha256",
        "map_return_sha256",
        "required_map_tool_ids",
        "minimums",
        "provider_receipts",
        "agent_receipts",
        "python_tool_receipts",
        "retry_receipts",
        "hold_receipts",
        "failure_receipts",
        "cancellation_receipts",
        "skill_receipts",
        "wave_receipts",
        "hook_receipts",
        "source_currentness_receipts",
        "claim_ceiling",
    }
)

_ROW_ALIASES = {
    "provider_receipts": ("provider_receipts", "provider_calls"),
    "agent_receipts": ("agent_receipts", "agent_parentage_receipts"),
    "python_tool_receipts": ("python_tool_receipts", "tool_receipts"),
    "retry_receipts": ("retry_receipts", "retries"),
    "hold_receipts": ("hold_receipts", "holds"),
    "failure_receipts": ("failure_receipts", "failures"),
    "cancellation_receipts": ("cancellation_receipts", "cancellations"),
    "skill_receipts": ("skill_receipts", "skills"),
    "wave_receipts": ("wave_receipts", "waves"),
    "hook_receipts": ("hook_receipts", "hooks"),
    "source_currentness_receipts": (
        "source_currentness_receipts",
        "source_receipts",
        "currentness_receipts",
    ),
}


def _refuse(reason: str, detail: str = "") -> None:
    raise ZipJobRefusal(reason, detail)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _refuse("REFUSE_EXECUTION_EVIDENCE_SCHEMA", label)
    return value


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        _refuse("REFUSE_EXECUTION_EVIDENCE_DIGEST", label)
    return value


def _status(row: Mapping[str, Any], label: str) -> str:
    value = row.get("status")
    if value is None:
        disposition = row.get("disposition")
        value = {
            "OBSERVED": "COMPLETED",
            "COMPLETED": "COMPLETED",
            "FAILED": "FAILED",
            "HOLD": "HOLD",
            "REFUSED": "HOLD",
            "CANCELLED": "CANCELLED",
        }.get(disposition)
    if value not in _STATUSES:
        _refuse("REFUSE_EXECUTION_EVIDENCE_STATUS", label)
    return str(value)


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _refuse("REFUSE_EXECUTION_EVIDENCE_SCHEMA", label)
    return value


def _rows(
    envelope: Mapping[str, Any],
    category: str,
    seen: set[str],
) -> list[dict[str, Any]]:
    """Load and bind one event list.

    The event digest is the SHA-256 of its canonical JSON body with the
    ``receipt_sha256`` field removed.  This keeps the compiler useful for raw
    JSON receipts while making mutation and stale-digest tests deterministic.
    A producer that has raw receipt bytes can canonicalize those bytes into
    the event body before calling this function.
    """

    selected: object = None
    selected_name: str | None = None
    for name in _ROW_ALIASES[category]:
        if name in envelope:
            if selected is not None:
                _refuse("REFUSE_EXECUTION_EVIDENCE_DUPLICATE_CATEGORY", category)
            selected = envelope[name]
            selected_name = name
    if selected is None:
        return []
    if not isinstance(selected, list):
        _refuse("REFUSE_EXECUTION_EVIDENCE_SCHEMA", selected_name or category)
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(selected):
        row = dict(_mapping(raw, f"{category}[{index}]"))
        if _AGGREGATE_KEYS.intersection(row):
            keys = ",".join(sorted(_AGGREGATE_KEYS.intersection(row)))
            _refuse("REFUSE_EXECUTION_EVIDENCE_CALLER_COUNT", f"{category}[{index}]:{keys}")
        receipt = _digest(row.get(_DIGEST), f"{category}[{index}].{_DIGEST}")
        if receipt in seen:
            _refuse("REFUSE_EXECUTION_EVIDENCE_DUPLICATE_RECEIPT", receipt)
        body = dict(row)
        body.pop(_DIGEST, None)
        expected = sha256_bytes(canonical_json_bytes(body))
        if expected != receipt:
            _refuse("REFUSE_EXECUTION_EVIDENCE_RECEIPT_TAMPER", f"{category}[{index}]")
        seen.add(receipt)
        row[_DIGEST] = receipt
        rows.append(row)
    return rows


def _minimums(raw: object) -> dict[str, Any]:
    if raw is None:
        return {
            "profile_id": "default",
            "distinct_providers": 0,
            "model_calls": 0,
            "agents": 0,
            "subagents": 0,
            "subsubagents": 0,
            "python_tool_calls": 0,
            "required_skill_ids": [],
            "required_wave_ids": [],
        }
    value = dict(_mapping(raw, "minimums"))
    allowed = {
        "profile_id",
        "distinct_providers",
        "model_calls",
        "agents",
        "subagents",
        "subsubagents",
        "python_tool_calls",
        "required_skill_ids",
        "required_wave_ids",
    }
    if set(value) - allowed:
        _refuse("REFUSE_EXECUTION_EVIDENCE_MINIMUMS", "fields")
    result: dict[str, Any] = {
        "profile_id": _text(value.get("profile_id", "default"), "minimums.profile_id"),
    }
    for key in (
        "distinct_providers",
        "model_calls",
        "agents",
        "subagents",
        "subsubagents",
        "python_tool_calls",
    ):
        number = value.get(key, 0)
        if isinstance(number, bool) or not isinstance(number, int) or number < 0:
            _refuse("REFUSE_EXECUTION_EVIDENCE_MINIMUMS", f"minimums.{key}")
        result[key] = number
    for key in ("required_skill_ids", "required_wave_ids"):
        items = value.get(key, [])
        if not isinstance(items, list) or any(not isinstance(item, str) or not item for item in items):
            _refuse("REFUSE_EXECUTION_EVIDENCE_MINIMUMS", f"minimums.{key}")
        if len(items) != len(set(items)):
            _refuse("REFUSE_EXECUTION_EVIDENCE_MINIMUMS", f"minimums.{key}:duplicate")
        result[key] = list(items)
    return result


def _row_field(row: Mapping[str, Any], names: Sequence[str], label: str) -> object:
    for name in names:
        if name in row:
            return row[name]
    _refuse("REFUSE_EXECUTION_EVIDENCE_SCHEMA", label)


def _failure_item(
    row: Mapping[str, Any],
    *,
    default_reason: str,
    default_plain: str,
    default_impact: str,
    default_next: str,
) -> dict[str, Any]:
    reason = row.get("reason_code", default_reason)
    plain = row.get("plain_language", default_plain)
    impact = row.get("impact", default_impact)
    next_test = row.get("next_test", default_next)
    return {
        "reason_code": _text(reason, "failure.reason_code"),
        "plain_language": _text(plain, "failure.plain_language"),
        "impact": _text(impact, "failure.impact"),
        "next_test": _text(next_test, "failure.next_test") if next_test is not None else None,
    }


def _next_options(state: str, failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if failures:
        first = failures[0]["reason_code"]
        first_action = f"resolve {first}"
    else:
        first_action = "review the receipt-bound result"
    return [
        {
            "option_id": "repair-and-rerun",
            "title": "Repair the evidence path and rerun",
            "prompt_text": (
                "Review the listed evidence gaps, repair the deterministic path, "
                "and rerun the same operation with fresh receipts. Do not infer "
                f"success from prose; address {first_action}."
            ),
            "combines_actions": [
                "inspect receipt failures",
                "repair the bounded operation",
                "rerun with fresh evidence",
            ],
            "framing_mmm_ids": [],
            "preserves_raw_prompt": True,
        },
        {
            "option_id": "probe-and-compare",
            "title": "Probe the boundary and compare a second path",
            "prompt_text": (
                "Run a positive case plus mutation, duplicate, missing-parent, "
                "and replay negatives; compare the resulting receipt-derived "
                "forms and append only observations that change the map."
            ),
            "combines_actions": [
                "run mutation negatives",
                "compare an independent path",
                "append the observed map delta",
            ],
            "framing_mmm_ids": [],
            "preserves_raw_prompt": True,
        },
    ]


def compile_execution_evidence_v1(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Compile one receipt envelope into a HumanOracle-shaped object.

    All observed lists contain one event per invocation.  The returned
    ``call_count`` values are therefore compiler-derived ``1`` values, while
    the execution totals are sums over those rows.  Caller-provided totals,
    aggregate ``execution`` objects, and stale/tampered receipt digests are
    refused before a human surface can be rendered.
    """

    envelope = _mapping(raw, "evidence")
    if envelope.get("schema") != INPUT_SCHEMA:
        _refuse("REFUSE_EXECUTION_EVIDENCE_SCHEMA", "schema")
    if _AGGREGATE_KEYS.intersection(envelope):
        keys = ",".join(sorted(_AGGREGATE_KEYS.intersection(envelope)))
        _refuse("REFUSE_EXECUTION_EVIDENCE_CALLER_COUNT", keys)
    unknown = set(envelope) - _TOP_LEVEL_KEYS
    if unknown:
        _refuse("REFUSE_EXECUTION_EVIDENCE_SCHEMA", "fields:" + ",".join(sorted(unknown)))

    run_id = _text(envelope.get("run_id"), "run_id")
    raw_prompt_sha = _digest(envelope.get("raw_prompt_sha256"), "raw_prompt_sha256")
    map_snapshot_sha = _digest(envelope.get("map_snapshot_sha256"), "map_snapshot_sha256")
    map_return_sha = _digest(envelope.get("map_return_sha256"), "map_return_sha256")
    required_map_tools = envelope.get("required_map_tool_ids", [])
    if not isinstance(required_map_tools, list) or any(
        not isinstance(item, str) or not item for item in required_map_tools
    ):
        _refuse("REFUSE_EXECUTION_EVIDENCE_SCHEMA", "required_map_tool_ids")
    if len(required_map_tools) != len(set(required_map_tools)):
        _refuse("REFUSE_EXECUTION_EVIDENCE_SCHEMA", "required_map_tool_ids:duplicate")

    seen: set[str] = set()
    provider_rows = _rows(envelope, "provider_receipts", seen)
    agent_rows = _rows(envelope, "agent_receipts", seen)
    tool_rows = _rows(envelope, "python_tool_receipts", seen)
    retry_rows = _rows(envelope, "retry_receipts", seen)
    hold_rows = _rows(envelope, "hold_receipts", seen)
    failure_rows = _rows(envelope, "failure_receipts", seen)
    cancellation_rows = _rows(envelope, "cancellation_receipts", seen)
    skill_rows = _rows(envelope, "skill_receipts", seen)
    wave_rows = _rows(envelope, "wave_receipts", seen)
    hook_rows = _rows(envelope, "hook_receipts", seen)
    currentness_rows = _rows(envelope, "source_currentness_receipts", seen)

    # Provider events are deliberately one row per call.  A repeated route ID
    # would make the HumanOracle surface ambiguous and is refused rather than
    # silently inventing a route suffix.
    route_ids: set[str] = set()
    models: list[dict[str, Any]] = []
    completed_providers: set[str] = set()
    completed_model_calls = 0
    for index, row in enumerate(provider_rows):
        route = _text(
            _row_field(row, ("route_id", "provider_request_id", "request_id"), "provider.route_id"),
            "provider.route_id",
        )
        if route in route_ids:
            _refuse("REFUSE_EXECUTION_EVIDENCE_DUPLICATE_ROUTE", route)
        route_ids.add(route)
        provider = _text(row.get("provider"), f"provider[{index}].provider")
        requested = _text(
            _row_field(row, ("model_requested", "model"), f"provider[{index}].model_requested"),
            f"provider[{index}].model_requested",
        )
        observed_value = row.get("model_observed")
        if observed_value is None:
            observed_values = row.get("models_observed")
            if isinstance(observed_values, list) and observed_values:
                observed_value = observed_values[0]
        observed = (
            _text(observed_value, f"provider[{index}].model_observed")
            if observed_value is not None
            else "UNOBSERVED"
        )
        status = _status(row, f"provider[{index}].status")
        receipt = row[_DIGEST]
        models.append(
            {
                "route_id": route,
                "provider": provider,
                "model_requested": requested,
                "model_observed": observed,
                "call_count": 1,
                "status": status,
                "receipt_sha256": receipt,
            }
        )
        if status == "COMPLETED":
            completed_providers.add(provider)
            completed_model_calls += 1

    # Agent parentage is structural evidence, not a caller count.  Enforce a
    # strict depth step so a child cannot claim to be attached to a grandparent.
    agent_ids: set[str] = set()
    agent_meta: dict[str, tuple[int, str | None]] = {}
    agents: list[dict[str, Any]] = []
    for index, row in enumerate(agent_rows):
        agent_id = _text(row.get("agent_id"), f"agent[{index}].agent_id")
        if agent_id in agent_ids:
            _refuse("REFUSE_EXECUTION_EVIDENCE_DUPLICATE_AGENT", agent_id)
        agent_ids.add(agent_id)
        depth = row.get("depth")
        if isinstance(depth, bool) or not isinstance(depth, int) or depth < 0 or depth > 64:
            _refuse("REFUSE_EXECUTION_EVIDENCE_PARENTAGE", f"{agent_id}:depth")
        parent = row.get("parent_agent_id")
        if parent is not None:
            parent = _text(parent, f"agent[{index}].parent_agent_id")
        if depth == 0 and parent is not None:
            _refuse("REFUSE_EXECUTION_EVIDENCE_PARENTAGE", f"{agent_id}:root_parent")
        agent_meta[agent_id] = (depth, parent)
        model_route = row.get("model_route_id")
        if model_route is not None:
            model_route = _text(model_route, f"agent[{index}].model_route_id")
        agents.append(
            {
                "agent_id": agent_id,
                "parent_agent_id": parent,
                "depth": depth,
                "status": _status(row, f"agent[{index}].status"),
                "model_route_id": model_route,
                "receipt_sha256": row[_DIGEST],
            }
        )
    for agent_id, (depth, parent) in agent_meta.items():
        if depth > 0:
            if parent not in agent_meta:
                _refuse("REFUSE_EXECUTION_EVIDENCE_MISSING_PARENT", f"{agent_id}:{parent}")
            parent_depth = agent_meta[parent][0]
            if parent_depth != depth - 1:
                _refuse("REFUSE_EXECUTION_EVIDENCE_PARENTAGE", f"{agent_id}:depth_step")
    for row in agents:
        route_id = row["model_route_id"]
        if route_id is not None and route_id not in route_ids:
            _refuse(
                "REFUSE_EXECUTION_EVIDENCE_AGENT_ROUTE",
                f"{row['agent_id']}:{route_id}",
            )

    def _tool_rows() -> list[dict[str, Any]]:
        values: list[dict[str, Any]] = []
        for index, row in enumerate(tool_rows):
            values.append(
                {
                    "tool_id": _text(row.get("tool_id"), f"tool[{index}].tool_id"),
                    "operation": _text(
                        row.get("operation", row.get("operation_id")),
                        f"tool[{index}].operation",
                    ),
                    "call_count": 1,
                    "status": _status(row, f"tool[{index}].status"),
                    "receipt_sha256": row[_DIGEST],
                }
            )
        return values

    python_tools = _tool_rows()
    skills: list[dict[str, Any]] = []
    for index, row in enumerate(skill_rows):
        skills.append(
            {
                "skill_id": _text(row.get("skill_id"), f"skill[{index}].skill_id"),
                "call_count": 1,
                "status": _status(row, f"skill[{index}].status"),
                "receipt_sha256": row[_DIGEST],
            }
        )
    waves: list[dict[str, Any]] = []
    for index, row in enumerate(wave_rows):
        profile = row.get("profile", "LEAN")
        if profile not in {"LEAN", "FULL"}:
            _refuse("REFUSE_EXECUTION_EVIDENCE_SCHEMA", f"wave[{index}].profile")
        waves.append(
            {
                "wave_id": _text(row.get("wave_id"), f"wave[{index}].wave_id"),
                "profile": profile,
                "status": _status(row, f"wave[{index}].status"),
                "receipt_sha256": row[_DIGEST],
            }
        )

    # Structured lifecycle evidence is converted into plain-language failure
    # rows.  The prose comes from the receipt; when absent, deterministic text
    # makes the omission visible without pretending an LLM supplied a report.
    failures: list[dict[str, Any]] = []
    currentness_valid = bool(currentness_rows)
    for row in failure_rows:
        failures.append(
            _failure_item(
                row,
                default_reason="REFUSE_RECORDED_FAILURE",
                default_plain="A failure receipt was recorded.",
                default_impact="The operation cannot be treated as complete without a repair or explicit hold.",
                default_next="Inspect the bound failure receipt and rerun the smallest affected operation.",
            )
        )
    for row in hold_rows:
        failures.append(
            _failure_item(
                row,
                default_reason="HOLD_RECORDED",
                default_plain="A deterministic hold was recorded.",
                default_impact="The run is not authorized to proceed from this evidence.",
                default_next="Resolve the hold condition and recompile from fresh receipts.",
            )
        )
    for row in cancellation_rows:
        failures.append(
            _failure_item(
                row,
                default_reason="CANCELLED_RECORDED",
                default_plain="The run or one of its operations was cancelled.",
                default_impact="Cancellation is not a successful execution result.",
                default_next="Start a new receipt-bound run if the work is still wanted.",
            )
        )
    for row in currentness_rows:
        before = _digest(
            row.get("source_before_sha256", row.get("source_sha256")),
            "currentness.source_before_sha256",
        )
        after = _digest(
            row.get("source_after_sha256", row.get("source_sha256")),
            "currentness.source_after_sha256",
        )
        current = row.get("current", before == after)
        current_status = (
            _status(row, "currentness.status")
            if "status" in row or "disposition" in row
            else "COMPLETED"
        )
        if current_status != "COMPLETED" or current is not True or before != after:
            currentness_valid = False
            failures.append(
                _failure_item(
                    row,
                    default_reason="HOLD_SOURCE_CURRENTNESS_DRIFT",
                    default_plain="The runtime source changed during or around the evidence interval.",
                    default_impact="The receipts cannot be claimed as a current execution of one source state.",
                    default_next="Rerun after freezing the runtime source interval and bind both endpoints.",
                )
            )
    if not currentness_rows:
        failures.append(
            {
                "reason_code": "HOLD_SOURCE_CURRENTNESS_MISSING",
                "plain_language": "No source-currentness receipt was supplied.",
                "impact": "The execution interval cannot be shown to belong to one current runtime.",
                "next_test": "Capture matching source-before and source-after receipts around a fresh run.",
            }
        )
    for row in provider_rows:
        status = _status(row, "provider.status")
        if status != "COMPLETED":
            failures.append(
                _failure_item(
                    row,
                    default_reason=f"PROVIDER_{status}",
                    default_plain=f"A provider call ended in {status.lower()} rather than completed.",
                    default_impact="This call is visible but does not count toward completed model minimums.",
                    default_next="Inspect the provider receipt and rerun only the failed call.",
                )
            )
    for row in hook_rows:
        if _status(row, "hook.status") != "COMPLETED":
            failures.append(
                _failure_item(
                    row,
                    default_reason="HOLD_HOOK_RECEIPT",
                    default_plain="A hook seam did not complete with a receipt.",
                    default_impact="The host relay or authority-removal seam is not evidenced.",
                    default_next="Repeat the host hook phase and capture its receipt without granting semantic authority.",
                )
            )

    minimums = _minimums(envelope.get("minimums"))
    depth_counts = (
        sum(row["depth"] == 0 for row in agents),
        sum(row["depth"] == 1 for row in agents),
        sum(row["depth"] == 2 for row in agents),
        sum(row["depth"] > 2 for row in agents),
    )
    completed_depth_counts = (
        sum(row["depth"] == 0 and row["status"] == "COMPLETED" for row in agents),
        sum(row["depth"] == 1 and row["status"] == "COMPLETED" for row in agents),
        sum(row["depth"] == 2 and row["status"] == "COMPLETED" for row in agents),
        sum(row["depth"] > 2 and row["status"] == "COMPLETED" for row in agents),
    )
    completed_tools = sum(row["call_count"] for row in python_tools if row["status"] == "COMPLETED")
    completed_skill_ids = {row["skill_id"] for row in skills if row["status"] == "COMPLETED"}
    completed_wave_ids = {row["wave_id"] for row in waves if row["status"] == "COMPLETED"}
    checks = {
        "distinct_providers": len(completed_providers) >= minimums["distinct_providers"],
        "model_calls": completed_model_calls >= minimums["model_calls"],
        "agents": completed_depth_counts[0] >= minimums["agents"],
        "subagents": completed_depth_counts[1] >= minimums["subagents"],
        "subsubagents": completed_depth_counts[2] >= minimums["subsubagents"],
        "python_tool_calls": completed_tools >= minimums["python_tool_calls"],
        "required_skill_ids": set(minimums["required_skill_ids"]).issubset(completed_skill_ids),
        "required_wave_ids": set(minimums["required_wave_ids"]).issubset(completed_wave_ids),
    }
    minimums_satisfied = all(checks.values())
    source_current = currentness_valid
    cancellation_present = bool(cancellation_rows) or any(
        _status(row, "cancellation.status") == "CANCELLED"
        for row in provider_rows + agent_rows + tool_rows + skill_rows + wave_rows
    )
    hold_present = bool(hold_rows) or not source_current or not minimums_satisfied
    if cancellation_present:
        state = "CANCELLED"
    elif hold_present or failures:
        state = "HOLD"
    else:
        state = "COMPLETE"

    evidence_digest = sha256_bytes(canonical_json_bytes(dict(envelope)))
    what_ran = [
        f"{len(provider_rows)} provider call receipt(s) compiled",
        f"{len(agents)} agent parentage receipt(s) compiled",
        f"{len(python_tools)} Python tool receipt(s) compiled",
        f"{len(retry_rows)} retry receipt(s) compiled",
        f"{len(skill_rows)} skill receipt(s) compiled",
        f"{len(wave_rows)} wave receipt(s) compiled",
        f"{len(hook_rows)} hook receipt(s) compiled",
        f"{len(currentness_rows)} source-currentness receipt(s) compiled",
    ]
    summary = (
        f"Compiled {len(provider_rows)} provider call(s), {len(agents)} agent(s), "
        f"{len(python_tools)} Python tool call(s), and {len(failures)} recorded issue(s) "
        "from receipt-bound events."
    )
    if state == "COMPLETE":
        decision = "The evidence is internally complete, but this form still authorizes no execution or promotion."
    elif state == "CANCELLED":
        decision = "The run was cancelled. Start a new receipt-bound run before asking for downstream work."
    else:
        decision = "Resolve the listed evidence gaps and recompile; this HOLD authorizes no downstream work."
    surface: dict[str, Any] = {
        "schema": OUTPUT_SCHEMA,
        "run_id": run_id,
        "state": state,
        "headline": f"Execution evidence: {state}",
        "summary": summary,
        "closing_summary": (
            f"Receipt compiler digest `{evidence_digest[:8]}...{evidence_digest[-4:]}`. "
            "Model/provider identity is run data; no semantic admission was performed."
        ),
        "raw_prompt_sha256": raw_prompt_sha,
        "map_snapshot_sha256": map_snapshot_sha,
        "map_return_sha256": map_return_sha,
        "required_map_tool_ids": list(required_map_tools),
        "execution": {
            "model_calls": len(provider_rows),
            "agents": depth_counts[0],
            "subagents": depth_counts[1],
            "subsubagents": depth_counts[2],
            "deeper_agents": depth_counts[3],
            "tool_operations": len(python_tools),
            "retries": len(retry_rows),
            "failures": len(failure_rows),
            "source_receipt_sha256": evidence_digest,
        },
        "models": models,
        "agent_runs": agents,
        "python_tools": python_tools,
        "skills": skills,
        "waves": waves,
        "minimums": minimums,
        "minimums_satisfied": minimums_satisfied,
        "what_ran": what_ran,
        "failures_and_unknowns": failures,
        "decision_needed": decision,
        "next_prompt_options": _next_options(state, failures),
        "claim_ceiling": str(envelope.get("claim_ceiling") or CLAIM_CEILING),
        "execution_authorized": False,
        "promotion_allowed": False,
    }
    return surface


compile_execution_evidence = compile_execution_evidence_v1


def run_compile_execution_evidence_v1(
    task: TaskSpec,
    workspace: dict[str, bytes],
) -> dict[str, bytes]:
    """ZIP operation adapter for the receipt compiler."""

    if len(task.input_paths) != 1 or len(task.output_paths) != 1:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    source_path = task.input_paths[0]
    value = strict_json_loads(workspace[source_path], label=source_path)
    if not isinstance(value, dict):
        raise ZipJobRefusal("REFUSE_EXECUTION_EVIDENCE_SCHEMA", source_path)
    return {task.output_paths[0]: canonical_json_bytes(compile_execution_evidence_v1(value))}

__all__ = [
    "compile_execution_evidence_v1",
    "compile_execution_evidence",
    "run_compile_execution_evidence_v1",
    "INPUT_SCHEMA",
    "OUTPUT_SCHEMA",
]
