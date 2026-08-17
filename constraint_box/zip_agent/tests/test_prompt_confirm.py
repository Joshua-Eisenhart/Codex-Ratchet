from __future__ import annotations

import json
import zipfile
import io

import pytest

from constraintbox_zip_agent.prompt_confirm import build_prompt_confirm_packet
from constraintbox_zip_agent.protocol import ZipJobRefusal
from constraintbox_zip_agent.runtime import execute_packet


def _surface() -> dict:
    return {
        "ready_template_options": [
            {"template_id": "roster-triad"},
            {"template_id": "handshake-next-round"},
        ],
        "execution_authorized": False,
    }


def test_prompt_confirm_binds_choice_and_does_not_execute() -> None:
    packet = build_prompt_confirm_packet(
        surface=_surface(),
        choice={
            "schema": "constraintbox.prompt-confirm-choice.v1",
            "selected_template_ids": ["roster-triad"],
        },
    )
    result = execute_packet(packet)
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        receipt = json.loads(archive.read("output/prompt_confirm.json"))
    assert receipt["execution_authorized"] is False
    assert receipt["materialized_work_zip"] is False
    assert receipt["executed_work_zip"] is False
    assert receipt["selected_template_ids"] == ["roster-triad"]


def test_prompt_confirm_materializes_work_zip_without_executing() -> None:
    surface = _surface()
    surface["work_templates"] = {
        "roster-triad": {
            "files": {
                "00_RUN_ME_FIRST.md": "work zip only",
                "AGENTS/strategy.md": "role: strategy\n",
            }
        }
    }
    packet = build_prompt_confirm_packet(
        surface=surface,
        choice={
            "schema": "constraintbox.prompt-confirm-choice.v1",
            "selected_template_ids": ["roster-triad"],
        },
    )
    result = execute_packet(packet)
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        receipt = json.loads(archive.read("output/prompt_confirm.json"))
        work = archive.read("output/work/roster-triad.zip")
    assert receipt["execution_authorized"] is False
    assert receipt["executed_work_zip"] is False
    assert receipt["materialized_work_zip"] is True
    assert "output/work/roster-triad.zip" in receipt["work_zip_sha256"]
    with zipfile.ZipFile(io.BytesIO(work)) as inner:
        assert "AGENTS/strategy.md" in inner.namelist()
        assert inner.read("AGENTS/strategy.md") == b"role: strategy\n"


def test_prompt_confirm_unknown_template_is_refused() -> None:
    packet = build_prompt_confirm_packet(
        surface=_surface(),
        choice={
            "schema": "constraintbox.prompt-confirm-choice.v1",
            "selected_template_ids": ["not-eligible"],
        },
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROMPT_CONFIRM_SELECTION"


def test_prompt_confirm_execute_flag_is_refused() -> None:
    packet = build_prompt_confirm_packet(
        surface=_surface(),
        choice={
            "schema": "constraintbox.prompt-confirm-choice.v1",
            "selected_template_ids": ["roster-triad"],
            "execute": True,
        },
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROMPT_CONFIRM_EXECUTION"


def test_prompt_confirm_nested_automation_execute_is_refused() -> None:
    surface = _surface()
    surface["automation"] = {"execution_authorized": True}
    packet = build_prompt_confirm_packet(
        surface=surface,
        choice={
            "schema": "constraintbox.prompt-confirm-choice.v1",
            "selected_template_ids": ["roster-triad"],
        },
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROMPT_CONFIRM_EXECUTION"
