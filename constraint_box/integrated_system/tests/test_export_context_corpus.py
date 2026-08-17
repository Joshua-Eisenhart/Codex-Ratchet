from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_context_corpus.py"
SPEC = importlib.util.spec_from_file_location("export_context_corpus", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)


def _row(sequence: int, previous: str, event_type: str, text: str) -> dict:
    event = {
        "schema": "constraintbox.project-event.v1",
        "event_id": f"e{sequence}",
        "event_type": event_type,
        "material": {"kind": "verbatim_text", "text": text},
    }
    body = {
        "schema": "constraintbox.project-ledger-line.v1",
        "sequence": sequence,
        "previous_sha256": previous,
        "event": event,
    }
    digest = hashlib.sha256(exporter.canonical_json_bytes(body)).hexdigest()
    return {**body, "line_sha256": digest}


def test_export_keeps_prompt_and_progress_but_not_source_snapshot(tmp_path: Path) -> None:
    first = _row(1, "0" * 64, "OWNER_PROMPT", "owner\n")
    second = _row(2, first["line_sha256"], "SOURCE_SNAPSHOT_IMPORTED", "large\n")
    third = _row(3, second["line_sha256"], "PROGRESS_UPDATE", "progress\n")
    ledger = tmp_path / "events.jsonl"
    ledger.write_bytes(
        b"".join(exporter.canonical_json_bytes(row) + b"\n" for row in (first, second, third))
    )
    output = tmp_path / "corpus.jsonl"
    summary_path = tmp_path / "summary.json"
    summary = exporter.write_export(
        ledger, output, summary_path, expected_head=third["line_sha256"]
    )
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert [row["event"]["event_type"] for row in rows] == [
        "OWNER_PROMPT",
        "PROGRESS_UPDATE",
    ]
    assert summary["source_event_count"] == 3
    assert summary["selected_event_count"] == 2
    assert summary["source_ledger_required_at_runtime"] is False
    assert not Path(summary["output"]).is_absolute()
    assert summary["promotion_allowed"] is False


def test_tampered_chain_and_wrong_head_refuse(tmp_path: Path) -> None:
    row = _row(1, "0" * 64, "OWNER_PROMPT", "owner\n")
    ledger = tmp_path / "events.jsonl"
    ledger.write_text(json.dumps({**row, "previous_sha256": "f" * 64}) + "\n")
    with pytest.raises(ValueError, match="digest mismatch|chain mismatch"):
        exporter.load_and_verify_ledger(ledger)
    ledger.write_bytes(exporter.canonical_json_bytes(row) + b"\n")
    with pytest.raises(ValueError, match="head mismatch"):
        exporter.write_export(
            ledger, tmp_path / "out.jsonl", tmp_path / "summary.json", "e" * 64
        )
