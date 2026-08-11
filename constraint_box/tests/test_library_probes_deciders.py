"""Contract tests for the decider-capable adopted-library probe table."""
from __future__ import annotations

import json
from pathlib import Path

from constraintbox.library_probe_runner import LIBRARIES, SCHEMA, load_tables, run_probe_table


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "config" / "library_probes_deciders.json"
RECEIPT = ROOT / "receipts" / "library_probes_deciders_v1.json"


def test_table_has_every_decider_library_and_specific_negative() -> None:
    rows = load_tables([CONFIG])
    assert {row["library"] for row in rows} == set(LIBRARIES)
    for row in rows:
        assert row["question_kind"]
        assert row["negative"]["expect"]
        assert "independent_of" in row


def test_runner_replays_and_writes_receipt() -> None:
    receipt = run_probe_table([CONFIG], RECEIPT)
    assert receipt["schema"] == "cb.library_probe_receipt.v1"
    assert receipt["promotion_allowed"] is False
    assert len(receipt["libraries"]) == len(LIBRARIES)
    assert RECEIPT.is_file()
    parsed = json.loads(RECEIPT.read_text())
    assert parsed["summary"]["total"] == len(LIBRARIES)
    for row in parsed["libraries"]:
        assert row["status"] in {"proven", "available_unproven", "unavailable", "unused"}
        assert "replay" in row


def test_lane18_table_is_optional_and_loadable() -> None:
    lane18 = ROOT / "config" / "library_probes_harness.json"
    rows = load_tables([CONFIG, lane18])
    assert rows
    assert all(row["library"] for row in rows)
