from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from pydantic import ValidationError

from constraintbox_zip_agent.preprompt import (
    PrepromptRunConfiguration,
    build_preprompt_packet,
)
from constraintbox_zip_agent.project_ledger import ProjectLedger, record_text_event
from constraintbox_zip_agent.runtime import execute_packet


def _run_configuration(*, new: bool, round_index: int = 0) -> dict[str, object]:
    return {
        "schema": "constraintbox.preprompt-run-configuration.v1",
        "run_id": "preprompt-run",
        "prompt_round_index": round_index,
        "minimum_prompt_rounds": 2,
        "project": {
            "mode": "NEW" if new else "EXISTING",
            "required_question_ids": ["goal", "boundary"] if new else [],
            "answered_question_ids": ["goal"] if new else [],
            "required_document_ids": ["source-context"] if new else [],
            "submitted_document_ids": [],
        },
        "model_routes": [
            {
                "route_id": "route-from-run-data",
                "provider": "provider-from-run-data",
                "model_requested": "model-from-run-data",
                "budget_label": "bounded-run-data",
                "status": "QUALIFIED",
                "qualification_receipt_sha256": "1" * 64,
            }
        ],
        "mini_mmm_ids": ["voice:one:compact", "voice:two:compact"],
    }


def _tools(*, status: str = "QUALIFIED") -> dict[str, object]:
    return {
        "schema": "constraintbox.preprompt-tool-qualification.v1",
        "status": status,
        "tested_operation_ids": ["operation-one", "operation-two"],
        "failed_operation_ids": [] if status == "QUALIFIED" else ["operation-two"],
        "receipt_sha256": "2" * 64,
    }


def _ledger(tmp_path: Path) -> Path:
    plan = tmp_path / "plan.md"
    plan.write_text("Phase 3 is next: CB-run preprompt.\n", encoding="utf-8")
    progress = tmp_path / "progress.md"
    progress.write_text("Ledger imported. Preprompt not done yet.\n", encoding="utf-8")
    root = tmp_path / "state"
    ledger = ProjectLedger(root)
    record_text_event(
        ledger, plan, event_id="plan-1", event_type="PLAN_REVISION", source_kind="test"
    )
    record_text_event(
        ledger,
        progress,
        event_id="prog-1",
        event_type="PROGRESS_UPDATE",
        source_kind="test",
    )
    return root


def _execute(tmp_path: Path, *, run: dict[str, object], tools: dict[str, object]) -> dict:
    packet = build_preprompt_packet(
        owner_prompt="what is the plan?",
        run_configuration=run,
        tool_qualification=tools,
        ledger_root=_ledger(tmp_path),
    )
    result = execute_packet(packet)
    with zipfile.ZipFile(BytesIO(result.return_zip_bytes)) as archive:
        return json.loads(archive.read("output/preprompt.json"))


def test_new_project_requires_declared_questions_and_documents(tmp_path: Path) -> None:
    compiled = _execute(tmp_path, run=_run_configuration(new=True), tools=_tools())
    assert compiled["stage"] == "PROJECT_DISCOVERY_REQUIRED"
    assert compiled["project_discovery"]["missing_question_ids"] == ["boundary"]
    assert compiled["project_discovery"]["missing_document_ids"] == ["source-context"]
    assert compiled["execution_authorized"] is False
    assert compiled["model_routes"][0]["model_requested"] == "model-from-run-data"
    assert compiled["boot_evidence_required"]["mmm_read_proved"] is False


def test_existing_project_requires_multiple_prompt_rounds(tmp_path: Path) -> None:
    compiled = _execute(tmp_path, run=_run_configuration(new=False), tools=_tools())
    assert compiled["stage"] == "PROMPT_REFINEMENT_REQUIRED"
    assert compiled["next_operation"] == "generate_and_compare_next_prompt_options"


def test_completed_minimum_rounds_reaches_boot_probe_not_execution(tmp_path: Path) -> None:
    compiled = _execute(
        tmp_path, run=_run_configuration(new=False, round_index=1), tools=_tools()
    )
    assert compiled["stage"] == "BOOT_PROBE_REQUIRED"
    assert compiled["execution_authorized"] is False
    assert compiled["boot_evidence_required"]["python_tool_token_returned"] is True


def test_unqualified_tools_hold_before_boot(tmp_path: Path) -> None:
    compiled = _execute(
        tmp_path,
        run=_run_configuration(new=False, round_index=1),
        tools=_tools(status="HOLD"),
    )
    assert compiled["stage"] == "PREFLIGHT_HOLD"
    assert compiled["execution_authorized"] is False


def test_model_roster_is_not_embedded_in_preprompt_source() -> None:
    source = Path(
        __import__("constraintbox_zip_agent.preprompt", fromlist=["x"]).__file__
    ).read_text(encoding="utf-8")
    for slug in ("claude-sonnet", "gpt-5", "grok-4"):
        assert slug not in source.lower()


def test_new_project_cannot_skip_declared_discovery_requirements() -> None:
    run = _run_configuration(new=True)
    run["project"] = {
        "mode": "NEW",
        "required_question_ids": [],
        "answered_question_ids": [],
        "required_document_ids": [],
        "submitted_document_ids": [],
    }
    with pytest.raises(ValidationError):
        PrepromptRunConfiguration.model_validate(run)
