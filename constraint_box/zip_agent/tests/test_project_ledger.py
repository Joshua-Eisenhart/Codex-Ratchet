from __future__ import annotations

import gzip
import json
import sqlite3
from pathlib import Path

import pytest

from constraintbox_zip_agent.project_ledger import (
    ProjectLedger,
    import_artifact,
    import_codex_rollout,
    import_hermes_session,
    record_text_event,
    write_current_view,
)
from constraintbox_zip_agent.protocol import ZipJobRefusal


def test_text_events_are_hash_chained_and_idempotent(tmp_path: Path) -> None:
    source = tmp_path / "plan.md"
    source.write_text("finite plan\n", encoding="utf-8")
    ledger = ProjectLedger(tmp_path / "state")

    first = record_text_event(
        ledger,
        source,
        event_id="plan-1",
        event_type="PLAN_REVISION",
        source_kind="owner_plan",
    )
    second = record_text_event(
        ledger,
        source,
        event_id="plan-1",
        event_type="PLAN_REVISION",
        source_kind="owner_plan",
    )

    assert first["added_event_count"] == 1
    assert second["added_event_count"] == 0
    assert ledger.verify()["event_count"] == 1
    row = json.loads(ledger.path.read_text(encoding="utf-8"))
    assert row["previous_sha256"] == "0" * 64
    assert row["event"]["material"]["text"] == "finite plan\n"


def test_expected_head_refuses_a_stale_resumer_before_append(tmp_path: Path) -> None:
    first_source = tmp_path / "first.md"
    second_source = tmp_path / "second.md"
    stale_source = tmp_path / "stale.md"
    first_source.write_text("first\n", encoding="utf-8")
    second_source.write_text("second\n", encoding="utf-8")
    stale_source.write_text("stale\n", encoding="utf-8")
    ledger = ProjectLedger(tmp_path / "state")
    first = record_text_event(
        ledger,
        first_source,
        event_id="first",
        event_type="PROGRESS_UPDATE",
        source_kind="test",
        expected_head_sha256="0" * 64,
    )
    inspected_head = first["head_sha256"]
    record_text_event(
        ledger,
        second_source,
        event_id="second",
        event_type="PROGRESS_UPDATE",
        source_kind="test",
        expected_head_sha256=inspected_head,
    )
    before = ledger.verify()
    with pytest.raises(ZipJobRefusal, match="REFUSE_PROJECT_LEDGER_STALE_PARENT"):
        record_text_event(
            ledger,
            stale_source,
            event_id="stale",
            event_type="PROGRESS_UPDATE",
            source_kind="test",
            expected_head_sha256=inspected_head,
        )
    after = ledger.verify()
    assert after == before
    assert after["event_count"] == 2


def test_chain_tamper_refuses(tmp_path: Path) -> None:
    source = tmp_path / "plan.md"
    source.write_text("one\n", encoding="utf-8")
    ledger = ProjectLedger(tmp_path / "state")
    record_text_event(
        ledger,
        source,
        event_id="plan-1",
        event_type="PLAN_REVISION",
        source_kind="owner_plan",
    )
    row = json.loads(ledger.path.read_text(encoding="utf-8"))
    row["event"]["material"]["text"] = "forged\n"
    ledger.path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ZipJobRefusal, match="REFUSE_PROJECT_LEDGER_DIGEST"):
        ledger.verify()


def test_imported_artifact_survives_source_removal(tmp_path: Path) -> None:
    source = tmp_path / "outside.md"
    source.write_bytes(b"external evidence\n")
    ledger = ProjectLedger(tmp_path / "state")
    import_artifact(ledger, source, source_kind="hermes_plan")
    source.unlink()

    assert ledger.verify()["objects_verified"] is True
    row = json.loads(ledger.path.read_text(encoding="utf-8"))
    object_path = ledger.root / row["event"]["material"]["object_path"]
    assert gzip.decompress(object_path.read_bytes()) == b"external evidence\n"


def test_codex_rollout_retains_snapshot_and_verbatim_messages(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout.jsonl"
    rows = [
        {"type": "session_meta", "timestamp": "t0", "payload": {"id": "thread-1"}},
        {
            "type": "response_item",
            "timestamp": "t1",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "owner bytes\n"}],
            },
        },
        {
            "type": "response_item",
            "timestamp": "t2",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "model bytes\n"}],
            },
        },
    ]
    rollout.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    ledger = ProjectLedger(tmp_path / "state")

    result = import_codex_rollout(ledger, rollout)
    repeated = import_codex_rollout(ledger, rollout)

    assert result["conversation_event_count"] == 2
    assert repeated["added_event_count"] == 0
    assert ledger.verify()["event_count"] == 3
    events = [json.loads(line)["event"] for line in ledger.path.read_text().splitlines()]
    assert [event["material"].get("text") for event in events[1:]] == [
        "owner bytes\n",
        "model bytes\n",
    ]


def test_codex_resync_retains_only_verified_append_delta(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout.jsonl"
    initial = (
        json.dumps({"type": "session_meta", "payload": {"id": "thread-delta"}}) + "\n"
    ).encode()
    rollout.write_bytes(initial)
    ledger = ProjectLedger(tmp_path / "state")
    first = import_codex_rollout(ledger, rollout)

    appended = (
        json.dumps(
            {
                "type": "response_item",
                "timestamp": "t1",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "new owner bytes"}],
                },
            }
        )
        + "\n"
    ).encode()
    rollout.write_bytes(initial + appended)
    second = import_codex_rollout(ledger, rollout)

    assert first["source_artifact_kind"] == "full_snapshot"
    assert second["source_artifact_kind"] == "append_delta"
    assert second["source_artifact_sha256"] is not None
    rows = [json.loads(line)["event"] for line in ledger.path.read_text().splitlines()]
    delta = next(event for event in rows if event["event_type"] == "SOURCE_DELTA_IMPORTED")
    delta_path = ledger.root / delta["material"]["object_path"]
    assert gzip.decompress(delta_path.read_bytes()) == appended
    assert delta["metadata"]["byte_start"] == len(initial)
    assert delta["metadata"]["complete_through_byte_length"] == len(initial + appended)


def _hermes_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            model TEXT,
            title TEXT,
            started_at REAL,
            last_activity_at REAL
        );
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp REAL,
            active INTEGER,
            compacted INTEGER
        );
        INSERT INTO sessions VALUES ('hermes-1', 'grok-test', 'test', 1, 3);
        INSERT INTO messages VALUES (1, 'hermes-1', 'user', 'old owner', 1, 0, 1);
        INSERT INTO messages VALUES (2, 'hermes-1', 'tool', 'tool work', 2, 0, 1);
        INSERT INTO messages VALUES (3, 'hermes-1', 'assistant', 'current answer', 3, 1, 0);
        """
    )
    connection.commit()
    connection.close()


def test_hermes_import_includes_active_and_compacted_rows(tmp_path: Path) -> None:
    database = tmp_path / "state.db"
    _hermes_database(database)
    ledger = ProjectLedger(tmp_path / "state")

    result = import_hermes_session(ledger, database, "hermes-1")

    assert result["source_message_count"] == 3
    assert result["conversation_event_count"] == 2
    assert ledger.verify()["event_count"] == 3
    snapshot = json.loads(ledger.path.read_text().splitlines()[0])["event"]
    assert snapshot["metadata"]["includes_active_and_compacted_rows"] is True


def test_hermes_resync_retains_append_delta_when_prior_rows_are_unchanged(
    tmp_path: Path,
) -> None:
    database = tmp_path / "state.db"
    _hermes_database(database)
    ledger = ProjectLedger(tmp_path / "state")
    first = import_hermes_session(ledger, database, "hermes-1")
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO messages VALUES (4, 'hermes-1', 'user', 'new owner', 4, 1, 0)"
    )
    connection.execute("UPDATE sessions SET last_activity_at=4 WHERE id='hermes-1'")
    connection.commit()
    connection.close()

    second = import_hermes_session(ledger, database, "hermes-1")

    assert first["source_artifact_kind"] == "full_snapshot"
    assert second["source_artifact_kind"] == "append_delta"
    rows = [json.loads(line)["event"] for line in ledger.path.read_text().splitlines()]
    delta = next(event for event in rows if event["event_type"] == "SOURCE_DELTA_IMPORTED")
    raw_delta = gzip.decompress(
        (ledger.root / delta["material"]["object_path"]).read_bytes()
    )
    assert b'"content":"new owner"' in raw_delta
    assert b'"id":4' in raw_delta


def test_current_view_is_derived_from_verified_ledger(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("1. prove the direct route\n", encoding="utf-8")
    progress = tmp_path / "progress.md"
    progress.write_text("ledger landed; waves pending\n", encoding="utf-8")
    ledger = ProjectLedger(tmp_path / "state")
    record_text_event(
        ledger,
        plan,
        event_id="plan-1",
        event_type="PLAN_REVISION",
        source_kind="owner_plan",
    )
    record_text_event(
        ledger,
        progress,
        event_id="progress-1",
        event_type="PROGRESS_UPDATE",
        source_kind="controller_progress",
    )

    destination = tmp_path / "CURRENT.md"
    result = write_current_view(ledger, destination)

    assert result["disposition"] == "PROJECT_CURRENT_VIEW_RENDERED"
    text = destination.read_text(encoding="utf-8")
    assert "projection, not authority" in text
    assert "Projection generated at:" in text
    assert "Last ledger event recorded at:" in text
    assert "prove the direct route" in text
    assert "ledger landed; waves pending" in text
