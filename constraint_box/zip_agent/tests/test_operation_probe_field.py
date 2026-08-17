from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path

from constraintbox_zip_agent.operation_probe_field import (
    EVENT_OUTPUT,
    FIELD_OUTPUT,
    RANKING_OUTPUT,
    SUMMARY_OUTPUT,
    main,
    run_operation_probe_field,
    build_operation_probe_field_packet,
)
from constraintbox_zip_agent.protocol import validate_packet, validate_return_zip
from constraintbox_zip_agent.runtime import execute_packet


def _tool(
    tool_id: str,
    *,
    operation_probe: dict[str, object] | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "tool_id": tool_id,
        "locked_distribution": "jsonschema",
        "locked_version": importlib.metadata.version("jsonschema"),
        "import_names": ["jsonschema"],
    }
    if operation_probe is not None:
        row["operation_probe"] = operation_probe
    return row


def _request(*, cohort_size: int = 4, max_pairs: int = 8) -> bytes:
    return json.dumps(
        {
            "schema": "constraintbox.operation_probe_field_request.v1",
            "seed": 17,
            "cohort_size": cohort_size,
            "cohort_limit": 32,
            "max_pairs": max_pairs,
            "max_ablation_tools": 16,
        },
        sort_keys=True,
    ).encode()


def _validate_probe() -> dict[str, object]:
    return {
        "module": "jsonschema",
        "callable": "validate",
        "positive": {"args": [1, {"type": "integer"}]},
        "mutations": [
            {
                "name": "invalid-schema",
                "args": [1, {"type": "not-a-real-jsonschema-type"}],
                "expected": "REFUSED",
            }
        ],
        "boundaries": [
            {"name": "zero", "args": [0, {"type": "integer"}]},
        ],
        "shared_input": {"args": [1, {"type": "integer"}]},
    }


def _validator_for_probe() -> dict[str, object]:
    return {
        "module": "jsonschema",
        "callable": "validators.validator_for",
        "positive": {"args": [{"type": "integer"}]},
        "mutations": [],
        "boundaries": [],
        "shared_input": {"args": [{"type": "integer"}]},
    }


def _run(tools: list[dict[str, object]]) -> dict[str, bytes]:
    manifest = json.dumps({"tools": tools}, sort_keys=True).encode()
    return run_operation_probe_field(_request(), manifest, b"{}")


def _field(outputs: dict[str, bytes]) -> dict[str, object]:
    return json.loads(outputs[FIELD_OUTPUT])


def test_only_real_explicit_operation_is_mapped_and_generic_rows_stay_unmapped() -> None:
    outputs = _run([_tool("jsonschema.validate", operation_probe=_validate_probe()), _tool("jsonschema.generic")])
    field = _field(outputs)
    assert field["tool_count"] == 2
    assert field["operation_mapped_count"] == 1
    assert field["generic_only_unmapped_count"] == 1
    facts = {row["tool_id"]: row for row in field["tools"]}
    assert facts["jsonschema.validate"]["mapping_status"] == "OPERATION_MAPPED"
    assert facts["jsonschema.validate"]["mapping_reason"] == "REAL_IMPORTED_API_OPERATION_PROBE"
    assert facts["jsonschema.generic"]["mapping_status"] == "UNMAPPED_GENERIC_ONLY"
    assert facts["jsonschema.generic"]["mapping_reason"] == "NO_EXPLICIT_OPERATION_PROBE"
    assert "jsonschema.generic" in json.loads(outputs[RANKING_OUTPUT])["unmapped_generic_only"]
    assert "core" in field["ranking_ceiling"]


def test_mutation_boundary_replay_and_metrics_are_evidence_bound() -> None:
    outputs = _run([_tool("jsonschema.validate", operation_probe=_validate_probe())])
    field = _field(outputs)
    fact = field["tools"][0]
    single = fact["single_probe"]
    assert fact["mapping_status"] == "OPERATION_MAPPED"
    assert single["positive_succeeded"] is True
    assert single["replay_stable"] is True
    assert single["boundary_cases"] == 2
    assert single["boundary_expected_ok"] is True
    assert single["settled"] is True
    assert fact["settlement_score"] == 1.0
    assert fact["boundary_yield"] > 0.0
    events = [json.loads(line) for line in outputs[EVENT_OUTPUT].splitlines()]
    assert {row.get("scenario") for row in events} >= {"positive", "replay", "mutation", "boundary"}
    assert all("event_id" in row for row in events)


def test_ab_ba_order_and_ablation_are_recorded_without_core_declaration() -> None:
    outputs = _run(
        [
            _tool("jsonschema.validate", operation_probe=_validate_probe()),
            _tool("jsonschema.validator_for", operation_probe=_validator_for_probe()),
        ]
    )
    field = _field(outputs)
    assert field["operation_mapped_count"] == 2
    assert field["cohorts"]
    assert field["cohorts"][0]["ablation_count"] == 2
    events = [json.loads(line) for line in outputs[EVENT_OUTPUT].splitlines()]
    assert any(row.get("kind") == "cohort_ablation" for row in events)
    pair_events = [row for row in events if row.get("scenario") == "pair_order"]
    assert len(pair_events) == 4
    ranking = json.loads(outputs[RANKING_OUTPUT])
    assert len(ranking["ranked_operation_candidates"]) == 2
    assert ranking["ranked_operation_candidates"][0]["operation_rank"] == 1
    assert all(row["operation_rank"] is not None for row in ranking["ranked_operation_candidates"])
    assert field["promotion_allowed"] is False


def test_invalid_operation_does_not_fall_back_to_import_mapping() -> None:
    outputs = _run([_tool("jsonschema.invalid", operation_probe={"module": "jsonschema"})])
    fact = _field(outputs)["tools"][0]
    assert fact["mapping_status"] == "UNMAPPED_GENERIC_ONLY"
    assert fact["mapping_reason"] == "OPERATION_MODULE_OR_CALLABLE_MISSING"
    assert fact["probe_event_count"] == 0


def test_field_is_byte_replayable() -> None:
    tools = [_tool("jsonschema.validate", operation_probe=_validate_probe())]
    first = _run(tools)
    second = _run(tools)
    assert first == second


def test_event_ids_are_unique_across_repeated_pair_membership() -> None:
    tools = [
        _tool(f"jsonschema.{index}", operation_probe=_validate_probe())
        for index in range(4)
    ]
    outputs = _run(tools)
    rows = [json.loads(line) for line in outputs[EVENT_OUTPUT].splitlines()]
    assert len({row["event_id"] for row in rows}) == len(rows)


def test_cli_like_callable_writes_declared_outputs(tmp_path: Path) -> None:
    request = tmp_path / "request.json"
    manifest = tmp_path / "manifest.json"
    output_dir = tmp_path / "out"
    request.write_bytes(_request())
    manifest.write_text(json.dumps({"tools": [_tool("jsonschema.validate", operation_probe=_validate_probe())]}), encoding="utf-8")
    assert main(
        [
            "--request",
            str(request),
            "--manifest",
            str(manifest),
            "--output-dir",
            str(output_dir),
        ]
    ) == 0
    assert {path.name for path in output_dir.iterdir()} == {
        Path(EVENT_OUTPUT).name,
        Path(FIELD_OUTPUT).name,
        Path(RANKING_OUTPUT).name,
        Path(SUMMARY_OUTPUT).name,
    }


def test_registered_operation_packet_executes_and_replays() -> None:
    request = _request()
    manifest = {"tools": [_tool("jsonschema", operation_probe=_validate_probe())]}
    packet = build_operation_probe_field_packet(
        request=request,
        manifest=json.dumps(manifest).encode("utf-8"),
        operation_catalog=b"{}",
        job_id="operation-probe-test",
    )
    validated = validate_packet(packet, known_operations={"operation_probe_field_v1"})
    assert validated.manifest.job_id == "operation-probe-test"

    first = execute_packet(packet)
    second = execute_packet(packet)
    assert first.return_zip_bytes == second.return_zip_bytes
    returned = validate_return_zip(
        first.return_zip_bytes,
        expected_input_sha256=first.input_packet_sha256,
        input_packet_bytes=packet,
    )
    assert returned.job_id == "operation-probe-test"
