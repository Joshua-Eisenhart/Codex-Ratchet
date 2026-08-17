from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
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


INPUT_PATHS = [
    "inputs/owner_prompt.bin",
    "inputs/composed_prompt.md",
    "inputs/preload_receipt.json",
    "inputs/mmm_bundle.md",
    "inputs/run_settings.json",
    "inputs/tool_qualification.json",
    "inputs/provider_calls.json",
    "inputs/source_receipts.json",
    "inputs/template_catalog.json",
    "inputs/candidate_observations.json",
    "inputs/tool_field_packet.zip",
    "inputs/tool_field_return.zip",
    "inputs/handshake_test_report.xml",
]

OUTPUT_PATHS = [
    "output/qualification_snapshot.json",
    "output/prompt_candidates.json",
    "output/eligible_templates.json",
    "output/confirmation_required.json",
    "output/confirmation_surface.json",
]

_HEX64 = re.compile(r"[0-9a-f]{64}")
_PROVIDER_FIELDS = {
    "schema",
    "run_id",
    "agent_id",
    "parent_id",
    "wave_id",
    "round_index",
    "depth",
    "preload_receipt_sha256",
    "provider",
    "route",
    "model_requested",
    "model_observed",
    "prompt_sha256",
    "request_sha256",
    "response_sha256",
    "terminal_state",
    "started_at",
    "completed_at",
    "budget",
    "usage",
    "source_receipt_schema",
    "source_receipt_sha256",
    "claim_ceiling",
    "promotion_allowed",
    "provider_call_sha256",
}


def _object(raw: bytes, label: str, fields: set[str]) -> dict[str, Any]:
    value = strict_json_loads(raw, label=label)
    if not isinstance(value, dict) or set(value) != fields:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", label)
    return value


def _hex(value: object, label: str) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_DIGEST", label)
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ZipJobRefusal("REFUSE_HANDSHAKE_TEXT", label)
    return value


def _string_list(value: object, label: str, *, minimum: int = 0) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum or len(value) > 32:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_LIST", label)
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_text(item, f"{label}[{index}]"))
    if len(result) != len(set(result)):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_DUPLICATE", label)
    return result


def _self_hash(value: dict[str, Any], field: str, label: str) -> str:
    observed = _hex(value.get(field), f"{label}.{field}")
    body = {key: item for key, item in value.items() if key != field}
    if observed != sha256_bytes(canonical_json_bytes(body)):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SELF_HASH", label)
    return observed


def _provider_call_self_hash(value: dict[str, Any]) -> None:
    """Verify the canonical profile declared by constraintbox.provider-call.v1."""

    observed = _hex(value.get("provider_call_sha256"), "provider_call.sha256")
    body = {
        key: item for key, item in value.items() if key != "provider_call_sha256"
    }
    encoded = (
        json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")
    if observed != hashlib.sha256(encoded).hexdigest():
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SELF_HASH", "provider_call")


def _validate_preload(
    raw: bytes,
    *,
    composed_prompt: bytes,
    mmm_bundle: bytes,
    run_id: str,
    wave_id: str,
    round_index: int,
    depth: int,
) -> dict[str, Any]:
    value = strict_json_loads(raw, label="inputs/preload_receipt.json")
    if not isinstance(value, dict):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "inputs/preload_receipt.json")
    _self_hash(value, "receipt_self_checksum", "preload_receipt")
    expected = {
        "schema": "constraintbox.mmm-preload.v2",
        "disposition": "CONTENT_BOUND",
        "run_id": run_id,
        "wave_id": wave_id,
        "round": round_index,
        "depth": depth,
        "composed_prompt_sha256": sha256_bytes(composed_prompt),
        "composed_prompt_bytes": len(composed_prompt),
        "bundle_sha256": sha256_bytes(mmm_bundle),
        "bundle_bytes": len(mmm_bundle),
        "provider_dispatch_proved": False,
        "behavioral_effect_claimed": False,
    }
    for field, wanted in expected.items():
        if value.get(field) != wanted:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_PRELOAD_BINDING", field)
    selection = value.get("selection")
    if not isinstance(selection, dict) or set(selection) != {
        "algorithm",
        "python",
        "resolved_primary_ids",
        "seed",
        "voice_count",
        "voice_variant_request",
    }:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_PRELOAD_BINDING", "selection")
    if selection["algorithm"] != "cb-mini-mmm-selection-v2":
        raise ZipJobRefusal("REFUSE_HANDSHAKE_PRELOAD_BINDING", "selection.algorithm")
    resolved_ids = _string_list(
        selection["resolved_primary_ids"], "selection.resolved_primary_ids", minimum=1
    )
    sources = value.get("sources")
    if not isinstance(sources, list) or len(sources) != len(resolved_ids):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_PRELOAD_BINDING", "sources")
    source_ids: list[str] = []
    for source in sources:
        if not isinstance(source, dict) or set(source) != {
            "included_bytes",
            "line_count",
            "path",
            "primary_id",
            "sha256",
            "source_bytes",
        }:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_PRELOAD_BINDING", "source")
        source_ids.append(_text(source["primary_id"], "source.primary_id"))
        _hex(source["sha256"], "source.sha256")
        if (
            isinstance(source["source_bytes"], bool)
            or not isinstance(source["source_bytes"], int)
            or source["source_bytes"] <= 0
            or source["included_bytes"] != source["source_bytes"]
        ):
            raise ZipJobRefusal("REFUSE_HANDSHAKE_PRELOAD_BINDING", "source bytes")
    if source_ids != resolved_ids:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_PRELOAD_BINDING", "source ordering")
    return value


def _validate_provider_envelope(
    value: object,
    *,
    run_id: str,
    wave_id: str,
    round_index: int,
    depth: int,
    prompt_sha256: str,
    preload_sha256: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _PROVIDER_FIELDS:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_PROVIDER_SCHEMA")
    if value.get("schema") != "constraintbox.provider-call.v1":
        raise ZipJobRefusal("REFUSE_HANDSHAKE_PROVIDER_SCHEMA")
    _provider_call_self_hash(value)
    bindings = {
        "run_id": run_id,
        "wave_id": wave_id,
        "round_index": round_index,
        "depth": depth,
        "prompt_sha256": prompt_sha256,
        "preload_receipt_sha256": preload_sha256,
        "terminal_state": "OBSERVED",
        "promotion_allowed": False,
    }
    for field, wanted in bindings.items():
        if value.get(field) != wanted:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_PROVIDER_BINDING", field)
    for field in (
        "agent_id",
        "provider",
        "route",
        "model_requested",
        "model_observed",
        "source_receipt_schema",
    ):
        _text(value.get(field), f"provider_call.{field}")
    for field in ("request_sha256", "response_sha256", "source_receipt_sha256"):
        _hex(value.get(field), f"provider_call.{field}")
    if not isinstance(value.get("usage"), dict):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_PROVIDER_SCHEMA", "usage")
    duration = value["usage"].get("duration_seconds")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration < 0:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_PROVIDER_SCHEMA", "duration_seconds")
    return value


def _validate_source_receipts(
    raw: bytes,
    envelopes: dict[str, dict[str, Any]],
) -> None:
    value = _object(
        raw,
        "inputs/source_receipts.json",
        {"schema", "receipts"},
    )
    if value["schema"] != "constraintbox.prompt-handshake-source-receipts.v1":
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "source_receipts")
    rows = value["receipts"]
    if not isinstance(rows, list):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "source_receipts.receipts")
    resolved: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "route_id",
            "response_digest_field",
            "receipt",
        }:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "source_receipt")
        route_id = _text(row["route_id"], "source_receipt.route_id")
        digest_field = _text(
            row["response_digest_field"], "source_receipt.response_digest_field"
        )
        receipt = row["receipt"]
        if not isinstance(receipt, dict) or route_id in resolved:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "source_receipt.receipt")
        _self_hash(receipt, "receipt_sha256", f"source_receipt.{route_id}")
        envelope = envelopes.get(route_id)
        if envelope is None:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_ROUTE_SET", route_id)
        checks = {
            "schema": envelope["source_receipt_schema"],
            "receipt_sha256": envelope["source_receipt_sha256"],
            "request_sha256": envelope["request_sha256"],
            "prompt_sha256": envelope["prompt_sha256"],
            "model_requested": envelope["model_requested"],
            "disposition": "OBSERVED",
            "model_binding_confirmed": True,
            digest_field: envelope["response_sha256"],
        }
        for field, wanted in checks.items():
            if receipt.get(field) != wanted:
                raise ZipJobRefusal("REFUSE_HANDSHAKE_SOURCE_BINDING", f"{route_id}.{field}")
        resolved[route_id] = receipt
    if set(resolved) != set(envelopes):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_ROUTE_SET", "source_receipts")


def run_prompt_handshake(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    if task.input_paths != INPUT_PATHS or task.output_paths != OUTPUT_PATHS:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)

    owner_prompt = workspace[INPUT_PATHS[0]]
    composed_prompt = workspace[INPUT_PATHS[1]]
    preload_raw = workspace[INPUT_PATHS[2]]
    mmm_bundle = workspace[INPUT_PATHS[3]]
    if not owner_prompt or not composed_prompt or not mmm_bundle:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_EMPTY_INPUT")

    settings = _object(
        workspace[INPUT_PATHS[4]],
        INPUT_PATHS[4],
        {
            "schema",
            "run_id",
            "wave_id",
            "round_index",
            "depth",
            "owner_prompt_sha256",
            "required_route_ids",
            "required_tool_ids",
            "budget",
        },
    )
    if settings["schema"] != "constraintbox.prompt-handshake-run.v1":
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "run_settings")
    run_id = _text(settings["run_id"], "run_id")
    wave_id = _text(settings["wave_id"], "wave_id")
    round_index = settings["round_index"]
    depth = settings["depth"]
    if (
        isinstance(round_index, bool)
        or not isinstance(round_index, int)
        or round_index < 0
        or isinstance(depth, bool)
        or not isinstance(depth, int)
        or depth < 0
    ):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "round/depth")
    if settings["owner_prompt_sha256"] != sha256_bytes(owner_prompt):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_OWNER_PROMPT_DRIFT")
    required_routes = _string_list(settings["required_route_ids"], "required_route_ids", minimum=1)
    required_tools = _string_list(settings["required_tool_ids"], "required_tool_ids")
    budget = settings["budget"]
    if not isinstance(budget, dict) or set(budget) != {
        "max_provider_calls",
        "max_total_wall_seconds",
        "max_child_depth",
    }:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "budget")
    for field in budget:
        value = budget[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", f"budget.{field}")

    preload = _validate_preload(
        preload_raw,
        composed_prompt=composed_prompt,
        mmm_bundle=mmm_bundle,
        run_id=run_id,
        wave_id=wave_id,
        round_index=round_index,
        depth=depth,
    )
    preload_sha = preload["receipt_self_checksum"]
    composed_sha = sha256_bytes(composed_prompt)

    call_set = _object(
        workspace[INPUT_PATHS[6]],
        INPUT_PATHS[6],
        {"schema", "calls"},
    )
    if call_set["schema"] != "constraintbox.prompt-handshake-provider-calls.v1":
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "provider_calls")
    if not isinstance(call_set["calls"], list):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_PROVIDER_SCHEMA")
    envelopes: dict[str, dict[str, Any]] = {}
    total_duration = 0.0
    for row in call_set["calls"]:
        envelope = _validate_provider_envelope(
            row,
            run_id=run_id,
            wave_id=wave_id,
            round_index=round_index,
            depth=depth,
            prompt_sha256=composed_sha,
            preload_sha256=preload_sha,
        )
        route = envelope["route"]
        if route in envelopes:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_DUPLICATE", "provider route")
        envelopes[route] = envelope
        total_duration += float(envelope["usage"]["duration_seconds"])
    if set(envelopes) != set(required_routes):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_ROUTE_SET", "provider_calls")
    if len(envelopes) > budget["max_provider_calls"]:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_BUDGET", "provider calls")
    if total_duration > budget["max_total_wall_seconds"]:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_BUDGET", "wall seconds")
    _validate_source_receipts(workspace[INPUT_PATHS[7]], envelopes)

    tools = _object(
        workspace[INPUT_PATHS[5]],
        INPUT_PATHS[5],
        {
            "schema",
            "source_fingerprint_sha256",
            "field_packet_sha256",
            "field_return_sha256",
            "handshake_test_report_sha256",
            "tools",
        },
    )
    if tools["schema"] != "constraintbox.prompt-handshake-tool-qualification.v1":
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "tool_qualification")
    _hex(tools["source_fingerprint_sha256"], "source_fingerprint_sha256")
    field_packet = workspace[INPUT_PATHS[10]]
    field_return = workspace[INPUT_PATHS[11]]
    test_report = workspace[INPUT_PATHS[12]]
    evidence_bindings = {
        "field_packet_sha256": sha256_bytes(field_packet),
        "field_return_sha256": sha256_bytes(field_return),
        "handshake_test_report_sha256": sha256_bytes(test_report),
    }
    for field, wanted in evidence_bindings.items():
        if tools[field] != wanted:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_TOOL_EVIDENCE", field)
    from .protocol import validate_return_zip

    validate_return_zip(
        field_return,
        expected_input_sha256=sha256_bytes(field_packet),
        input_packet_bytes=field_packet,
    )
    try:
        xml_root = ET.fromstring(test_report)
    except ET.ParseError as exc:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_TOOL_EVIDENCE", "test report XML") from exc
    suites = [xml_root] if xml_root.tag.endswith("testsuite") else list(xml_root)
    if not suites:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_TOOL_EVIDENCE", "test suites")
    test_count = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
    failure_count = sum(int(suite.attrib.get("failures", "0")) for suite in suites)
    error_count = sum(int(suite.attrib.get("errors", "0")) for suite in suites)
    if test_count < 1 or failure_count != 0 or error_count != 0:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_TOOL_EVIDENCE", "test result")
    if not isinstance(tools["tools"], list):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "tools")
    tool_rows: dict[str, dict[str, Any]] = {}
    operations: set[str] = set()
    for row in tools["tools"]:
        if not isinstance(row, dict) or set(row) != {
            "tool_id",
            "qualified",
            "evidence_sha256",
            "operation_ids",
        }:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "tool row")
        tool_id = _text(row["tool_id"], "tool_id")
        if tool_id in tool_rows or not isinstance(row["qualified"], bool):
            raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "tool row")
        _hex(row["evidence_sha256"], f"{tool_id}.evidence_sha256")
        row_operations = _string_list(row["operation_ids"], f"{tool_id}.operation_ids")
        if row["qualified"]:
            operations.update(row_operations)
        tool_rows[tool_id] = row
    if any(tool_id not in tool_rows or not tool_rows[tool_id]["qualified"] for tool_id in required_tools):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_REQUIRED_TOOL")

    candidates = _object(
        workspace[INPUT_PATHS[9]],
        INPUT_PATHS[9],
        {
            "schema",
            "owner_prompt_sha256",
            "composed_prompt_sha256",
            "observations",
        },
    )
    if candidates["schema"] != "constraintbox.prompt-handshake-candidates.v1":
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "candidate_observations")
    if candidates["owner_prompt_sha256"] != sha256_bytes(owner_prompt):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_OWNER_PROMPT_DRIFT")
    if candidates["composed_prompt_sha256"] != composed_sha:
        raise ZipJobRefusal("REFUSE_HANDSHAKE_PROVIDER_BINDING", "candidate prompt")
    if not isinstance(candidates["observations"], list):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "observations")
    observation_rows: dict[str, dict[str, Any]] = {}
    for row in candidates["observations"]:
        if not isinstance(row, dict) or set(row) != {
            "route_id",
            "response_sha256",
            "paraphrases",
            "questions",
            "alternative_interpretations",
        }:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "observation")
        route_id = _text(row["route_id"], "observation.route_id")
        if route_id in observation_rows or route_id not in envelopes:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_ROUTE_SET", route_id)
        if row["response_sha256"] != envelopes[route_id]["response_sha256"]:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_SOURCE_BINDING", f"{route_id}.response")
        _string_list(row["paraphrases"], f"{route_id}.paraphrases", minimum=1)
        _string_list(row["questions"], f"{route_id}.questions")
        _string_list(
            row["alternative_interpretations"],
            f"{route_id}.alternative_interpretations",
            minimum=1,
        )
        observation_rows[route_id] = row
    if set(observation_rows) != set(required_routes):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_ROUTE_SET", "candidate observations")

    catalog = _object(
        workspace[INPUT_PATHS[8]],
        INPUT_PATHS[8],
        {"schema", "templates"},
    )
    if catalog["schema"] != "constraintbox.prompt-handshake-template-catalog.v1":
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "template_catalog")
    if not isinstance(catalog["templates"], list):
        raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "templates")
    eligible: list[dict[str, Any]] = []
    eligible_surfaces: list[dict[str, Any]] = []
    seen_templates: set[str] = set()
    work_templates: dict[str, Any] = {}
    for row in catalog["templates"]:
        if not isinstance(row, dict) or set(row) != {
            "template_id",
            "version",
            "template_sha256",
            "template_definition",
            "required_route_ids",
            "required_tool_ids",
            "required_operation_ids",
            "maximum_child_depth",
            "claim_ceiling",
        }:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", "template row")
        template_id = _text(row["template_id"], "template_id")
        if template_id in seen_templates:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_DUPLICATE", "template_id")
        seen_templates.add(template_id)
        _text(row["version"], f"{template_id}.version")
        _hex(row["template_sha256"], f"{template_id}.template_sha256")
        definition = row["template_definition"]
        if (
            not isinstance(definition, dict)
            or definition.get("template_id") != template_id
            or definition.get("version") != row["version"]
            or sha256_bytes(canonical_json_bytes(definition)) != row["template_sha256"]
        ):
            raise ZipJobRefusal("REFUSE_HANDSHAKE_TEMPLATE_BINDING", template_id)
        template_routes = set(_string_list(row["required_route_ids"], f"{template_id}.routes"))
        template_tools = set(_string_list(row["required_tool_ids"], f"{template_id}.tools"))
        template_operations = set(
            _string_list(row["required_operation_ids"], f"{template_id}.operations")
        )
        maximum_depth = row["maximum_child_depth"]
        if isinstance(maximum_depth, bool) or not isinstance(maximum_depth, int) or maximum_depth < 0:
            raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", f"{template_id}.depth")
        _text(row["claim_ceiling"], f"{template_id}.claim_ceiling")
        if (
            template_routes.issubset(envelopes)
            and template_tools.issubset(
                tool_id for tool_id, tool in tool_rows.items() if tool["qualified"]
            )
            and template_operations.issubset(operations)
            and maximum_depth <= budget["max_child_depth"]
        ):
            eligible.append(
                {
                    "template_id": template_id,
                    "version": row["version"],
                    "template_sha256": row["template_sha256"],
                    "claim_ceiling": row["claim_ceiling"],
                }
            )
            eligible_surfaces.append(
                {
                    "template_id": template_id,
                    "version": row["version"],
                    "template_sha256": row["template_sha256"],
                    "claim_ceiling": row["claim_ceiling"],
                    "required_route_ids": sorted(template_routes),
                    "required_tool_ids": sorted(template_tools),
                    "required_operation_ids": sorted(template_operations),
                    "maximum_child_depth": maximum_depth,
                    "purpose": definition.get("purpose"),
                    "swarm_model_routes": definition.get("swarm_model_routes", []),
                    "ready_to_materialize": True,
                }
            )
            packet_files = definition.get("packet_files")
            if isinstance(packet_files, dict) and packet_files:
                if any(
                    not isinstance(path, str)
                    or not path
                    or path.startswith("/")
                    or ".." in path
                    or not isinstance(body, str)
                    for path, body in packet_files.items()
                ):
                    raise ZipJobRefusal("REFUSE_HANDSHAKE_SCHEMA", f"{template_id}.packet_files")
                work_templates[template_id] = {"files": dict(packet_files)}

    qualification = {
        "schema": "constraintbox.prompt-handshake-qualification.v1",
        "run_id": run_id,
        "owner_prompt_sha256": sha256_bytes(owner_prompt),
        "composed_prompt_sha256": composed_sha,
        "preload_receipt_sha256": preload_sha,
        "source_fingerprint_sha256": tools["source_fingerprint_sha256"],
        **evidence_bindings,
        "handshake_test_count": test_count,
        "qualified_route_ids": sorted(envelopes),
        "qualified_tool_ids": sorted(
            tool_id for tool_id, row in tool_rows.items() if row["qualified"]
        ),
        "available_operation_ids": sorted(operations),
        "observed_provider_calls": len(envelopes),
        "observed_total_wall_seconds": total_duration,
        "disposition": "HANDSHAKE_INPUTS_QUALIFIED_LOCAL",
        "promotion_allowed": False,
    }
    prompt_candidates = {
        "schema": "constraintbox.prompt-handshake-prompt-candidates.v1",
        "run_id": run_id,
        "owner_prompt_sha256": sha256_bytes(owner_prompt),
        "observations": [observation_rows[route] for route in sorted(observation_rows)],
        "claim_ceiling": "model observations for human comparison only",
        "promotion_allowed": False,
    }
    eligible_output = {
        "schema": "constraintbox.prompt-handshake-eligible-templates.v1",
        "run_id": run_id,
        "templates": sorted(eligible, key=lambda row: row["template_id"]),
        "selection_made": False,
        "execution_authorized": False,
        "promotion_allowed": False,
    }
    qualification_bytes = canonical_json_bytes(qualification)
    candidates_bytes = canonical_json_bytes(prompt_candidates)
    eligible_bytes = canonical_json_bytes(eligible_output)
    confirmation = {
        "schema": "constraintbox.prompt-handshake-confirmation.v1",
        "run_id": run_id,
        "owner_prompt_sha256": sha256_bytes(owner_prompt),
        "qualification_sha256": sha256_bytes(qualification_bytes),
        "prompt_candidates_sha256": sha256_bytes(candidates_bytes),
        "eligible_templates_sha256": sha256_bytes(eligible_bytes),
        "state": "HUMAN_CONFIRMATION_REQUIRED",
        "human_confirmation_present": False,
        "selected_template_ids": [],
        "execution_authorized": False,
        "next_operation": "submit_new_confirmation_zip",
        "promotion_allowed": False,
    }
    confirmation_surface = {
        "schema": "constraintbox.prompt-handshake-confirmation-surface.v1",
        "run_id": run_id,
        "state": "HUMAN_CONFIRMATION_REQUIRED",
        "actual_prompt": {
            "path": "inputs/owner_prompt.bin",
            "sha256": sha256_bytes(owner_prompt),
            "text": owner_prompt.decode("utf-8", errors="replace"),
        },
        "composed_prompt": {
            "path": "inputs/composed_prompt.md",
            "sha256": composed_sha,
            "text": composed_prompt.decode("utf-8", errors="replace"),
        },
        "models_to_be_used": [
            {
                "route_id": route,
                "provider": envelopes[route]["provider"],
                "model_requested": envelopes[route]["model_requested"],
                "model_observed": envelopes[route]["model_observed"],
                "terminal_state": envelopes[route]["terminal_state"],
                "duration_seconds": envelopes[route]["usage"]["duration_seconds"],
                "prechecked": True,
                "spark_oauth_required": (
                    "spark" in str(envelopes[route]["model_requested"]).lower()
                    or "spark" in route.lower()
                ),
                "spark_oauth_smoked": False,
            }
            for route in sorted(envelopes)
        ],
        "python_tool_health": [
            {
                "tool_id": tool_id,
                "qualified": row["qualified"],
                "operation_ids": list(row["operation_ids"]),
                "evidence_sha256": row["evidence_sha256"],
            }
            for tool_id, row in sorted(tool_rows.items())
        ],
        "prompt_options": [
            {
                "route_id": route,
                "paraphrases": observation_rows[route]["paraphrases"],
                "questions": observation_rows[route]["questions"],
                "alternative_interpretations": observation_rows[route][
                    "alternative_interpretations"
                ],
                "prechecked": True,
                "response_sha256": observation_rows[route]["response_sha256"],
            }
            for route in sorted(observation_rows)
        ],
        "ready_template_options": sorted(
            eligible_surfaces, key=lambda row: row["template_id"]
        ),
        "work_templates": work_templates,
        "default_recommendation": (
            sorted(eligible_surfaces, key=lambda row: row["template_id"])[0][
                "template_id"
            ]
            if eligible_surfaces
            else None
        ),
        "automation": {
            "all_presented_model_routes_prechecked": True,
            "all_presented_templates_eligible": True,
            "unsmoked_spark_presented": any(
                row.get("spark_oauth_required") and not row.get("spark_oauth_smoked")
                for row in [
                    {
                        "spark_oauth_required": (
                            "spark" in str(envelopes[route]["model_requested"]).lower()
                            or "spark" in route.lower()
                        ),
                        "spark_oauth_smoked": False,
                    }
                    for route in envelopes
                ]
            ),
            "execution_authorized": False,
            "human_must_select_or_edit": True,
        },
        "claim_ceiling": "human selection surface only; no template execution or semantic acceptance",
        "promotion_allowed": False,
    }
    return {
        OUTPUT_PATHS[0]: qualification_bytes,
        OUTPUT_PATHS[1]: candidates_bytes,
        OUTPUT_PATHS[2]: eligible_bytes,
        OUTPUT_PATHS[3]: canonical_json_bytes(confirmation),
        OUTPUT_PATHS[4]: canonical_json_bytes(confirmation_surface),
    }


def build_prompt_handshake_packet(
    *,
    owner_prompt: bytes,
    composed_prompt: bytes,
    preload_receipt: bytes,
    mmm_bundle: bytes,
    run_settings: bytes,
    tool_qualification: bytes,
    provider_calls: bytes,
    source_receipts: bytes,
    template_catalog: bytes,
    candidate_observations: bytes,
    tool_field_packet: bytes,
    tool_field_return: bytes,
    handshake_test_report: bytes,
) -> bytes:
    task_path = "tasks/00_compile_prompt_handshake.task.json"
    payloads = [
        owner_prompt,
        composed_prompt,
        preload_receipt,
        mmm_bundle,
        run_settings,
        tool_qualification,
        provider_calls,
        source_receipts,
        template_catalog,
        candidate_observations,
        tool_field_packet,
        tool_field_return,
        handshake_test_report,
    ]
    files = {
        "00_RUN_ME_FIRST.md": (
            b"# ConstraintBox prompt handshake\n\n"
            b"This ZIP qualifies bound observations and stops for human confirmation. "
            b"It cannot select, materialize, or execute a later template.\n"
        ),
        **dict(zip(INPUT_PATHS, payloads, strict=True)),
        task_path: _task(
            task_id="compile-prompt-handshake",
            sequence=0,
            operation="compile_prompt_handshake_v1",
            inputs=INPUT_PATHS,
            outputs=OUTPUT_PATHS,
        ),
    }
    return build_packet(
        _manifest(
            job_id="prompt-handshake",
            task_paths=[task_path],
            outputs=OUTPUT_PATHS,
            operations=["compile_prompt_handshake_v1"],
        ),
        files,
    )
