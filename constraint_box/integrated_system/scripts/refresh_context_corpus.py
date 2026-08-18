#!/usr/bin/env python3
"""Append a declared Codex rollout to the compact context corpus.

This is deliberately a *refresh* utility, not a rollout archive.  It reads a
rollout once, extracts text message blocks, and stores only the selected event
projection.  The rollout itself is never copied into the product package.

The old project ledger is not a runtime dependency of the compact corpus.  A
refresh instead binds the current corpus, the exact source file, and a small
hash-chained refresh record.  A later refresh of the same source must have an
unchanged byte prefix; a changed or shortened source is refused.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "constraintbox.context-corpus-refresh.v1"
LEDGER_SCHEMA = "constraintbox.context-corpus-refresh-ledger.v1"
PENDING_SCHEMA = "constraintbox.context-corpus-refresh-pending.v1"
EVENT_SCHEMA = "constraintbox.project-event.v1"
ZERO_DIGEST = "0" * 64
PLATFORM_PREFIXES = ("<recommended_plugins>", "# AGENTS.md instructions")
TEXT_BLOCK_TYPES = frozenset({"input_text", "output_text", "text"})


class RefreshRefusal(ValueError):
    """An input or custody check failed; no refresh output is authoritative."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path, prefix_bytes: int | None = None) -> str:
    hasher = hashlib.sha256()
    remaining = prefix_bytes
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            if remaining is not None:
                if remaining <= 0:
                    break
                chunk = chunk[:remaining]
                remaining -= len(chunk)
            hasher.update(chunk)
            if remaining == 0:
                break
    if remaining is not None and remaining > 0:
        raise RefreshRefusal("source prefix is shorter than the prior source")
    return hasher.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RefreshRefusal(f"{label} unreadable: {type(exc).__name__}:{exc}") from exc
    if not isinstance(value, dict):
        raise RefreshRefusal(f"{label} is not an object")
    return value


def _material_digest(material: dict[str, Any], where: str) -> None:
    text = material.get("text")
    if not isinstance(text, str):
        raise RefreshRefusal(f"{where} material text is not a string")
    encoded = text.encode("utf-8")
    if material.get("sha256") != sha256_bytes(encoded):
        raise RefreshRefusal(f"{where} material hash mismatch")
    if material.get("byte_length") != len(encoded):
        raise RefreshRefusal(f"{where} material byte length mismatch")


def _event_fingerprint(event: dict[str, Any]) -> bytes:
    """Return the complete event bytes for duplicate diagnostics."""

    return canonical_json_bytes(event)


def _stable_source(event: dict[str, Any]) -> tuple[Any, Any, Any] | None:
    source = event.get("source")
    if not isinstance(source, dict):
        return None
    return (source.get("role"), source.get("session_id"), source.get("source_record"))


def _material_identity(event: dict[str, Any]) -> tuple[Any, Any] | None:
    material = event.get("material")
    if not isinstance(material, dict):
        return None
    return (material.get("sha256"), material.get("text"))


def _platform_text(event: dict[str, Any]) -> bool:
    material = event.get("material")
    return isinstance(material, dict) and isinstance(material.get("text"), str) and material[
        "text"
    ].lstrip().startswith(PLATFORM_PREFIXES)


def _compatible_event(existing: dict[str, Any], incoming: dict[str, Any]) -> bool:
    """Compare an old event with a refreshed event without rewriting old bytes.

    Older corpus rows did not carry the refresher's platform classification
    metadata.  Identity is therefore the event id, exact material, and stable
    source role/session/record.  The only permitted type change is the
    recognized platform-injected-user classification.
    """

    if _material_identity(existing) != _material_identity(incoming):
        return False
    if _stable_source(existing) != _stable_source(incoming):
        return False
    old_type = existing.get("event_type")
    new_type = incoming.get("event_type")
    if old_type == new_type:
        return True
    return (
        {old_type, new_type} == {"OWNER_PROMPT", "PLATFORM_INJECTED_USER"}
        and _platform_text(existing)
        and _platform_text(incoming)
    )


@dataclass(frozen=True)
class CorpusState:
    raw: bytes
    rows: tuple[dict[str, Any], ...]
    events: dict[str, dict[str, Any]]
    text_bytes: int


def load_corpus(corpus: Path, manifest: Path) -> CorpusState:
    """Validate the current corpus without normalizing or rewriting its bytes."""

    try:
        raw = corpus.read_bytes()
    except OSError as exc:
        raise RefreshRefusal(f"corpus unreadable: {type(exc).__name__}:{exc}") from exc
    manifest_value = _read_json(manifest, "manifest")
    expected_hash = manifest_value.get("output_sha256")
    if expected_hash is not None and expected_hash != sha256_bytes(raw):
        raise RefreshRefusal("corpus hash differs from manifest")
    expected_bytes = manifest_value.get("output_bytes")
    if expected_bytes is not None and expected_bytes != len(raw):
        raise RefreshRefusal("corpus byte count differs from manifest")

    rows: list[dict[str, Any]] = []
    events: dict[str, dict[str, Any]] = {}
    text_bytes = 0
    if raw:
        for line_number, raw_line in enumerate(raw.splitlines(), start=1):
            if not raw_line.strip():
                raise RefreshRefusal(f"corpus row {line_number} is blank")
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise RefreshRefusal(
                    f"corpus row {line_number} malformed: {exc}"
                ) from exc
            if not isinstance(row, dict) or not isinstance(row.get("event"), dict):
                raise RefreshRefusal(f"corpus row {line_number} is not an event row")
            event = row["event"]
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or not event_id:
                raise RefreshRefusal(f"corpus row {line_number} missing event_id")
            material = event.get("material")
            if not isinstance(material, dict):
                raise RefreshRefusal(f"corpus row {line_number} missing material")
            _material_digest(material, f"corpus row {line_number}")
            for digest_key in ("event_sha256", "event_digest"):
                if digest_key in row and row[digest_key] != _event_fingerprint(event):
                    raise RefreshRefusal(
                        f"corpus row {line_number} {digest_key} mismatch"
                    )
            prior = events.get(event_id)
            if prior is not None and not _compatible_event(prior, event):
                raise RefreshRefusal(
                    f"corpus duplicate event_id has different bytes: {event_id}"
                )
            events[event_id] = event
            text_bytes += len(material["text"].encode("utf-8"))
            rows.append(row)
    return CorpusState(bytes(raw), tuple(rows), events, text_bytes)


def _source_checkpoint(record: dict[str, Any]) -> dict[str, str] | None:
    if record.get("type") != "session_meta":
        return None
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None
    session_id = payload.get("session_id")
    record_id = payload.get("id")
    if session_id is not None and (not isinstance(session_id, str) or not session_id):
        raise RefreshRefusal("source session_id checkpoint is malformed")
    if record_id is not None and (not isinstance(record_id, str) or not record_id):
        raise RefreshRefusal("source id checkpoint is malformed")
    if session_id is not None and record_id is not None and session_id != record_id:
        raise RefreshRefusal("source id/session_id checkpoint disagrees")
    session_id = session_id or record_id
    if not isinstance(session_id, str) or not session_id:
        return None
    checkpoint: dict[str, str] = {"session_id": session_id}
    forked_from = payload.get("forked_from_id")
    if isinstance(forked_from, str) and forked_from:
        checkpoint["forked_from_id"] = forked_from
    return checkpoint


def _message_rows(
    record: dict[str, Any],
    line_number: int,
    raw_line: bytes,
    source_path: Path,
    session_id: str,
    previous_line_digest: str,
) -> list[dict[str, Any]]:
    if record.get("type") != "response_item":
        return []
    payload = record.get("payload")
    if not isinstance(payload, dict) or payload.get("type") != "message":
        return []
    role = payload.get("role")
    if role not in {"user", "assistant"}:
        return []
    content = payload.get("content")
    if not isinstance(content, list):
        raise RefreshRefusal(f"source row {line_number} message content is malformed")
    line_digest = sha256_bytes(raw_line)
    message_id = payload.get("id")
    if not isinstance(message_id, str):
        message_id = ""
    rows: list[dict[str, Any]] = []
    selected_block_index = 0
    for block_index, block in enumerate(content):
        if not isinstance(block, dict):
            raise RefreshRefusal(f"source row {line_number} content block is malformed")
        block_type = block.get("type")
        text = block.get("text")
        if block_type not in TEXT_BLOCK_TYPES or not isinstance(text, str):
            continue
        # The original compact-corpus importer numbered only retained text
        # blocks.  Keep that identity stable across non-text image/tool blocks.
        event_id = f"codex:{session_id}:{line_number}:{selected_block_index}"
        encoded = text.encode("utf-8")
        platform_injected = role == "user" and text.lstrip().startswith(PLATFORM_PREFIXES)
        event_type = (
            "PLATFORM_INJECTED_USER"
            if platform_injected
            else "OWNER_PROMPT"
            if role == "user"
            else "ASSISTANT_OBSERVATION"
        )
        event: dict[str, Any] = {
            "claim_ceiling": "project_context_and_provenance_only;not_semantic_admission;not_promotion",
            "event_id": event_id,
            "event_type": event_type,
            "material": {
                "byte_length": len(encoded),
                "encoding": "utf-8",
                "kind": "verbatim_text",
                "sha256": sha256_bytes(encoded),
                "text": text,
            },
            "metadata": {
                "content_block": selected_block_index,
                "source_content_block": block_index,
                "message_id": message_id,
                "platform_injected": platform_injected,
            },
            "promotion_allowed": False,
            "receipt_ids": [],
            "run_ids": [],
            "schema": EVENT_SCHEMA,
            "source": {
                "kind": "codex_rollout_message",
                "locator": str(source_path.resolve()),
                "role": role,
                "session_id": session_id,
                "source_record": line_number,
            },
        }
        timestamp = record.get("timestamp")
        if isinstance(timestamp, str):
            event["recorded_at"] = timestamp
        rows.append(
            {
                "event": event,
                "source_line_sha256": line_digest,
                "source_previous_sha256": previous_line_digest,
                "source_sequence": line_number,
            }
        )
        selected_block_index += 1
    return rows


@dataclass(frozen=True)
class SourceState:
    path: Path
    size: int
    sha256: str
    # Hash of the complete source at ``size``.  The name is retained because
    # the refresh ledger uses it as the prefix anchor for the next growth.
    prefix_sha256: str
    checkpoint: dict[str, str]
    rows: tuple[dict[str, Any], ...]


def scan_source(source: Path, prior_size: int | None = None) -> SourceState:
    try:
        size = source.stat().st_size
    except OSError as exc:
        raise RefreshRefusal(f"source unreadable: {type(exc).__name__}:{exc}") from exc
    source_sha = _sha256_file(source)
    # A ledger row's prefix anchor must describe the whole source at that row's
    # source_size.  The *next* refresh hashes the old-size prefix before it
    # parses the source; storing only the old prefix here breaks growth-after-
    # growth refreshes.
    prefix_sha = source_sha
    checkpoint: dict[str, str] | None = None
    rows: list[dict[str, Any]] = []
    previous_line_digest = ZERO_DIGEST
    try:
        with source.open("rb") as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                if not raw_line.strip():
                    raise RefreshRefusal(f"source row {line_number} is blank")
                try:
                    record = json.loads(raw_line)
                except json.JSONDecodeError as exc:
                    raise RefreshRefusal(
                        f"source row {line_number} malformed: {exc}"
                    ) from exc
                if not isinstance(record, dict):
                    raise RefreshRefusal(f"source row {line_number} is not an object")
                possible_checkpoint = _source_checkpoint(record)
                if possible_checkpoint is not None:
                    checkpoint = possible_checkpoint
                if record.get("type") == "response_item":
                    payload = record.get("payload")
                    if isinstance(payload, dict) and payload.get("type") == "message":
                        if checkpoint is None:
                            raise RefreshRefusal(
                                "source message appears before a detectable checkpoint"
                            )
                        rows.extend(
                            _message_rows(
                                record,
                                line_number,
                                raw_line,
                                source,
                                checkpoint["session_id"],
                                previous_line_digest,
                            )
                        )
                previous_line_digest = sha256_bytes(raw_line)
    except OSError as exc:
        raise RefreshRefusal(f"source read failed: {type(exc).__name__}:{exc}") from exc
    if checkpoint is None:
        raise RefreshRefusal("source has no detectable session checkpoint")
    return SourceState(
        source.resolve(), size, source_sha, prefix_sha, checkpoint, tuple(rows)
    )


def _load_refresh_ledger(path: Path) -> tuple[list[dict[str, Any]], str]:
    if not path.exists():
        return [], ZERO_DIGEST
    try:
        lines = path.read_bytes().splitlines()
    except OSError as exc:
        raise RefreshRefusal(f"refresh ledger unreadable: {exc}") from exc
    rows: list[dict[str, Any]] = []
    previous = ZERO_DIGEST
    for line_number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip():
            raise RefreshRefusal(f"refresh ledger row {line_number} is blank")
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise RefreshRefusal(f"refresh ledger row {line_number} malformed") from exc
        if not isinstance(row, dict):
            raise RefreshRefusal(f"refresh ledger row {line_number} is not an object")
        observed = row.get("line_sha256")
        body = {key: value for key, value in row.items() if key != "line_sha256"}
        if observed != sha256_bytes(canonical_json_bytes(body)):
            raise RefreshRefusal(f"refresh ledger row {line_number} digest mismatch")
        if row.get("previous_sha256") != previous:
            raise RefreshRefusal(f"refresh ledger row {line_number} chain mismatch")
        if row.get("sequence") != len(rows) + 1:
            raise RefreshRefusal(f"refresh ledger row {line_number} sequence mismatch")
        previous = observed
        rows.append(row)
    return rows, previous


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _path_state(path: Path) -> tuple[bool, str]:
    """Return existence and digest without conflating missing with empty."""

    if not path.exists():
        return False, sha256_bytes(b"")
    try:
        return True, sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise RefreshRefusal(f"pending target unreadable: {path}: {exc}") from exc


def _pending_path(corpus: Path) -> Path:
    return corpus.resolve().parent / ".context-corpus-refresh.pending.json"


def _recover_pending(corpus: Path) -> dict[str, Any] | None:
    """Finish a prepared generation after an interrupted multi-file apply.

    Every target is allowed to be exactly its recorded old or new generation;
    any third hash is refused.  A target still at old must have its staged new
    bytes present and correctly hashed.  This makes a process crash resumable
    without pretending that three independent ``os.replace`` calls are one
    filesystem transaction.
    """

    pending_path = _pending_path(corpus)
    if not pending_path.exists():
        return None
    pending = _read_json(pending_path, "pending generation")
    if pending.get("schema") != PENDING_SCHEMA:
        raise RefreshRefusal("pending generation schema mismatch")
    targets = pending.get("targets")
    if not isinstance(targets, list) or not targets:
        raise RefreshRefusal("pending generation has no targets")
    old_state: dict[str, tuple[bool, str]] = {}
    new_state: dict[str, tuple[bool, str]] = {}
    for target in targets:
        if not isinstance(target, dict):
            raise RefreshRefusal("pending generation target malformed")
        name = target.get("name")
        path_text = target.get("path")
        stage_text = target.get("stage_path")
        if not all(isinstance(value, str) and value for value in (name, path_text, stage_text)):
            raise RefreshRefusal("pending generation target identity missing")
        path = Path(path_text)
        stage = Path(stage_text)
        if path == stage:
            raise RefreshRefusal("pending generation stage aliases target")
        old = (bool(target.get("old_exists")), target.get("old_sha256"))
        new = (bool(target.get("new_exists")), target.get("new_sha256"))
        if not isinstance(old[1], str) or not isinstance(new[1], str):
            raise RefreshRefusal("pending generation target digest missing")
        current = _path_state(path)
        if current != old and current != new:
            raise RefreshRefusal(f"pending target has unexpected third hash: {path}")
        old_state[name] = old
        new_state[name] = new
        if current == old:
            if not stage.exists():
                raise RefreshRefusal(f"pending staged target missing: {stage}")
            if _path_state(stage) != (True, new[1]):
                raise RefreshRefusal(f"pending staged target hash mismatch: {stage}")
    # Apply only targets that still expose the old generation.  If a prior
    # process already replaced one, its stage may have been consumed.
    for target in targets:
        path = Path(target["path"])
        stage = Path(target["stage_path"])
        current = _path_state(path)
        expected_new = (bool(target["new_exists"]), target["new_sha256"])
        if current == expected_new:
            continue
        os.replace(stage, path)
    for target in targets:
        path = Path(target["path"])
        expected_new = (bool(target["new_exists"]), target["new_sha256"])
        if _path_state(path) != expected_new:
            raise RefreshRefusal(f"pending target did not reach new generation: {path}")
        stage = Path(target["stage_path"])
        try:
            stage.unlink()
        except FileNotFoundError:
            pass
    try:
        pending_path.unlink()
    except FileNotFoundError:
        pass
    result = pending.get("result")
    if not isinstance(result, dict):
        result = {}
    return {
        **result,
        "disposition": "CONTEXT_CORPUS_REFRESH_RECOVERED",
        "recovered_from_pending": True,
        "pending_path": str(pending_path),
        "multi_file_atomicity_proved": False,
        "multi_file_recovery_proved": True,
        "multi_file_atomicity_status": "RECOVERABLE_PENDING_GENERATION",
    }


def _commit_pending_generation(
    corpus: Path,
    manifest: Path,
    refresh_ledger: Path,
    old_bytes: dict[str, bytes],
    new_bytes: dict[str, bytes],
    result: dict[str, Any],
    *,
    interrupt_after_target: int | None = None,
) -> Path:
    """Stage a generation, publish a pending record, then apply targets."""

    transaction_id = f"{result['refresh_digest'][:16]}-{result['new_corpus_sha256'][:16]}"
    pending_path = _pending_path(corpus)
    target_paths = {
        "corpus": corpus,
        "manifest": manifest,
        "refresh_ledger": refresh_ledger,
    }
    targets: list[dict[str, Any]] = []
    for name, path in target_paths.items():
        old_exists, old_hash = _path_state(path)
        if old_bytes[name] != (path.read_bytes() if old_exists else b""):
            raise RefreshRefusal(f"target changed while preparing generation: {path}")
        stage = corpus.resolve().parent / f".context-refresh.{transaction_id}.{name}.stage"
        _atomic_write(stage, new_bytes[name])
        new_exists, new_hash = True, sha256_bytes(new_bytes[name])
        targets.append(
            {
                "name": name,
                "path": str(path.resolve()),
                "stage_path": str(stage),
                "old_exists": old_exists,
                "old_sha256": old_hash,
                "new_exists": new_exists,
                "new_sha256": new_hash,
            }
        )
    pending = {
        "schema": PENDING_SCHEMA,
        "transaction_id": transaction_id,
        "created_at": _utc_now(),
        "targets": targets,
        "result": result,
    }
    _atomic_write(pending_path, (json.dumps(pending, sort_keys=True) + "\n").encode())
    replaced = 0
    for target in targets:
        path = Path(target["path"])
        stage = Path(target["stage_path"])
        old = (bool(target["old_exists"]), target["old_sha256"])
        new = (bool(target["new_exists"]), target["new_sha256"])
        current = _path_state(path)
        if current == new:
            continue
        if current != old:
            raise RefreshRefusal(f"target changed during generation: {path}")
        os.replace(stage, path)
        replaced += 1
        if interrupt_after_target is not None and replaced >= interrupt_after_target:
            raise RuntimeError("injected pending-generation interruption")
    # Verify before removing the recovery record.
    _recover_pending(corpus)
    return pending_path


def refresh_context_corpus(
    corpus: Path,
    manifest: Path,
    source: Path,
    refresh_ledger: Path,
    *,
    dry_run: bool = False,
    _interrupt_after_target: int | None = None,
) -> dict[str, Any]:
    recovered = _recover_pending(corpus)
    if recovered is not None:
        return recovered
    state = load_corpus(corpus, manifest)
    prior_ledger, previous_refresh_digest = _load_refresh_ledger(refresh_ledger)
    prior = prior_ledger[-1] if prior_ledger else None
    if prior is not None:
        if prior.get("source_path") != str(source.resolve()):
            raise RefreshRefusal("source path drift from prior refresh")
        prior_size = prior.get("source_size")
        if not isinstance(prior_size, int):
            raise RefreshRefusal("prior refresh has no source size")
        if source.stat().st_size < prior_size:
            raise RefreshRefusal("source shrink from prior refresh")
        # Check custody before parsing.  A changed prefix must be reported as
        # source drift even when the edit also makes a JSON line malformed.
        if _sha256_file(source, prior_size) != prior.get("source_prefix_sha256"):
            raise RefreshRefusal("source prefix drift from prior refresh")
        if state.raw and prior.get("new_corpus_sha256") != sha256_bytes(state.raw):
            raise RefreshRefusal("corpus drift from prior refresh")
    else:
        prior_size = None
    source_state = scan_source(source, prior_size)
    source_events: dict[str, dict[str, Any]] = {}
    new_rows: list[dict[str, Any]] = []
    for row in source_state.rows:
        event = row["event"]
        event_id = event["event_id"]
        previous_event = source_events.get(event_id)
        if previous_event is not None and not _compatible_event(previous_event, event):
            raise RefreshRefusal(f"source duplicate event_id has different bytes: {event_id}")
        source_events[event_id] = event
        existing = state.events.get(event_id)
        if existing is not None:
            if not _compatible_event(existing, event):
                raise RefreshRefusal(f"duplicate event_id has different bytes: {event_id}")
            continue
        if previous_event is None:
            new_rows.append(row)

    appended_bytes = b"".join(canonical_json_bytes(row) + b"\n" for row in new_rows)
    separator = b"" if not state.raw or state.raw.endswith((b"\n", b"\r")) else b"\n"
    new_raw = state.raw + (separator + appended_bytes if appended_bytes else b"")
    new_hash = sha256_bytes(new_raw)
    now = _utc_now()
    ledger_body: dict[str, Any] = {
        "schema": LEDGER_SCHEMA,
        "sequence": len(prior_ledger) + 1,
        "previous_sha256": previous_refresh_digest,
        "recorded_at": now,
        "prior_corpus_sha256": sha256_bytes(state.raw),
        "prior_corpus_bytes": len(state.raw),
        "prior_corpus_event_count": len(state.rows),
        "source_path": str(source_state.path),
        "source_size": source_state.size,
        "source_sha256": source_state.sha256,
        "source_prefix_sha256": source_state.prefix_sha256,
        "source_checkpoint": source_state.checkpoint,
        "appended_event_ids": [row["event"]["event_id"] for row in new_rows],
        "appended_event_count": len(new_rows),
        "new_corpus_sha256": new_hash,
        "new_corpus_bytes": len(new_raw),
        "new_corpus_event_count": len(state.rows) + len(new_rows),
        "multi_file_atomicity_proved": False,
        "multi_file_recovery_proved": True,
        "multi_file_atomicity_status": "RECOVERABLE_PENDING_GENERATION",
    }
    ledger_row = {
        **ledger_body,
        "line_sha256": sha256_bytes(canonical_json_bytes(ledger_body)),
    }
    manifest_value = _read_json(manifest, "manifest")
    new_manifest = dict(manifest_value)
    selected_event_types = Counter(
        row["event"]["event_type"] for row in state.rows
    )
    selected_event_types.update(row["event"]["event_type"] for row in new_rows)
    new_manifest.update(
        {
            "output_sha256": new_hash,
            "output_bytes": len(new_raw),
            "selected_event_count": len(state.rows) + len(new_rows),
            "selected_event_types": dict(sorted(selected_event_types.items())),
            "selected_text_bytes": state.text_bytes
            + sum(
                len(row["event"]["material"]["text"].encode("utf-8"))
                for row in new_rows
            ),
            "refresh_ledger": os.path.relpath(
                refresh_ledger.resolve(), manifest.resolve().parent.resolve()
            ),
            "refresh_last_digest": ledger_row["line_sha256"],
            "refresh_schema": SCHEMA,
            "multi_file_atomicity_proved": False,
            "multi_file_recovery_proved": True,
            "multi_file_atomicity_status": "RECOVERABLE_PENDING_GENERATION",
        }
    )
    result = {
        "schema": SCHEMA,
        "disposition": "CONTEXT_CORPUS_REFRESH_PLAN"
        if dry_run
        else "CONTEXT_CORPUS_REFRESHED_LOCAL",
        "source_path": str(source_state.path),
        "source_size": source_state.size,
        "source_sha256": source_state.sha256,
        "source_checkpoint": source_state.checkpoint,
        "appended_event_ids": ledger_row["appended_event_ids"],
        "appended_event_count": len(new_rows),
        "new_corpus_sha256": new_hash,
        "new_corpus_bytes": len(new_raw),
        "new_corpus_event_count": len(state.rows) + len(new_rows),
        "refresh_digest": ledger_row["line_sha256"],
        "multi_file_atomicity_proved": False,
        "multi_file_recovery_proved": True,
        "multi_file_atomicity_status": "RECOVERABLE_PENDING_GENERATION",
        "dry_run": dry_run,
        "promotion_allowed": False,
    }
    if dry_run:
        return result
    ledger_raw = refresh_ledger.read_bytes() if refresh_ledger.exists() else b""
    ledger_append = canonical_json_bytes(ledger_row) + b"\n"
    new_manifest_bytes = (json.dumps(new_manifest, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    _commit_pending_generation(
        corpus,
        manifest,
        refresh_ledger,
        {
            "corpus": state.raw,
            "manifest": manifest.read_bytes(),
            "refresh_ledger": ledger_raw,
        },
        {
            "corpus": new_raw,
            "manifest": new_manifest_bytes,
            "refresh_ledger": ledger_raw + ledger_append,
        },
        result,
        interrupt_after_target=_interrupt_after_target,
    )
    return result


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--refresh-ledger", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = refresh_context_corpus(
            args.corpus,
            args.manifest,
            args.source,
            args.refresh_ledger,
            dry_run=args.dry_run,
        )
    except (OSError, RefreshRefusal, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "disposition": "REFUSE_CONTEXT_CORPUS_REFRESH",
                    "detail": f"{type(exc).__name__}:{exc}",
                    "promotion_allowed": False,
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
