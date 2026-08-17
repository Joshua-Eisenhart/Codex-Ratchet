from __future__ import annotations

import hashlib
import io
import json
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from constraintbox_zip_agent.prompt_handshake import build_prompt_handshake_packet
from constraintbox_zip_agent.failure_wave import build_demo_packet
from constraintbox_zip_agent.protocol import (
    ZipJobRefusal,
    canonical_json_bytes,
    sha256_bytes,
    validate_return_zip,
)
from constraintbox_zip_agent.runtime import execute_packet


OWNER = b"Keep the exact owner prompt; do not turn a paraphrase into authority."
COMPOSED = b"shared mini-MMM bytes\n\nexact owner task bytes"
MMM_BUNDLE = b"mini voice one\nmini voice two\n"
ROUTES = ["codex1-spark", "route-b", "route-c"]
FIELD_PACKET = build_demo_packet()
FIELD_RETURN = execute_packet(FIELD_PACKET).return_zip_bytes
TEST_REPORT = b'<testsuites><testsuite tests="7" failures="0" errors="0"/></testsuites>'


def _hashed(value: dict[str, object], field: str) -> dict[str, object]:
    result = dict(value)
    result[field] = sha256_bytes(canonical_json_bytes(result))
    return result


def _provider_hashed(value: dict[str, object]) -> dict[str, object]:
    result = dict(value)
    encoded = (
        json.dumps(
            result,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")
    result["provider_call_sha256"] = hashlib.sha256(encoded).hexdigest()
    return result


def _fixture() -> dict[str, object]:
    eligible_definition = {
        "schema": "constraintbox.zip-template.v1",
        "template_id": "eligible-template",
        "version": "1",
        "purpose": "another bounded handshake round",
    }
    cheap_swarm_definition = {
        "schema": "constraintbox.zip-template.v1",
        "template_id": "cheap-codex1-swarm",
        "version": "1",
        "purpose": "main swarm using the cheapest qualified Codex1 route",
        "swarm_model_routes": ["codex1-spark"],
        "packet_files": {
            "00_RUN_ME_FIRST.md": "materialized work zip only",
            "AGENTS/strategy.md": "role: strategy\n",
        },
    }
    ineligible_definition = {
        "schema": "constraintbox.zip-template.v1",
        "template_id": "ineligible-template",
        "version": "1",
        "purpose": "requires unavailable evidence",
    }
    preload = _hashed(
        {
            "schema": "constraintbox.mmm-preload.v2",
            "disposition": "CONTENT_BOUND",
            "run_id": "handshake-run",
            "agent_id": "shared-triplet",
            "parent_id": "owner",
            "wave_id": "prompt-handshake",
            "round": 1,
            "depth": 0,
            "selection": {
                "algorithm": "cb-mini-mmm-selection-v2",
                "python": "3.13.6",
                "resolved_primary_ids": ["voice:one:compact"],
                "seed": 7,
                "voice_count": 1,
                "voice_variant_request": "compact",
            },
            "sources": [
                {
                    "included_bytes": 10,
                    "line_count": 1,
                    "path": "/voices/one.md",
                    "primary_id": "voice:one:compact",
                    "sha256": "1" * 64,
                    "source_bytes": 10,
                }
            ],
            "task_path": "inputs/owner_prompt.bin",
            "task_sha256": sha256_bytes(OWNER),
            "pool_sha256": "2" * 64,
            "bundle_path": "inputs/mmm_bundle.md",
            "bundle_sha256": sha256_bytes(MMM_BUNDLE),
            "bundle_bytes": len(MMM_BUNDLE),
            "composed_prompt_path": "inputs/composed_prompt.md",
            "composed_prompt_sha256": sha256_bytes(COMPOSED),
            "composed_prompt_bytes": len(COMPOSED),
            "max_bytes": 240000,
            "captured_at": "2026-08-14T00:00:00Z",
            "provider_dispatch_proved": False,
            "behavioral_effect_claimed": False,
            "claim_ceiling": "content bytes only",
        },
        "receipt_self_checksum",
    )
    source_rows: list[dict[str, object]] = []
    calls: list[dict[str, object]] = []
    observations: list[dict[str, object]] = []
    for index, route in enumerate(ROUTES):
        response_sha = f"{index + 3}" * 64
        request_sha = f"{index + 6}" * 64
        model_name = "GPT-5.3-Codex-Spark" if route == "codex1-spark" else f"model-{index}"
        source = _hashed(
            {
                "schema": "constraintbox.synthetic-adapter-receipt.v1",
                "request_sha256": request_sha,
                "prompt_sha256": sha256_bytes(COMPOSED),
                "model_requested": model_name,
                "model_binding_confirmed": True,
                "disposition": "OBSERVED",
                "response_sha256": response_sha,
                "promotion_allowed": False,
            },
            "receipt_sha256",
        )
        source_rows.append(
            {
                "route_id": route,
                "response_digest_field": "response_sha256",
                "receipt": source,
            }
        )
        call = _provider_hashed(
            {
                "schema": "constraintbox.provider-call.v1",
                "run_id": "handshake-run",
                "agent_id": f"agent-{index}",
                "parent_id": "owner",
                "wave_id": "prompt-handshake",
                "round_index": 1,
                "depth": 0,
                "preload_receipt_sha256": preload["receipt_self_checksum"],
                "provider": f"provider-{index}",
                "route": route,
                "model_requested": model_name,
                "model_observed": model_name,
                "prompt_sha256": sha256_bytes(COMPOSED),
                "request_sha256": request_sha,
                "response_sha256": response_sha,
                "terminal_state": "OBSERVED",
                "started_at": None,
                "completed_at": None,
                "budget": {},
                "usage": {"duration_seconds": 2.0 + index},
                "source_receipt_schema": source["schema"],
                "source_receipt_sha256": source["receipt_sha256"],
                "claim_ceiling": "one normalized observation",
                "promotion_allowed": False,
            },
        )
        calls.append(call)
        observations.append(
            {
                "route_id": route,
                "response_sha256": response_sha,
                "paraphrases": [f"paraphrase from {route}"],
                "questions": [f"question from {route}"],
                "alternative_interpretations": [f"alternative from {route}"],
            }
        )
    return {
        "preload": preload,
        "settings": {
            "schema": "constraintbox.prompt-handshake-run.v1",
            "run_id": "handshake-run",
            "wave_id": "prompt-handshake",
            "round_index": 1,
            "depth": 0,
            "owner_prompt_sha256": sha256_bytes(OWNER),
            "required_route_ids": ROUTES,
            "required_tool_ids": ["tool-a"],
            "budget": {
                "max_provider_calls": 3,
                "max_total_wall_seconds": 30,
                "max_child_depth": 1,
            },
        },
        "tools": {
            "schema": "constraintbox.prompt-handshake-tool-qualification.v1",
            "source_fingerprint_sha256": "a" * 64,
            "field_packet_sha256": sha256_bytes(FIELD_PACKET),
            "field_return_sha256": sha256_bytes(FIELD_RETURN),
            "handshake_test_report_sha256": sha256_bytes(TEST_REPORT),
            "tools": [
                {
                    "tool_id": "tool-a",
                    "qualified": True,
                    "evidence_sha256": "b" * 64,
                    "operation_ids": ["operation-a"],
                }
            ],
        },
        "calls": {
            "schema": "constraintbox.prompt-handshake-provider-calls.v1",
            "calls": calls,
        },
        "sources": {
            "schema": "constraintbox.prompt-handshake-source-receipts.v1",
            "receipts": source_rows,
        },
        "catalog": {
            "schema": "constraintbox.prompt-handshake-template-catalog.v1",
            "templates": [
                {
                    "template_id": "cheap-codex1-swarm",
                    "version": "1",
                    "template_sha256": sha256_bytes(
                        canonical_json_bytes(cheap_swarm_definition)
                    ),
                    "template_definition": cheap_swarm_definition,
                    "required_route_ids": ["codex1-spark"],
                    "required_tool_ids": ["tool-a"],
                    "required_operation_ids": ["operation-a"],
                    "maximum_child_depth": 1,
                    "claim_ceiling": "materialization proposal only; no execution",
                },
                {
                    "template_id": "eligible-template",
                    "version": "1",
                    "template_sha256": sha256_bytes(
                        canonical_json_bytes(eligible_definition)
                    ),
                    "template_definition": eligible_definition,
                    "required_route_ids": ROUTES,
                    "required_tool_ids": ["tool-a"],
                    "required_operation_ids": ["operation-a"],
                    "maximum_child_depth": 1,
                    "claim_ceiling": "candidate only",
                },
                {
                    "template_id": "ineligible-template",
                    "version": "1",
                    "template_sha256": sha256_bytes(
                        canonical_json_bytes(ineligible_definition)
                    ),
                    "template_definition": ineligible_definition,
                    "required_route_ids": ROUTES,
                    "required_tool_ids": ["missing-tool"],
                    "required_operation_ids": [],
                    "maximum_child_depth": 1,
                    "claim_ceiling": "candidate only",
                },
            ],
        },
        "candidates": {
            "schema": "constraintbox.prompt-handshake-candidates.v1",
            "owner_prompt_sha256": sha256_bytes(OWNER),
            "composed_prompt_sha256": sha256_bytes(COMPOSED),
            "observations": observations,
        },
    }


def _packet(
    fixture: dict[str, object] | None = None,
    *,
    handshake_test_report: bytes = TEST_REPORT,
) -> bytes:
    value = fixture or _fixture()
    return build_prompt_handshake_packet(
        owner_prompt=OWNER,
        composed_prompt=COMPOSED,
        preload_receipt=canonical_json_bytes(value["preload"]),
        mmm_bundle=MMM_BUNDLE,
        run_settings=canonical_json_bytes(value["settings"]),
        tool_qualification=canonical_json_bytes(value["tools"]),
        provider_calls=canonical_json_bytes(value["calls"]),
        source_receipts=canonical_json_bytes(value["sources"]),
        template_catalog=canonical_json_bytes(value["catalog"]),
        candidate_observations=canonical_json_bytes(value["candidates"]),
        tool_field_packet=FIELD_PACKET,
        tool_field_return=FIELD_RETURN,
        handshake_test_report=handshake_test_report,
    )


def _json_member(return_zip: bytes, path: str) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(return_zip), "r") as archive:
        return json.loads(archive.read(path))


def test_handshake_runs_and_stops_for_external_human_confirmation() -> None:
    packet = _packet()
    result = execute_packet(packet)
    validate_return_zip(
        result.return_zip_bytes,
        expected_input_sha256=result.input_packet_sha256,
        input_packet_bytes=packet,
    )
    confirmation = _json_member(
        result.return_zip_bytes, "output/confirmation_required.json"
    )
    eligible = _json_member(result.return_zip_bytes, "output/eligible_templates.json")
    surface = _json_member(result.return_zip_bytes, "output/confirmation_surface.json")
    assert confirmation["state"] == "HUMAN_CONFIRMATION_REQUIRED"
    assert confirmation["human_confirmation_present"] is False
    assert confirmation["selected_template_ids"] == []
    assert confirmation["execution_authorized"] is False
    assert eligible["selection_made"] is False
    assert eligible["execution_authorized"] is False
    assert [row["template_id"] for row in eligible["templates"]] == [
        "cheap-codex1-swarm",
        "eligible-template",
    ]
    assert surface["actual_prompt"]["text"] == OWNER.decode()
    assert surface["models_to_be_used"][0]["route_id"] == "codex1-spark"
    assert surface["models_to_be_used"][0]["model_requested"] == "GPT-5.3-Codex-Spark"
    assert surface["python_tool_health"] == [
        {
            "tool_id": "tool-a",
            "qualified": True,
            "operation_ids": ["operation-a"],
            "evidence_sha256": "b" * 64,
        }
    ]
    assert len(surface["prompt_options"]) == 3
    assert surface["ready_template_options"][0]["template_id"] == "cheap-codex1-swarm"
    assert surface["ready_template_options"][0]["swarm_model_routes"] == ["codex1-spark"]
    assert surface["default_recommendation"] == "cheap-codex1-swarm"
    assert surface["models_to_be_used"][0]["spark_oauth_required"] is True
    assert surface["models_to_be_used"][0]["spark_oauth_smoked"] is False
    assert surface["automation"]["unsmoked_spark_presented"] is True
    assert surface["automation"]["all_presented_model_routes_prechecked"] is True
    assert surface["automation"]["execution_authorized"] is False
    assert surface["work_templates"]["cheap-codex1-swarm"]["files"]["AGENTS/strategy.md"] == "role: strategy\n"


def test_handshake_replays_byte_identically() -> None:
    packet = _packet()
    assert execute_packet(packet).return_zip_bytes == execute_packet(packet).return_zip_bytes


def test_owner_prompt_digest_drift_refuses() -> None:
    fixture = _fixture()
    fixture["settings"]["owner_prompt_sha256"] = "0" * 64
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(fixture))
    assert caught.value.reason_code == "REFUSE_HANDSHAKE_OWNER_PROMPT_DRIFT"


def test_failed_embedded_handshake_test_report_refuses() -> None:
    fixture = _fixture()
    failed_report = (
        b'<testsuites><testsuite tests="7" failures="1" errors="0"/></testsuites>'
    )
    fixture["tools"]["handshake_test_report_sha256"] = sha256_bytes(failed_report)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(fixture, handshake_test_report=failed_report))
    assert caught.value.reason_code == "REFUSE_HANDSHAKE_TOOL_EVIDENCE"


def test_missing_route_refuses_instead_of_accepting_two_of_three() -> None:
    fixture = _fixture()
    fixture["calls"]["calls"].pop()
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(fixture))
    assert caught.value.reason_code == "REFUSE_HANDSHAKE_ROUTE_SET"


def test_forged_source_receipt_refuses() -> None:
    fixture = _fixture()
    row = fixture["sources"]["receipts"][0]
    receipt = deepcopy(row["receipt"])
    receipt.pop("receipt_sha256")
    receipt["response_sha256"] = "f" * 64
    row["receipt"] = _hashed(receipt, "receipt_sha256")
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(fixture))
    assert caught.value.reason_code == "REFUSE_HANDSHAKE_SOURCE_BINDING"


def test_candidate_cannot_self_confirm_or_select_template() -> None:
    fixture = _fixture()
    fixture["candidates"]["confirmed"] = True
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(fixture))
    assert caught.value.reason_code == "REFUSE_HANDSHAKE_SCHEMA"


def test_runtime_contains_no_model_roster() -> None:
    source = Path(
        __file__
    ).parents[1] / "src" / "constraintbox_zip_agent" / "prompt_handshake.py"
    lowered = source.read_text(encoding="utf-8").lower()
    assert "grok-" not in lowered
    assert "gpt-" not in lowered
    assert "sonnet" not in lowered
    assert "opus" not in lowered


def test_handshake_surface_materializes_into_confirm_without_executing() -> None:
    from constraintbox_zip_agent.prompt_confirm import build_prompt_confirm_packet

    result = execute_packet(_packet())
    surface = _json_member(result.return_zip_bytes, "output/confirmation_surface.json")
    confirmed = execute_packet(
        build_prompt_confirm_packet(
            surface=surface,
            choice={
                "schema": "constraintbox.prompt-confirm-choice.v1",
                "selected_template_ids": ["cheap-codex1-swarm"],
            },
        )
    )
    with zipfile.ZipFile(io.BytesIO(confirmed.return_zip_bytes)) as archive:
        receipt = json.loads(archive.read("output/prompt_confirm.json"))
        work = archive.read("output/work/cheap-codex1-swarm.zip")
    assert receipt["execution_authorized"] is False
    assert receipt["executed_work_zip"] is False
    assert receipt["materialized_work_zip"] is True
    with zipfile.ZipFile(io.BytesIO(work)) as inner:
        assert inner.read("AGENTS/strategy.md") == b"role: strategy\n"
