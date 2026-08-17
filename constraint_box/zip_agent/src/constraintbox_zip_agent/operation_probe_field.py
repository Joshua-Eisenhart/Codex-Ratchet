"""Small, replayable operation probes for the candidate tool field.

The older tool field proves that a distribution can be imported.  That is useful
installation evidence, but it cannot establish that the distribution is useful
to a CB operation.  This module deliberately starts at the next boundary:
only a manifest row with an explicit ``operation_probe`` is executed.  Rows
without one remain ``UNMAPPED_GENERIC_ONLY`` even when their import succeeds.

The operation description is data, not executable Python.  It names a module,
one attribute, and JSON arguments.  The runner imports that module, calls the
named attribute, and records a normalized result.  Positive, replay, mutation,
boundary, cohort-ablation, and AB/BA observations are all evidence about this
packet only.  They are never a permanent core list or an admission decision.
"""

from __future__ import annotations

import argparse
import copy
import importlib
import importlib.metadata
import inspect
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Sequence

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .protocol import (
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    sha256_bytes,
    strict_json_loads,
)


CLAIM_CEILING = (
    "local_operation_probe_observations_only;not_global_tool_rank;"
    "not_core;not_admission;not_model_execution;not_portability;not_release"
)

EVENT_OUTPUT = "output/operation_probe_events.jsonl"
FIELD_OUTPUT = "output/operation_probe_field.json"
RANKING_OUTPUT = "output/operation_probe_rankings.json"
SUMMARY_OUTPUT = "output/operation_probe_summary.json"
OUTPUTS = (EVENT_OUTPUT, FIELD_OUTPUT, RANKING_OUTPUT, SUMMARY_OUTPUT)

_STATUS_SUCCEEDED = "SUCCEEDED"
_STATUS_REFUSED = "REFUSED"
_STATUS_IMPORT_REFUSED = "IMPORT_REFUSED"
_STATUS_SPEC_REFUSED = "SPEC_REFUSED"
_EXPECTED_STATUSES = frozenset({_STATUS_SUCCEEDED, _STATUS_REFUSED})


class OperationProbeFieldRequest(BaseModel):
    """Bounded controls for one deterministic operation-probe field."""

    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    schema_: Literal["constraintbox.operation_probe_field_request.v1"] = Field(
        alias="schema"
    )
    seed: int = Field(ge=0, le=2**31 - 1)
    cohort_size: int = Field(default=4, ge=1, le=16)
    cohort_limit: int = Field(default=32, ge=1, le=512)
    max_pairs: int = Field(default=64, ge=0, le=2048)
    max_ablation_tools: int = Field(default=16, ge=0, le=64)


@dataclass(frozen=True)
class _Tool:
    tool_id: str
    distribution: str
    version: str
    import_name: str
    operation_raw: dict[str, Any] | None
    operation_source: str | None


@dataclass(frozen=True)
class _Case:
    name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    expected: str


@dataclass(frozen=True)
class _Operation:
    module: str
    callable_name: str
    positive: _Case
    mutations: tuple[_Case, ...]
    boundaries: tuple[_Case, ...]
    shared_input: _Case | None
    digest: str


def build_operation_probe_field_packet(
    *,
    request: bytes,
    manifest: bytes,
    operation_catalog: bytes,
    job_id: str = "operation-probe-field",
) -> bytes:
    """Build one model-free ZIP_JOB around the registered probe operation."""

    task_path = "tasks/operation-field.task.json"
    task = {
        "schema": "constraintbox.zip_task.v1",
        "task_id": "operation-field",
        "sequence": 0,
        "operation": "operation_probe_field_v1",
        "input_paths": [
            "inputs/request.json",
            "inputs/manifest.json",
            "inputs/operation_catalog.json",
        ],
        "output_paths": list(OUTPUTS),
        "depends_on": [],
        "parameters": {},
        "preload_files": [],
    }
    files = {
        task_path: canonical_json_bytes(task),
        "inputs/request.json": request,
        "inputs/manifest.json": manifest,
        "inputs/operation_catalog.json": operation_catalog,
    }
    manifest_fields = {
        "schema": "constraintbox.zip_job.v1",
        "job_id": job_id,
        "task_execution_order": [task_path],
        "required_output_file_list": list(OUTPUTS),
        "allowed_operations": ["operation_probe_field_v1"],
        "allowed_child_job_ids": [],
        "max_child_depth": 0,
        "claim_ceiling": (
            "local_deterministic_zip_execution_only;"
            "not_model_execution;not_admission;not_release"
        ),
    }
    return build_packet(manifest_fields, files)


def _object(data: bytes, label: str) -> dict[str, Any]:
    value = strict_json_loads(data, label=label)
    if not isinstance(value, dict):
        raise ZipJobRefusal("REFUSE_OPERATION_PROBE_INPUT_SHAPE", label)
    return value


def _request(value: dict[str, Any]) -> OperationProbeFieldRequest:
    schema = OperationProbeFieldRequest.model_json_schema()
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.path))
    if errors:
        raise ZipJobRefusal("REFUSE_OPERATION_PROBE_REQUEST_SCHEMA", errors[0].message)
    try:
        return OperationProbeFieldRequest.model_validate(value, strict=True)
    except ValidationError as exc:
        raise ZipJobRefusal("REFUSE_OPERATION_PROBE_REQUEST_TYPED", str(exc)) from exc


def _tools(manifest: dict[str, Any], prior: dict[str, Any]) -> list[_Tool]:
    raw = manifest.get("tools")
    if not isinstance(raw, list) or not raw:
        raise ZipJobRefusal("REFUSE_OPERATION_PROBE_MANIFEST_EMPTY")
    prior_specs = prior.get("operation_probes", {})
    if not isinstance(prior_specs, (dict, list)):
        raise ZipJobRefusal("REFUSE_OPERATION_PROBE_PRIOR_SPECS")
    if isinstance(prior_specs, list):
        converted: dict[str, Any] = {}
        for item in prior_specs:
            if isinstance(item, dict) and isinstance(item.get("tool_id"), str):
                converted[item["tool_id"]] = item.get("operation_probe") or item.get("probe")
        prior_specs = converted
    rows: list[_Tool] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ZipJobRefusal("REFUSE_OPERATION_PROBE_MANIFEST_ROW", str(index))
        distribution = item.get("locked_distribution") or item.get("distribution")
        version = item.get("locked_version") or item.get("version")
        imports = item.get("import_names")
        if not (
            isinstance(distribution, str)
            and distribution
            and isinstance(version, str)
            and version
            and isinstance(imports, list)
            and len(imports) == 1
            and isinstance(imports[0], str)
            and imports[0]
        ):
            raise ZipJobRefusal("REFUSE_OPERATION_PROBE_MANIFEST_ROW", str(index))
        tool_id = item.get("tool_id") or distribution
        if not isinstance(tool_id, str) or not tool_id or tool_id in seen:
            raise ZipJobRefusal("REFUSE_OPERATION_PROBE_TOOL_ID", str(index))
        seen.add(tool_id)
        operation = item.get("operation_probe")
        if operation is None:
            operation = item.get("operation_probes")
        operation_source = "manifest" if operation is not None else None
        if operation is None and isinstance(prior_specs, dict) and tool_id in prior_specs:
            operation = prior_specs[tool_id]
            operation_source = "prior_operation_catalog"
            if isinstance(operation, dict) and "operation_probe" in operation:
                operation = operation["operation_probe"]
        if operation is not None and not isinstance(operation, dict):
            # Keep the candidate in the field, but make the mapping failure
            # explicit.  An invalid operation description must not turn an
            # import-only row into an operation claim.
            operation = {"__invalid__": repr(operation)}
            operation_source = operation_source or "manifest"
        rows.append(
            _Tool(
                tool_id=tool_id,
                distribution=distribution,
                version=version,
                import_name=imports[0],
                operation_raw=operation,
                operation_source=operation_source,
            )
        )
    return sorted(rows, key=lambda row: row.tool_id)


def _case(value: Any, *, default_name: str, default_expected: str) -> _Case:
    if not isinstance(value, dict):
        raise ValueError("case must be an object")
    name = value.get("name", default_name)
    args = value.get("args", [])
    kwargs = value.get("kwargs", {})
    expected = value.get("expected", default_expected)
    if (
        not isinstance(name, str)
        or not name
        or not isinstance(args, list)
        or not isinstance(kwargs, dict)
        or expected not in _EXPECTED_STATUSES
    ):
        raise ValueError("invalid case")
    # Validate that the copied case is canonical JSON before it can be used as
    # a call argument.  This also rejects NaN/Infinity deterministically.
    canonical_json_bytes({"args": args, "kwargs": kwargs})
    return _Case(name=name, args=tuple(copy.deepcopy(args)), kwargs=copy.deepcopy(kwargs), expected=expected)


def _operation(tool: _Tool) -> tuple[_Operation | None, str | None]:
    raw = tool.operation_raw
    if raw is None:
        return None, "NO_EXPLICIT_OPERATION_PROBE"
    if "__invalid__" in raw:
        return None, "INVALID_OPERATION_PROBE_SPEC"
    # The explicit form is preferred.  A compact args/kwargs form makes it
    # easy to author a first probe while preserving the same evidence shape.
    module = raw.get("module") or raw.get("import_name")
    callable_name = raw.get("callable") or raw.get("attribute") or raw.get("symbol")
    if not isinstance(module, str) or not module or not isinstance(callable_name, str) or not callable_name:
        return None, "OPERATION_MODULE_OR_CALLABLE_MISSING"
    root = tool.import_name.split(".", 1)[0]
    if module != tool.import_name and not module.startswith(tool.import_name + ".") and module != root:
        return None, "OPERATION_MODULE_OUTSIDE_DECLARED_IMPORT"
    positive_raw = raw.get("positive")
    if positive_raw is None:
        positive_raw = {"args": raw.get("args", []), "kwargs": raw.get("kwargs", {})}
    try:
        positive = _case(positive_raw, default_name="positive", default_expected=_STATUS_SUCCEEDED)
        if positive.expected != _STATUS_SUCCEEDED:
            raise ValueError("positive case must expect SUCCEEDED")
        mutation_values = raw.get("mutations", raw.get("negative", []))
        boundary_values = raw.get("boundaries", raw.get("boundary", []))
        if not isinstance(mutation_values, list) or not isinstance(boundary_values, list):
            raise ValueError("mutation/boundary list")
        mutations = tuple(
            _case(item, default_name=f"mutation-{i}", default_expected=_STATUS_REFUSED)
            for i, item in enumerate(mutation_values)
        )
        boundaries = tuple(
            _case(item, default_name=f"boundary-{i}", default_expected=_STATUS_SUCCEEDED)
            for i, item in enumerate(boundary_values)
        )
        shared_raw = raw.get("shared_input")
        shared = (
            _case(shared_raw, default_name="shared", default_expected=_STATUS_SUCCEEDED)
            if shared_raw is not None
            else None
        )
    except (TypeError, ValueError, ZipJobRefusal) as exc:
        return None, f"INVALID_OPERATION_PROBE_SPEC:{type(exc).__name__}"
    normalized = {
        "module": module,
        "callable": callable_name,
        "positive": {"name": positive.name, "args": list(positive.args), "kwargs": positive.kwargs, "expected": positive.expected},
        "mutations": [
            {"name": item.name, "args": list(item.args), "kwargs": item.kwargs, "expected": item.expected}
            for item in mutations
        ],
        "boundaries": [
            {"name": item.name, "args": list(item.args), "kwargs": item.kwargs, "expected": item.expected}
            for item in boundaries
        ],
        "shared_input": (
            {"name": shared.name, "args": list(shared.args), "kwargs": shared.kwargs, "expected": shared.expected}
            if shared is not None
            else None
        ),
    }
    return (
        _Operation(
            module=module,
            callable_name=callable_name,
            positive=positive,
            mutations=mutations,
            boundaries=boundaries,
            shared_input=shared,
            digest=sha256_bytes(canonical_json_bytes(normalized)),
        ),
        None,
    )


def _normal(value: Any) -> Any:
    """Make common API results stable without trusting object repr strings."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            return {"type": "float", "non_finite": True}
        return value
    if isinstance(value, (list, tuple)):
        return [_normal(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normal(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (set, frozenset)):
        return sorted((_normal(item) for item in value), key=lambda item: canonical_json_bytes(item))
    if hasattr(value, "model_dump") and callable(value.model_dump):
        try:
            return {"model_dump": _normal(value.model_dump(mode="json"))}
        except Exception:
            pass
    return {
        "type": f"{type(value).__module__}.{type(value).__qualname__}",
        "text": str(value) if type(value).__module__ in {"sympy", "decimal", "fractions"} else None,
    }


def _resolve(module_name: str, callable_name: str) -> Any:
    module = importlib.import_module(module_name)
    target: Any = module
    for part in callable_name.split("."):
        if not part or part.startswith("_"):
            raise AttributeError(callable_name)
        target = getattr(target, part)
    if not callable(target):
        raise TypeError(f"not_callable:{callable_name}")
    if inspect.iscoroutinefunction(target):
        raise TypeError("async_operation_not_supported")
    return target


def _call(tool: _Tool, operation: _Operation, case: _Case) -> dict[str, Any]:
    base = {
        "tool_id": tool.tool_id,
        "module": operation.module,
        "callable": operation.callable_name,
        "case": case.name,
        "expected_status": case.expected,
        "input_sha256": sha256_bytes(canonical_json_bytes({"args": list(case.args), "kwargs": case.kwargs})),
    }
    try:
        try:
            installed_version = importlib.metadata.version(tool.distribution)
        except importlib.metadata.PackageNotFoundError:
            return {**base, "status": _STATUS_IMPORT_REFUSED, "reason": "DISTRIBUTION_NOT_INSTALLED", "executed": False}
        if installed_version != tool.version:
            return {
                **base,
                "status": _STATUS_IMPORT_REFUSED,
                "reason": "LOCKED_VERSION_MISMATCH",
                "installed_version": installed_version,
                "expected_version": tool.version,
                "executed": False,
            }
        target = _resolve(operation.module, operation.callable_name)
        result = target(*copy.deepcopy(list(case.args)), **copy.deepcopy(case.kwargs))
        normalized = _normal(result)
        output = canonical_json_bytes(normalized)
        return {
            **base,
            "status": _STATUS_SUCCEEDED,
            "output_sha256": sha256_bytes(output),
            "output": normalized,
            "executed": True,
        }
    except BaseException as exc:  # an operation's refusal is evidence, not a field crash
        return {
            **base,
            "status": _STATUS_REFUSED,
            "reason": type(exc).__name__,
            "executed": True,
        }


def _event(body: dict[str, Any]) -> dict[str, Any]:
    return {**body, "event_id": sha256_bytes(canonical_json_bytes(body))}


def _entropy(statuses: Sequence[str]) -> float:
    if not statuses:
        return 0.0
    counts = Counter(statuses)
    total = sum(counts.values())
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _expected_ok(row: dict[str, Any]) -> bool:
    return row.get("status") == row.get("expected_status") and bool(row.get("executed"))


def _fingerprint(rows: Sequence[dict[str, Any]]) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            [
                {
                    "tool_id": row.get("tool_id"),
                    "case": row.get("case"),
                    "status": row.get("status"),
                    "output_sha256": row.get("output_sha256"),
                    "reason": row.get("reason"),
                }
                for row in rows
            ]
        )
    )


def _run_tool(tool: _Tool, operation: _Operation, *, configuration: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    positive = _call(tool, operation, operation.positive)
    positive["configuration"] = configuration
    positive["scenario"] = "positive"
    rows.append(_event(positive))
    replay = _call(tool, operation, operation.positive)
    replay["configuration"] = configuration
    replay["scenario"] = "replay"
    rows.append(_event(replay))
    for case in operation.mutations:
        observed = _call(tool, operation, case)
        observed["configuration"] = configuration
        observed["scenario"] = "mutation"
        rows.append(_event(observed))
    for case in operation.boundaries:
        observed = _call(tool, operation, case)
        observed["configuration"] = configuration
        observed["scenario"] = "boundary"
        rows.append(_event(observed))
    positive_rows = [row for row in rows if row["scenario"] == "positive"]
    replay_rows = [row for row in rows if row["scenario"] == "replay"]
    boundary_rows = [row for row in rows if row["scenario"] in {"mutation", "boundary"}]
    expected_ok = all(_expected_ok(row) for row in rows)
    replay_stable = bool(
        positive_rows
        and replay_rows
        and positive_rows[0].get("status") == replay_rows[0].get("status")
        and positive_rows[0].get("output_sha256") == replay_rows[0].get("output_sha256")
    )
    summary = {
        "tool_id": tool.tool_id,
        "configuration": configuration,
        "positive_succeeded": bool(positive_rows and positive_rows[0]["status"] == _STATUS_SUCCEEDED),
        "replay_stable": replay_stable,
        "boundary_cases": len(boundary_rows),
        "boundary_expected_ok": all(_expected_ok(row) for row in boundary_rows),
        "settled": bool(expected_ok and replay_stable),
        "boundary_yield": round(
            len({row.get("status") for row in boundary_rows if row.get("status") != _STATUS_SUCCEEDED})
            / len(boundary_rows),
            12,
        )
        if boundary_rows
        else 0.0,
        "status_entropy_bits": round(_entropy([str(row["status"]) for row in rows]), 12),
        "event_count": len(rows),
        "executed_event_count": sum(bool(row.get("executed")) for row in rows),
        "fingerprint": _fingerprint(rows),
    }
    return rows, summary


def _shared_order(
    left: _Tool,
    left_op: _Operation,
    right: _Tool,
    right_op: _Operation,
    *,
    configuration: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if left_op.shared_input is None or right_op.shared_input is None:
        return [], {
            "left_tool_id": left.tool_id,
            "right_tool_id": right.tool_id,
            "configuration": configuration,
            "status": "SKIPPED_NO_SHARED_INPUT",
            "order_stable": None,
            "ab_ba_synergy_score": 0.0,
        }
    # Each direction receives a fresh JSON input.  This intentionally tests
    # order sensitivity without allowing one operation to mutate authority
    # state owned by another operation.
    ab_left = _call(left, left_op, left_op.shared_input)
    ab_right = _call(right, right_op, right_op.shared_input)
    ba_right = _call(right, right_op, right_op.shared_input)
    ba_left = _call(left, left_op, left_op.shared_input)
    for row, order in ((ab_left, "AB"), (ab_right, "AB"), (ba_right, "BA"), (ba_left, "BA")):
        row["configuration"] = configuration
        row["scenario"] = "pair_order"
        row["order"] = order
        row["pair_left_tool_id"] = left.tool_id
        row["pair_right_tool_id"] = right.tool_id
    ab = [(ab_left.get("status"), ab_left.get("output_sha256"), ab_left.get("reason")), (ab_right.get("status"), ab_right.get("output_sha256"), ab_right.get("reason"))]
    ba = [(ba_right.get("status"), ba_right.get("output_sha256"), ba_right.get("reason")), (ba_left.get("status"), ba_left.get("output_sha256"), ba_left.get("reason"))]
    stable = ab == list(reversed(ba))
    summary = {
        "left_tool_id": left.tool_id,
        "right_tool_id": right.tool_id,
        "configuration": configuration,
        "status": "OBSERVED",
        "order_stable": stable,
        "ab_ba_synergy_score": 1.0 if not stable else 0.0,
        "ab_fingerprint": sha256_bytes(canonical_json_bytes(ab)),
        "ba_fingerprint": sha256_bytes(canonical_json_bytes(ba)),
    }
    return [_event(row) for row in (ab_left, ab_right, ba_right, ba_left)], summary


def _cohorts(rows: Sequence[_Tool], request: OperationProbeFieldRequest) -> list[list[_Tool]]:
    ordered = sorted(
        rows,
        key=lambda row: sha256_bytes(canonical_json_bytes([request.seed, row.tool_id])),
    )
    return [ordered[index : index + request.cohort_size] for index in range(0, min(len(ordered), request.cohort_limit), request.cohort_size)]


def run_operation_probe_field(
    request_bytes: bytes,
    manifest_bytes: bytes,
    prior_bytes: bytes = b"{}",
) -> dict[str, bytes]:
    """Run one operation probe field and return deterministic output files."""

    request = _request(_object(request_bytes, "inputs/request.json"))
    manifest = _object(manifest_bytes, "inputs/tool_manifest.json")
    prior = _object(prior_bytes, "inputs/prior_operation_probe.json")
    tools = _tools(manifest, prior)
    parsed: dict[str, tuple[_Operation | None, str | None]] = {
        row.tool_id: _operation(row) for row in tools
    }
    events: list[dict[str, Any]] = []
    facts: dict[str, dict[str, Any]] = {}
    for row in tools:
        operation, reason = parsed[row.tool_id]
        base = {
            "tool_id": row.tool_id,
            "distribution": row.distribution,
            "import_name": row.import_name,
            "operation_source": row.operation_source,
            "operation_spec_sha256": operation.digest if operation is not None else None,
            "mapping_status": "UNMAPPED_GENERIC_ONLY",
            "mapping_reason": reason,
            "probe_event_count": 0,
            "settled": False,
            "settlement_score": 0.0,
            "boundary_yield": 0.0,
            "information_gain_bits": 0.0,
            "ablation_score": 0.0,
            "ablation_settlement_delta": 0.0,
            "ab_ba_synergy_score": 0.0,
            "operation_rank": None,
        }
        if operation is None:
            facts[row.tool_id] = base
            events.append(
                _event(
                    {
                        "kind": "generic_only",
                        "tool_id": row.tool_id,
                        "mapping_status": "UNMAPPED_GENERIC_ONLY",
                        "reason": reason,
                    }
                )
            )
            continue
        # The operation is only mapped after this positive call imports the
        # declared distribution and executes the declared API.
        observed, summary = _run_tool(row, operation, configuration="single")
        events.extend(observed)
        if summary["positive_succeeded"]:
            base.update(
                {
                    "mapping_status": "OPERATION_MAPPED",
                    "mapping_reason": "REAL_IMPORTED_API_OPERATION_PROBE",
                    "probe_event_count": len(observed),
                    "settled": summary["settled"],
                    "settlement_score": 1.0 if summary["settled"] else 0.0,
                    "boundary_yield": summary["boundary_yield"],
                    "information_gain_bits": summary["status_entropy_bits"],
                    "single_probe": summary,
                }
            )
        else:
            base.update(
                {
                    "mapping_reason": "NO_REAL_OPERATION_PROBE",
                    "probe_event_count": len(observed),
                    "single_probe": summary,
                }
            )
        facts[row.tool_id] = base

    cohorts: list[dict[str, Any]] = []
    mapped_rows = {row.tool_id: row for row in tools if parsed[row.tool_id][0] is not None}
    for cohort_index, cohort in enumerate(_cohorts(tools, request)):
        cohort_id = sha256_bytes(canonical_json_bytes([request.seed, cohort_index, [row.tool_id for row in cohort]]))[:16]
        mapped = [row for row in cohort if row.tool_id in mapped_rows]
        cohort_full: list[dict[str, Any]] = []
        cohort_summaries: dict[str, dict[str, Any]] = {}
        for row in mapped:
            operation = parsed[row.tool_id][0]
            assert operation is not None
            observed, summary = _run_tool(row, operation, configuration=f"cohort:{cohort_id}:full")
            events.extend(observed)
            cohort_full.extend(observed)
            cohort_summaries[row.tool_id] = summary
        full_settled = all(summary["settled"] for summary in cohort_summaries.values()) if cohort_summaries else False
        full_entropy = _entropy([str(row["status"]) for row in cohort_full])
        ablation_rows: list[dict[str, Any]] = []
        for removed in mapped[: request.max_ablation_tools]:
            retained = [row for row in mapped if row.tool_id != removed.tool_id]
            subset_events: list[dict[str, Any]] = []
            subset_summaries: list[dict[str, Any]] = []
            for row in retained:
                operation = parsed[row.tool_id][0]
                assert operation is not None
                observed, summary = _run_tool(row, operation, configuration=f"cohort:{cohort_id}:without:{removed.tool_id}")
                events.extend(observed)
                subset_events.extend(observed)
                subset_summaries.append(summary)
            subset_settled = all(summary["settled"] for summary in subset_summaries) if subset_summaries else False
            subset_entropy = _entropy([str(row["status"]) for row in subset_events])
            delta = float(full_settled) - float(subset_settled)
            entropy_delta = max(0.0, subset_entropy - full_entropy)
            score = round(max(0.0, delta) + entropy_delta, 12)
            ablation = {
                "kind": "cohort_ablation",
                "cohort_id": cohort_id,
                "removed_tool_id": removed.tool_id,
                "full_settled": full_settled,
                "without_settled": subset_settled,
                "ablation_settlement_delta": round(delta, 12),
                "information_gain_bits": round(entropy_delta, 12),
                "ablation_score": score,
                "full_event_count": len(cohort_full),
                "without_event_count": len(subset_events),
            }
            events.append(_event(ablation))
            ablation_rows.append(ablation)
            fact = facts[removed.tool_id]
            fact["ablation_score"] = max(float(fact["ablation_score"]), score)
            fact["ablation_settlement_delta"] = max(float(fact["ablation_settlement_delta"]), delta)
            fact["information_gain_bits"] = max(float(fact["information_gain_bits"]), entropy_delta)
        pair_rows: list[dict[str, Any]] = []
        for index, left in enumerate(mapped):
            for right in mapped[index + 1 :]:
                if len(pair_rows) >= request.max_pairs:
                    break
                left_op = parsed[left.tool_id][0]
                right_op = parsed[right.tool_id][0]
                assert left_op is not None and right_op is not None
                pair_events, pair = _shared_order(
                    left, left_op, right, right_op, configuration=f"cohort:{cohort_id}"
                )
                events.extend(pair_events)
                pair_rows.append(pair)
                if pair.get("status") == "OBSERVED":
                    synergy = float(pair["ab_ba_synergy_score"])
                    facts[left.tool_id]["ab_ba_synergy_score"] = max(
                        float(facts[left.tool_id]["ab_ba_synergy_score"]), synergy
                    )
                    facts[right.tool_id]["ab_ba_synergy_score"] = max(
                        float(facts[right.tool_id]["ab_ba_synergy_score"]), synergy
                    )
            if len(pair_rows) >= request.max_pairs:
                break
        cohorts.append(
            {
                "cohort_id": cohort_id,
                "cohort_index": cohort_index,
                "tool_ids": [row.tool_id for row in cohort],
                "mapped_tool_ids": [row.tool_id for row in mapped],
                "unmapped_tool_ids": [row.tool_id for row in cohort if row.tool_id not in mapped_rows],
                "full_settled": full_settled,
                "full_status_entropy_bits": round(full_entropy, 12),
                "ablation_count": len(ablation_rows),
                "pair_count": len(pair_rows),
                "claim_ceiling": CLAIM_CEILING,
            }
        )

    # Generic-only rows are intentionally absent from this ranking.  A row can
    # enter only after a real imported API operation produced a positive result.
    mapped_facts = [row for row in facts.values() if row["mapping_status"] == "OPERATION_MAPPED"]
    mapped_facts.sort(
        key=lambda row: (
            -float(row["ablation_score"]),
            -float(row["settlement_score"]),
            -float(row["boundary_yield"]),
            -float(row["information_gain_bits"]),
            -float(row["ab_ba_synergy_score"]),
            row["tool_id"],
        )
    )
    for rank, row in enumerate(mapped_facts, start=1):
        row["operation_rank"] = rank
    events.sort(key=lambda item: item["event_id"])
    field = {
        "schema": "constraintbox.operation_probe_field.v1",
        "request_sha256": sha256_bytes(request_bytes),
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "prior_sha256": sha256_bytes(prior_bytes),
        "seed": request.seed,
        "tool_count": len(tools),
        "cohort_count": len(cohorts),
        "operation_mapped_count": len(mapped_facts),
        "generic_only_unmapped_count": len(tools) - len(mapped_facts),
        "tools": [facts[row.tool_id] for row in tools],
        "cohorts": cohorts,
        "ranking": [row["tool_id"] for row in mapped_facts],
        "ranking_ceiling": (
            "ordered operation candidates only; generic-only tools remain explicitly unmapped; "
            "scores are packet-local observations, not core/admission decisions"
        ),
        "event_count": len(events),
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    ranking = {
        "schema": "constraintbox.operation_probe_rankings.v1",
        "field_sha256": sha256_bytes(canonical_json_bytes(field)),
        "ranked_operation_candidates": mapped_facts,
        "unmapped_generic_only": sorted(
            row["tool_id"] for row in facts.values() if row["mapping_status"] == "UNMAPPED_GENERIC_ONLY"
        ),
        "ranking_ceiling": field["ranking_ceiling"],
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    summary = {
        "schema": "constraintbox.operation_probe_field_summary.v1",
        "tool_count": len(tools),
        "operation_mapped_count": len(mapped_facts),
        "generic_only_unmapped_count": len(tools) - len(mapped_facts),
        "cohort_count": len(cohorts),
        "event_count": len(events),
        "metric_names": [
            "ablation_score",
            "settlement_score",
            "boundary_yield",
            "information_gain_bits",
            "ab_ba_synergy_score",
        ],
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    return {
        EVENT_OUTPUT: b"\n".join(canonical_json_bytes(item) for item in events) + (b"\n" if events else b""),
        FIELD_OUTPUT: canonical_json_bytes(field),
        RANKING_OUTPUT: canonical_json_bytes(ranking),
        SUMMARY_OUTPUT: canonical_json_bytes(summary),
    }


def run_operation_probe_field_from_zip(task: Any, workspace: dict[str, bytes]) -> dict[str, bytes]:
    """Adapter-shaped callable for later registration in ``operations.py``."""

    if len(task.input_paths) != 3 or len(task.output_paths) != len(OUTPUTS):
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    result = run_operation_probe_field(
        workspace[task.input_paths[0]],
        workspace[task.input_paths[1]],
        workspace[task.input_paths[2]],
    )
    expected = set(task.output_paths)
    if expected != set(OUTPUTS):
        raise ZipJobRefusal("REFUSE_OPERATION_PROBE_OUTPUT_SET", task.task_id)
    return result


# Naming aliases keep the byte-level callable and the ZIP operation adapter
# distinct while making later registration in ``operations.py`` explicit.
run_operation_probe_field_operation = run_operation_probe_field_from_zip
OUTPUT_PATHS = OUTPUTS


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    """CLI-like local entry point for direct replay outside a ZIP packet."""

    parser = argparse.ArgumentParser(prog="cb-operation-probe-field")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--prior", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    prior = args.prior.read_bytes() if args.prior is not None else b"{}"
    outputs = run_operation_probe_field(args.request.read_bytes(), args.manifest.read_bytes(), prior)
    for relative, data in outputs.items():
        _atomic_write(args.output_dir / relative.removeprefix("output/"), data)
    print(
        json.dumps(
            {
                "schema": "constraintbox.operation_probe_field_cli.v1",
                "output_dir": str(args.output_dir.resolve()),
                "outputs": sorted(outputs),
                "output_sha256": {path: sha256_bytes(data) for path, data in sorted(outputs.items())},
                "promotion_allowed": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
