from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "refresh_context_corpus.py"
SPEC = importlib.util.spec_from_file_location("refresh_context_corpus", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
refresh = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = refresh
SPEC.loader.exec_module(refresh)


def _material(text: str) -> dict[str, object]:
    encoded = text.encode("utf-8")
    return {
        "byte_length": len(encoded),
        "encoding": "utf-8",
        "kind": "verbatim_text",
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "text": text,
    }


def _corpus_row(event_id: str, text: str, event_type: str = "OWNER_PROMPT") -> dict:
    return {
        "source_sequence": 1,
        "source_previous_sha256": refresh.ZERO_DIGEST,
        "source_line_sha256": "a" * 64,
        "event": {
            "claim_ceiling": "project_context_and_provenance_only;not_semantic_admission;not_promotion",
            "event_id": event_id,
            "event_type": event_type,
            "material": _material(text),
            "promotion_allowed": False,
            "schema": refresh.EVENT_SCHEMA,
        },
    }


def _rollout(path: Path, session: str, messages: list[tuple[str, str]]) -> None:
    rows = [
        {
            "timestamp": "2026-08-18T00:00:00.000Z",
            "type": "session_meta",
            "payload": {"session_id": session},
        }
    ]
    for index, (role, text) in enumerate(messages, start=1):
        rows.append(
            {
                "timestamp": f"2026-08-18T00:00:0{index}.000Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "id": f"message-{index}",
                    "role": role,
                    "content": [
                        {
                            "type": "input_text" if role == "user" else "output_text",
                            "text": text,
                        }
                    ],
                },
            }
        )
    path.write_bytes(
        b"".join(
            json.dumps(row, separators=(",", ":")).encode("utf-8") + b"\n"
            for row in rows
        )
    )


def _append_message(path: Path, role: str, text: str, index: int) -> None:
    row = {
        "timestamp": f"2026-08-18T00:01:{index:02d}.000Z",
        "type": "response_item",
        "payload": {
            "type": "message",
            "id": f"message-extra-{index}",
            "role": role,
            "content": [
                {
                    "type": "input_text" if role == "user" else "output_text",
                    "text": text,
                }
            ],
        },
    }
    with path.open("ab") as stream:
        stream.write(json.dumps(row, separators=(",", ":")).encode("utf-8") + b"\n")


def _fixture(tmp_path: Path, source_messages: list[tuple[str, str]]):
    corpus = tmp_path / "prompt_plan_progress_corpus.jsonl"
    initial = _corpus_row("old", "old prompt\n")
    corpus.write_bytes(refresh.canonical_json_bytes(initial) + b"\n")
    manifest = tmp_path / "CORPUS_MANIFEST.json"
    manifest.write_text(
        json.dumps(
            {
                "output": corpus.name,
                "output_bytes": corpus.stat().st_size,
                "output_sha256": hashlib.sha256(corpus.read_bytes()).hexdigest(),
                "selected_event_count": 1,
            }
        )
        + "\n"
    )
    source = tmp_path / "rollout.jsonl"
    _rollout(source, "session-1", source_messages)
    ledger = tmp_path / "CORPUS_REFRESH_LEDGER.jsonl"
    return corpus, manifest, source, ledger


def test_positive_append_and_platform_classification(tmp_path: Path) -> None:
    corpus, manifest, source, ledger = _fixture(
        tmp_path,
        [
            ("user", "new owner prompt"),
            ("assistant", "observed result"),
            ("user", "<recommended_plugins>\nInjected platform context"),
        ],
    )
    result = refresh.refresh_context_corpus(corpus, manifest, source, ledger)
    assert result["appended_event_count"] == 3
    rows = [json.loads(line) for line in corpus.read_bytes().splitlines()]
    assert [row["event"]["event_type"] for row in rows[1:]] == [
        "OWNER_PROMPT",
        "ASSISTANT_OBSERVATION",
        "PLATFORM_INJECTED_USER",
    ]
    assert len(ledger.read_bytes().splitlines()) == 1
    manifest_value = json.loads(manifest.read_text())
    assert manifest_value["selected_event_count"] == 4
    assert manifest_value["selected_event_types"] == {
        "ASSISTANT_OBSERVATION": 1,
        "OWNER_PROMPT": 2,
        "PLATFORM_INJECTED_USER": 1,
    }


def test_idempotent_noop_preserves_corpus_bytes(tmp_path: Path) -> None:
    corpus, manifest, source, ledger = _fixture(tmp_path, [("user", "new")])
    refresh.refresh_context_corpus(corpus, manifest, source, ledger)
    first = corpus.read_bytes()
    result = refresh.refresh_context_corpus(corpus, manifest, source, ledger)
    assert result["appended_event_count"] == 0
    assert corpus.read_bytes() == first
    assert len(ledger.read_bytes().splitlines()) == 2


def test_source_shrink_and_prefix_drift_refuse(tmp_path: Path) -> None:
    corpus, manifest, source, ledger = _fixture(tmp_path, [("user", "new")])
    refresh.refresh_context_corpus(corpus, manifest, source, ledger)
    original = source.read_bytes()
    source.write_bytes(original[:-2])
    with pytest.raises(refresh.RefreshRefusal, match="shrink"):
        refresh.refresh_context_corpus(corpus, manifest, source, ledger)
    source.write_bytes(b"X" + original)
    with pytest.raises(refresh.RefreshRefusal, match="prefix drift"):
        refresh.refresh_context_corpus(corpus, manifest, source, ledger)


def test_source_prefix_ratcheting_allows_two_growth_refreshes(tmp_path: Path) -> None:
    corpus, manifest, source, ledger = _fixture(tmp_path, [("user", "first")])
    first = refresh.refresh_context_corpus(corpus, manifest, source, ledger)
    _append_message(source, "assistant", "second", 2)
    second = refresh.refresh_context_corpus(corpus, manifest, source, ledger)
    _append_message(source, "user", "third", 3)
    third = refresh.refresh_context_corpus(corpus, manifest, source, ledger)
    assert first["appended_event_count"] == 1
    assert second["appended_event_count"] == 1
    assert third["appended_event_count"] == 1
    ledger_rows = [json.loads(line) for line in ledger.read_bytes().splitlines()]
    assert len(ledger_rows) == 3
    assert all(row["source_prefix_sha256"] == row["source_sha256"] for row in ledger_rows)


def test_legacy_owner_event_compatible_with_platform_reclassification(tmp_path: Path) -> None:
    corpus, manifest, source, ledger = _fixture(
        tmp_path, [("user", "<recommended_plugins>\nplatform context")]
    )
    legacy = _corpus_row(
        "codex:session-1:2:0",
        "<recommended_plugins>\nplatform context",
        "OWNER_PROMPT",
    )
    legacy["event"]["source"] = {
        "kind": "codex_rollout_message",
        "locator": str(source.resolve()),
        "role": "user",
        "session_id": "session-1",
        "source_record": 2,
    }
    corpus.write_bytes(refresh.canonical_json_bytes(legacy) + b"\n")
    manifest.write_text(
        json.dumps(
            {
                "output": corpus.name,
                "output_bytes": corpus.stat().st_size,
                "output_sha256": hashlib.sha256(corpus.read_bytes()).hexdigest(),
                "selected_event_count": 1,
            }
        )
        + "\n"
    )
    result = refresh.refresh_context_corpus(corpus, manifest, source, ledger)
    assert result["appended_event_count"] == 0
    # The old bytes/type remain untouched; compatibility does not rewrite them.
    assert json.loads(corpus.read_text())["event"]["event_type"] == "OWNER_PROMPT"


def test_conflicting_duplicate_refuses(tmp_path: Path) -> None:
    corpus, manifest, source, ledger = _fixture(tmp_path, [("user", "new")])
    first = _corpus_row("duplicate", "one")
    second = _corpus_row("duplicate", "two")
    corpus.write_bytes(
        b"\n".join(
            refresh.canonical_json_bytes(row) for row in (first, second)
        )
        + b"\n"
    )
    manifest.write_text(
        json.dumps(
            {
                "output": corpus.name,
                "output_bytes": corpus.stat().st_size,
                "output_sha256": hashlib.sha256(corpus.read_bytes()).hexdigest(),
            }
        )
        + "\n"
    )
    with pytest.raises(refresh.RefreshRefusal, match="duplicate event_id"):
        refresh.refresh_context_corpus(corpus, manifest, source, ledger)


def test_tampered_corpus_material_refuses(tmp_path: Path) -> None:
    corpus, manifest, source, ledger = _fixture(tmp_path, [("user", "new")])
    raw = corpus.read_text()
    corpus.write_text(raw.replace("old prompt", "tampered"))
    with pytest.raises(refresh.RefreshRefusal, match="corpus hash differs"):
        refresh.refresh_context_corpus(corpus, manifest, source, ledger)


def test_refresh_chain_tamper_refuses(tmp_path: Path) -> None:
    corpus, manifest, source, ledger = _fixture(tmp_path, [("user", "new")])
    refresh.refresh_context_corpus(corpus, manifest, source, ledger)
    row = json.loads(ledger.read_text())
    row["source_size"] += 1
    ledger.write_text(json.dumps(row) + "\n")
    with pytest.raises(refresh.RefreshRefusal, match="ledger row .* digest mismatch"):
        refresh.refresh_context_corpus(corpus, manifest, source, ledger)


def test_interrupted_pending_generation_recovers(tmp_path: Path) -> None:
    corpus, manifest, source, ledger = _fixture(tmp_path, [("user", "new")])
    with pytest.raises(RuntimeError, match="injected pending-generation"):
        refresh.refresh_context_corpus(
            corpus,
            manifest,
            source,
            ledger,
            _interrupt_after_target=1,
        )
    pending = corpus.parent / ".context-corpus-refresh.pending.json"
    assert pending.exists()
    recovered = refresh.refresh_context_corpus(corpus, manifest, source, ledger)
    assert recovered["disposition"] == "CONTEXT_CORPUS_REFRESH_RECOVERED"
    assert recovered["recovered_from_pending"] is True
    assert recovered["multi_file_recovery_proved"] is True
    assert recovered["multi_file_atomicity_proved"] is False
    assert not pending.exists()
    manifest_value = json.loads(manifest.read_text())
    assert manifest_value["output_sha256"] == hashlib.sha256(corpus.read_bytes()).hexdigest()
    assert len(ledger.read_bytes().splitlines()) == 1


def test_missing_checkpoint_and_malformed_source_refuse(tmp_path: Path) -> None:
    corpus, manifest, source, ledger = _fixture(tmp_path, [("user", "new")])
    source.write_text(json.dumps({"type": "response_item", "payload": {}}) + "\n")
    with pytest.raises(refresh.RefreshRefusal, match="checkpoint"):
        refresh.refresh_context_corpus(corpus, manifest, source, ledger)
    source.write_bytes(b"not-json\n")
    with pytest.raises(refresh.RefreshRefusal, match="malformed"):
        refresh.refresh_context_corpus(corpus, manifest, source, ledger)


def test_checkpoint_accepts_id_or_matching_session_id(tmp_path: Path) -> None:
    corpus, manifest, source, ledger = _fixture(tmp_path, [("user", "new")])
    source_lines = source.read_bytes().splitlines()
    meta = json.loads(source_lines[0])
    meta["payload"] = {"id": "session-1", "session_id": "session-1"}
    source_lines[0] = json.dumps(meta, separators=(",", ":")).encode("utf-8")
    source.write_bytes(b"\n".join(source_lines) + b"\n")
    assert refresh.refresh_context_corpus(corpus, manifest, source, ledger)[
        "source_checkpoint"
    ] == {"session_id": "session-1"}

    mismatch_dir = tmp_path / "mismatch"
    mismatch_dir.mkdir()
    corpus, manifest, source, ledger = _fixture(mismatch_dir, [("user", "new")])
    source_lines = source.read_bytes().splitlines()
    meta = json.loads(source_lines[0])
    meta["payload"] = {"id": "other", "session_id": "session-1"}
    source_lines[0] = json.dumps(meta, separators=(",", ":")).encode("utf-8")
    source.write_bytes(b"\n".join(source_lines) + b"\n")
    with pytest.raises(refresh.RefreshRefusal, match="disagrees"):
        refresh.refresh_context_corpus(corpus, manifest, source, ledger)


def test_dry_run_does_not_write(tmp_path: Path) -> None:
    corpus, manifest, source, ledger = _fixture(tmp_path, [("user", "new")])
    before = (corpus.read_bytes(), manifest.read_bytes(), ledger.exists())
    result = refresh.refresh_context_corpus(
        corpus, manifest, source, ledger, dry_run=True
    )
    assert result["disposition"] == "CONTEXT_CORPUS_REFRESH_PLAN"
    assert result["dry_run"] is True
    assert result["multi_file_atomicity_proved"] is False
    assert result["multi_file_recovery_proved"] is True
    assert result["multi_file_atomicity_status"] == "RECOVERABLE_PENDING_GENERATION"
    assert (corpus.read_bytes(), manifest.read_bytes(), ledger.exists()) == before
