from __future__ import annotations

from copy import deepcopy

import pytest

from constraintbox_zip_agent.execution_evidence import (
    INPUT_SCHEMA,
    compile_execution_evidence_v1,
)
from constraintbox_zip_agent.protocol import ZipJobRefusal, canonical_json_bytes, sha256_bytes


def _digest(body: dict[str, object]) -> dict[str, object]:
    result = dict(body)
    result["receipt_sha256"] = sha256_bytes(canonical_json_bytes(body))
    return result


def _base(*, current: bool = True) -> dict[str, object]:
    digest = "a" * 64
    current_body = {
        "status": "COMPLETED",
        "source_before_sha256": digest,
        "source_after_sha256": digest if current else "b" * 64,
        "current": current,
    }
    return {
        "schema": INPUT_SCHEMA,
        "run_id": "run-01",
        "raw_prompt_sha256": "1" * 64,
        "map_snapshot_sha256": "2" * 64,
        "map_return_sha256": "3" * 64,
        "required_map_tool_ids": ["jsonschema", "pydantic"],
        "minimums": {
            "profile_id": "nested-lean",
            "distinct_providers": 2,
            "model_calls": 2,
            "agents": 1,
            "subagents": 1,
            "subsubagents": 1,
            "python_tool_calls": 2,
            "required_skill_ids": ["mmm-preload"],
            "required_wave_ids": ["failure-wave"],
        },
        "provider_receipts": [
            _digest(
                {
                    "route_id": "route-a",
                    "provider": "provider-a",
                    "model_requested": "route-model-a",
                    "model_observed": "route-model-a",
                    "status": "COMPLETED",
                }
            ),
            _digest(
                {
                    "route_id": "route-b",
                    "provider": "provider-b",
                    "model_requested": "route-model-b",
                    "model_observed": "route-model-b",
                    "status": "COMPLETED",
                }
            ),
        ],
        "agent_receipts": [
            _digest({"agent_id": "root", "depth": 0, "status": "COMPLETED"}),
            _digest(
                {
                    "agent_id": "child",
                    "parent_agent_id": "root",
                    "depth": 1,
                    "status": "COMPLETED",
                    "model_route_id": "route-a",
                }
            ),
            _digest(
                {
                    "agent_id": "grandchild",
                    "parent_agent_id": "child",
                    "depth": 2,
                    "status": "COMPLETED",
                    "model_route_id": "route-b",
                }
            ),
        ],
        "python_tool_receipts": [
            _digest(
                {
                    "tool_id": "pydantic",
                    "operation": "validate_surface",
                    "status": "COMPLETED",
                }
            ),
            _digest(
                {
                    "tool_id": "jsonschema",
                    "operation": "validate_surface",
                    "status": "COMPLETED",
                }
            ),
        ],
        "retry_receipts": [
            _digest({"attempt": 2, "status": "COMPLETED", "operation": "render"})
        ],
        "skill_receipts": [
            _digest({"skill_id": "mmm-preload", "status": "COMPLETED"})
        ],
        "wave_receipts": [
            _digest({"wave_id": "failure-wave", "profile": "LEAN", "status": "COMPLETED"})
        ],
        "hook_receipts": [
            _digest({"hook_id": "submit", "phase": "pre", "status": "COMPLETED"})
        ],
        "source_currentness_receipts": [_digest(current_body)],
    }


def test_compiler_derives_human_shape_and_nested_counts() -> None:
    result = compile_execution_evidence_v1(_base())

    assert result["schema"] == "constraintbox.human-oracle-surface.v2"
    assert result["state"] == "COMPLETE"
    assert result["execution"] == {
        "model_calls": 2,
        "agents": 1,
        "subagents": 1,
        "subsubagents": 1,
        "deeper_agents": 0,
        "tool_operations": 2,
        "retries": 1,
        "failures": 0,
        "source_receipt_sha256": result["execution"]["source_receipt_sha256"],
    }
    assert result["minimums_satisfied"] is True
    assert [row["call_count"] for row in result["models"]] == [1, 1]
    assert [row["call_count"] for row in result["python_tools"]] == [1, 1]
    assert result["execution_authorized"] is False
    assert result["promotion_allowed"] is False


def test_caller_supplied_aggregate_counts_are_refused() -> None:
    raw = _base()
    raw["model_calls"] = 999
    with pytest.raises(ZipJobRefusal, match="REFUSE_EXECUTION_EVIDENCE_CALLER_COUNT"):
        compile_execution_evidence_v1(raw)

    raw = _base()
    raw["provider_receipts"][0]["call_count"] = 99
    with pytest.raises(ZipJobRefusal, match="REFUSE_EXECUTION_EVIDENCE_CALLER_COUNT"):
        compile_execution_evidence_v1(raw)


def test_mutated_receipt_body_is_refused() -> None:
    raw = _base()
    raw["provider_receipts"][0]["model_observed"] = "tampered"
    with pytest.raises(ZipJobRefusal, match="REFUSE_EXECUTION_EVIDENCE_RECEIPT_TAMPER"):
        compile_execution_evidence_v1(raw)


def test_tampered_receipt_digest_is_refused() -> None:
    raw = _base()
    raw["provider_receipts"][0]["receipt_sha256"] = "f" * 64
    with pytest.raises(ZipJobRefusal, match="REFUSE_EXECUTION_EVIDENCE_RECEIPT_TAMPER"):
        compile_execution_evidence_v1(raw)


def test_duplicate_receipt_digest_is_refused() -> None:
    raw = _base()
    raw["provider_receipts"].append(deepcopy(raw["provider_receipts"][0]))
    with pytest.raises(ZipJobRefusal, match="REFUSE_EXECUTION_EVIDENCE_DUPLICATE_RECEIPT"):
        compile_execution_evidence_v1(raw)


def test_missing_parent_is_refused() -> None:
    raw = _base()
    child = raw["agent_receipts"][1]
    child["parent_agent_id"] = "missing"
    child_body = dict(child)
    child_body.pop("receipt_sha256")
    child["receipt_sha256"] = sha256_bytes(canonical_json_bytes(child_body))
    with pytest.raises(ZipJobRefusal, match="REFUSE_EXECUTION_EVIDENCE_MISSING_PARENT"):
        compile_execution_evidence_v1(raw)


def test_source_drift_holds_without_claiming_complete() -> None:
    result = compile_execution_evidence_v1(_base(current=False))
    assert result["state"] == "HOLD"
    assert result["minimums_satisfied"] is True
    assert any(
        row["reason_code"] == "HOLD_SOURCE_CURRENTNESS_DRIFT"
        for row in result["failures_and_unknowns"]
    )


def test_cancelled_run_is_not_complete() -> None:
    raw = _base()
    raw["cancellation_receipts"] = [
        _digest({"status": "CANCELLED", "reason_code": "USER_CANCELLED"})
    ]
    result = compile_execution_evidence_v1(raw)
    assert result["state"] == "CANCELLED"
    assert result["execution_authorized"] is False


def test_failed_provider_does_not_satisfy_completed_model_minimum() -> None:
    raw = _base()
    failed = raw["provider_receipts"][1]
    failed["status"] = "FAILED"
    failed_body = dict(failed)
    failed_body.pop("receipt_sha256")
    failed["receipt_sha256"] = sha256_bytes(canonical_json_bytes(failed_body))
    result = compile_execution_evidence_v1(raw)
    assert result["state"] == "HOLD"
    assert result["minimums_satisfied"] is False
    assert result["execution"]["model_calls"] == 2
    assert any(row["reason_code"] == "PROVIDER_FAILED" for row in result["failures_and_unknowns"])


def test_failed_subsubagent_does_not_satisfy_nested_minimum() -> None:
    raw = _base()
    failed = raw["agent_receipts"][2]
    failed["status"] = "FAILED"
    failed_body = dict(failed)
    failed_body.pop("receipt_sha256")
    failed["receipt_sha256"] = sha256_bytes(canonical_json_bytes(failed_body))
    result = compile_execution_evidence_v1(raw)
    assert result["execution"]["subsubagents"] == 1
    assert result["minimums_satisfied"] is False
    assert result["state"] == "HOLD"


def test_agent_cannot_reference_an_unknown_model_route() -> None:
    raw = _base()
    child = raw["agent_receipts"][1]
    child["model_route_id"] = "route-missing"
    child_body = dict(child)
    child_body.pop("receipt_sha256")
    child["receipt_sha256"] = sha256_bytes(canonical_json_bytes(child_body))
    with pytest.raises(ZipJobRefusal, match="REFUSE_EXECUTION_EVIDENCE_AGENT_ROUTE"):
        compile_execution_evidence_v1(raw)
