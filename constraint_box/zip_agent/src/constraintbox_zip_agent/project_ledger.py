from __future__ import annotations

import fcntl
import gzip
import hashlib
import json
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .protocol import ZipJobRefusal, canonical_json_bytes, sha256_bytes


LEDGER_SCHEMA = "constraintbox.project-ledger-line.v1"
EVENT_SCHEMA = "constraintbox.project-event.v1"
GENESIS_SHA256 = "0" * 64


def _iso_from_epoch(value: float | int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _gzip_bytes(data: bytes) -> bytes:
    return gzip.compress(data, compresslevel=9, mtime=0)


def _material_for_text(text: str) -> dict[str, Any]:
    raw = text.encode("utf-8")
    return {
        "kind": "verbatim_text",
        "encoding": "utf-8",
        "byte_length": len(raw),
        "sha256": sha256_bytes(raw),
        "text": text,
    }


class ProjectLedger:
    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        self.path = self.root / "events.jsonl"
        self.head_path = self.root / "HEAD"
        self.lock_path = self.root / ".append.lock"
        self.objects = self.root / "objects" / "sha256"

    def _rows(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with self.path.open("rb") as stream:
            for line_number, raw in enumerate(stream, start=1):
                if not raw.endswith(b"\n"):
                    raise ZipJobRefusal("REFUSE_PROJECT_LEDGER_TRUNCATED", str(line_number))
                try:
                    row = json.loads(raw)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ZipJobRefusal("REFUSE_PROJECT_LEDGER_JSON", f"{line_number}:{exc}") from exc
                if not isinstance(row, dict):
                    raise ZipJobRefusal("REFUSE_PROJECT_LEDGER_SHAPE", str(line_number))
                rows.append(row)
        return rows

    def verify(self, *, verify_objects: bool = True) -> dict[str, Any]:
        previous = GENESIS_SHA256
        event_ids: set[str] = set()
        rows = self._rows()
        for sequence, row in enumerate(rows, start=1):
            if row.get("schema") != LEDGER_SCHEMA or row.get("sequence") != sequence:
                raise ZipJobRefusal("REFUSE_PROJECT_LEDGER_SHAPE", str(sequence))
            if row.get("previous_sha256") != previous:
                raise ZipJobRefusal("REFUSE_PROJECT_LEDGER_CHAIN", str(sequence))
            event = row.get("event")
            if not isinstance(event, dict) or event.get("schema") != EVENT_SCHEMA:
                raise ZipJobRefusal("REFUSE_PROJECT_EVENT_SHAPE", str(sequence))
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or not event_id or event_id in event_ids:
                raise ZipJobRefusal("REFUSE_PROJECT_EVENT_ID", str(sequence))
            event_ids.add(event_id)
            body = {
                "schema": LEDGER_SCHEMA,
                "sequence": sequence,
                "previous_sha256": previous,
                "event": event,
            }
            observed = sha256_bytes(canonical_json_bytes(body))
            if row.get("line_sha256") != observed:
                raise ZipJobRefusal("REFUSE_PROJECT_LEDGER_DIGEST", str(sequence))
            self._verify_material(event.get("material"), verify_object=verify_objects)
            previous = observed
        if self.head_path.exists():
            head = self.head_path.read_text(encoding="ascii").strip()
            if head != previous:
                raise ZipJobRefusal("REFUSE_PROJECT_LEDGER_HEAD", head)
        elif rows:
            raise ZipJobRefusal("REFUSE_PROJECT_LEDGER_HEAD", "missing")
        return {
            "disposition": "PROJECT_LEDGER_VERIFIED",
            "event_count": len(rows),
            "head_sha256": previous,
            "objects_verified": verify_objects,
            "promotion_allowed": False,
        }

    def _verify_material(self, material: Any, *, verify_object: bool) -> None:
        if not isinstance(material, dict):
            raise ZipJobRefusal("REFUSE_PROJECT_EVENT_MATERIAL", "shape")
        kind = material.get("kind")
        expected = material.get("sha256")
        expected_length = material.get("byte_length")
        if not isinstance(expected, str) or len(expected) != 64:
            raise ZipJobRefusal("REFUSE_PROJECT_EVENT_MATERIAL", "sha256")
        if isinstance(expected_length, bool) or not isinstance(expected_length, int):
            raise ZipJobRefusal("REFUSE_PROJECT_EVENT_MATERIAL", "byte_length")
        if kind == "verbatim_text":
            text = material.get("text")
            if not isinstance(text, str):
                raise ZipJobRefusal("REFUSE_PROJECT_EVENT_MATERIAL", "text")
            raw = text.encode("utf-8")
        elif kind == "artifact_object":
            relative = material.get("object_path")
            if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
                raise ZipJobRefusal("REFUSE_PROJECT_EVENT_MATERIAL", "object_path")
            if not verify_object:
                return
            path = self.root / relative
            if not path.is_file():
                raise ZipJobRefusal("REFUSE_PROJECT_OBJECT_MISSING", relative)
            try:
                raw = gzip.decompress(path.read_bytes())
            except (OSError, EOFError) as exc:
                raise ZipJobRefusal("REFUSE_PROJECT_OBJECT_GZIP", relative) from exc
        else:
            raise ZipJobRefusal("REFUSE_PROJECT_EVENT_MATERIAL", str(kind))
        if len(raw) != expected_length or sha256_bytes(raw) != expected:
            raise ZipJobRefusal("REFUSE_PROJECT_EVENT_MATERIAL_DIGEST", expected)

    def store_object(self, raw: bytes) -> dict[str, Any]:
        digest = sha256_bytes(raw)
        relative = Path("objects") / "sha256" / f"{digest}.gz"
        target = self.root / relative
        compressed = _gzip_bytes(raw)
        if target.exists():
            try:
                existing = gzip.decompress(target.read_bytes())
            except (OSError, EOFError) as exc:
                raise ZipJobRefusal("REFUSE_PROJECT_OBJECT_GZIP", str(relative)) from exc
            if existing != raw:
                raise ZipJobRefusal("REFUSE_PROJECT_OBJECT_COLLISION", digest)
        else:
            _atomic_write(target, compressed)
        return {
            "kind": "artifact_object",
            "encoding": "binary",
            "storage_encoding": "gzip",
            "byte_length": len(raw),
            "stored_byte_length": len(compressed),
            "sha256": digest,
            "object_path": relative.as_posix(),
        }

    def append_many(
        self,
        events: Iterable[dict[str, Any]],
        *,
        expected_head_sha256: str | None = None,
    ) -> dict[str, Any]:
        values = list(events)
        if not values:
            return self.verify()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock_path.touch(exist_ok=True)
        with self.lock_path.open("rb") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            verified = self.verify()
            if expected_head_sha256 is not None:
                if (
                    len(expected_head_sha256) != 64
                    or any(ch not in "0123456789abcdef" for ch in expected_head_sha256)
                ):
                    raise ZipJobRefusal(
                        "REFUSE_PROJECT_LEDGER_EXPECTED_HEAD", expected_head_sha256
                    )
                if verified["head_sha256"] != expected_head_sha256:
                    raise ZipJobRefusal(
                        "REFUSE_PROJECT_LEDGER_STALE_PARENT",
                        f"expected {expected_head_sha256}, current {verified['head_sha256']}",
                    )
            existing_rows = self._rows()
            existing = {str(row["event"]["event_id"]): row["event"] for row in existing_rows}
            previous = str(verified["head_sha256"])
            sequence = len(existing_rows)
            added = 0
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("ab") as stream:
                for event in values:
                    self._validate_event(event)
                    event_id = str(event["event_id"])
                    old = existing.get(event_id)
                    if old is not None:
                        if old != event:
                            raise ZipJobRefusal("REFUSE_PROJECT_EVENT_COLLISION", event_id)
                        continue
                    sequence += 1
                    body = {
                        "schema": LEDGER_SCHEMA,
                        "sequence": sequence,
                        "previous_sha256": previous,
                        "event": event,
                    }
                    line_sha256 = sha256_bytes(canonical_json_bytes(body))
                    stream.write(canonical_json_bytes({**body, "line_sha256": line_sha256}) + b"\n")
                    previous = line_sha256
                    existing[event_id] = event
                    added += 1
                stream.flush()
                os.fsync(stream.fileno())
            _atomic_write(self.head_path, (previous + "\n").encode("ascii"))
            result = self.verify()
            result["added_event_count"] = added
            return result

    def _validate_event(self, event: dict[str, Any]) -> None:
        if event.get("schema") != EVENT_SCHEMA:
            raise ZipJobRefusal("REFUSE_PROJECT_EVENT_SHAPE", "schema")
        for key in ("event_id", "event_type", "recorded_at"):
            if not isinstance(event.get(key), str) or not event[key]:
                raise ZipJobRefusal("REFUSE_PROJECT_EVENT_SHAPE", key)
        source = event.get("source")
        if not isinstance(source, dict) or not isinstance(source.get("kind"), str):
            raise ZipJobRefusal("REFUSE_PROJECT_EVENT_SHAPE", "source")
        for key in ("run_ids", "receipt_ids"):
            value = event.get(key)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise ZipJobRefusal("REFUSE_PROJECT_EVENT_SHAPE", key)
        if event.get("promotion_allowed") is not False:
            raise ZipJobRefusal("REFUSE_PROJECT_EVENT_SHAPE", "promotion_allowed")
        self._verify_material(event.get("material"), verify_object=True)


def project_event(
    *,
    event_id: str,
    event_type: str,
    recorded_at: str,
    source: dict[str, Any],
    material: dict[str, Any],
    run_ids: Iterable[str] = (),
    receipt_ids: Iterable[str] = (),
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": EVENT_SCHEMA,
        "event_id": event_id,
        "event_type": event_type,
        "recorded_at": recorded_at,
        "source": source,
        "material": material,
        "run_ids": list(run_ids),
        "receipt_ids": list(receipt_ids),
        "metadata": metadata or {},
        "claim_ceiling": "project_context_and_provenance_only;not_semantic_admission;not_promotion",
        "promotion_allowed": False,
    }


def import_artifact(
    ledger: ProjectLedger,
    path: Path,
    *,
    event_type: str = "EVIDENCE_ARTIFACT_IMPORTED",
    source_kind: str = "local_file",
    run_ids: Iterable[str] = (),
    receipt_ids: Iterable[str] = (),
) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    raw = resolved.read_bytes()
    stat = resolved.stat()
    material = ledger.store_object(raw)
    digest = str(material["sha256"])
    event = project_event(
        event_id=f"artifact:{source_kind}:{digest}",
        event_type=event_type,
        recorded_at=_iso_from_epoch(stat.st_mtime) or "1970-01-01T00:00:00Z",
        source={"kind": source_kind, "locator": str(resolved)},
        material=material,
        run_ids=run_ids,
        receipt_ids=receipt_ids,
        metadata={"source_name": resolved.name, "source_size": stat.st_size},
    )
    return ledger.append_many([event])


def _codex_text_blocks(payload: dict[str, Any]) -> list[str]:
    content = payload.get("content")
    if not isinstance(content, list):
        return []
    values: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") in {"input_text", "output_text"}:
            text = block.get("text")
            if isinstance(text, str):
                values.append(text)
    return values


def _source_import_material(
    ledger: ProjectLedger,
    raw: bytes,
    *,
    source_kind: str,
    session_id: str,
) -> tuple[dict[str, Any] | None, str | None, dict[str, Any]]:
    """Retain an append delta when prior source bytes are an exact prefix.

    A rewritten/truncated source falls back to a new full snapshot. Existing
    objects are never altered or removed.
    """
    prior = [
        row["event"]
        for row in ledger._rows()
        if row["event"].get("event_type")
        in {"SOURCE_SNAPSHOT_IMPORTED", "SOURCE_DELTA_IMPORTED"}
        and row["event"].get("source", {}).get("kind") == source_kind
        and row["event"].get("source", {}).get("session_id") == session_id
    ]
    cumulative_sha256 = sha256_bytes(raw)
    if prior:
        latest = prior[-1]
        metadata = latest.get("metadata") or {}
        material = latest["material"]
        previous_length = metadata.get("complete_through_byte_length")
        if isinstance(previous_length, bool) or not isinstance(previous_length, int):
            previous_length = material["byte_length"]
        previous_sha256 = metadata.get("complete_through_sha256")
        if not isinstance(previous_sha256, str):
            previous_sha256 = material["sha256"]
        if (
            len(raw) >= previous_length
            and sha256_bytes(raw[:previous_length]) == previous_sha256
        ):
            delta = raw[previous_length:]
            common = {
                "source_artifact_kind": "append_delta",
                "byte_start": previous_length,
                "complete_through_byte_length": len(raw),
                "complete_through_sha256": cumulative_sha256,
                "base_event_id": latest["event_id"],
            }
            if not delta:
                return None, None, common
            return ledger.store_object(delta), "SOURCE_DELTA_IMPORTED", common
    return (
        ledger.store_object(raw),
        "SOURCE_SNAPSHOT_IMPORTED",
        {
            "source_artifact_kind": "full_snapshot",
            "byte_start": 0,
            "complete_through_byte_length": len(raw),
            "complete_through_sha256": cumulative_sha256,
        },
    )


def import_codex_rollout(ledger: ProjectLedger, rollout: Path) -> dict[str, Any]:
    resolved = rollout.expanduser().resolve()
    raw = resolved.read_bytes()
    session_id = "unknown"
    message_events: list[dict[str, Any]] = []
    parsed_lines = 0
    for line_number, line in enumerate(raw.splitlines(), start=1):
        try:
            row = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ZipJobRefusal("REFUSE_CODEX_ROLLOUT_JSON", f"{line_number}:{exc}") from exc
        parsed_lines += 1
        if row.get("type") == "session_meta" and isinstance(row.get("payload"), dict):
            session_id = str(row["payload"].get("id") or session_id)
        if row.get("type") != "response_item" or not isinstance(row.get("payload"), dict):
            continue
        payload = row["payload"]
        role = payload.get("role")
        if payload.get("type") != "message" or role not in {"user", "assistant"}:
            continue
        for block_index, text in enumerate(_codex_text_blocks(payload)):
            message_events.append(
                project_event(
                    event_id=f"codex:{session_id}:{line_number}:{block_index}",
                    event_type="OWNER_PROMPT" if role == "user" else "ASSISTANT_OBSERVATION",
                    recorded_at=str(row.get("timestamp") or "unknown"),
                    source={
                        "kind": "codex_rollout_message",
                        "session_id": session_id,
                        "source_record": line_number,
                        "role": role,
                        "locator": str(resolved),
                    },
                    material=_material_for_text(text),
                    metadata={"content_block": block_index},
                )
            )
    artifact, source_event_type, source_metadata = _source_import_material(
        ledger,
        raw,
        source_kind="codex_rollout",
        session_id=session_id,
    )
    source_events: list[dict[str, Any]] = []
    if artifact is not None and source_event_type is not None:
        source_events.append(
            project_event(
                event_id=(
                    f"codex-source:{session_id}:"
                    f"{source_metadata['byte_start']}:{len(raw)}:"
                    f"{source_metadata['complete_through_sha256']}"
                ),
                event_type=source_event_type,
                recorded_at=_iso_from_epoch(resolved.stat().st_mtime)
                or "1970-01-01T00:00:00Z",
                source={
                    "kind": "codex_rollout",
                    "session_id": session_id,
                    "locator": str(resolved),
                },
                material=artifact,
                metadata={
                    **source_metadata,
                    "source_line_count": parsed_lines,
                    "imported_conversation_event_count": len(message_events),
                },
            )
        )
    result = ledger.append_many([*source_events, *message_events])
    result.update(
        {
            "source": "codex",
            "session_id": session_id,
            "source_line_count": parsed_lines,
            "conversation_event_count": len(message_events),
            "snapshot_sha256": sha256_bytes(raw),
            "source_artifact_kind": source_metadata["source_artifact_kind"],
            "source_artifact_sha256": artifact["sha256"] if artifact is not None else None,
        }
    )
    return result


def _hermes_export(connection: sqlite3.Connection, session_id: str) -> tuple[bytes, dict[str, Any], list[dict[str, Any]]]:
    connection.row_factory = sqlite3.Row
    session = connection.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    if session is None:
        raise ZipJobRefusal("REFUSE_HERMES_SESSION_MISSING", session_id)
    cursor = connection.execute("SELECT * FROM messages WHERE session_id=? ORDER BY id", (session_id,))
    columns = [item[0] for item in cursor.description]
    rows = cursor.fetchall()
    output = bytearray()
    conversation: list[dict[str, Any]] = []
    for row in rows:
        value = {column: row[column] for column in columns}
        output.extend(canonical_json_bytes(value) + b"\n")
        if value.get("role") in {"user", "assistant"} and isinstance(value.get("content"), str):
            conversation.append(value)
    return bytes(output), dict(session), conversation


def import_hermes_session(ledger: ProjectLedger, database: Path, session_id: str) -> dict[str, Any]:
    resolved = database.expanduser().resolve()
    connection = sqlite3.connect(f"file:{resolved}?mode=ro", uri=True)
    try:
        connection.execute("BEGIN")
        raw, session, conversation = _hermes_export(connection, session_id)
        connection.rollback()
    finally:
        connection.close()
    events: list[dict[str, Any]] = []
    for row in conversation:
        message_id = int(row["id"])
        role = str(row["role"])
        events.append(
            project_event(
                event_id=f"hermes:{session_id}:{message_id}",
                event_type="OWNER_PROMPT" if role == "user" else "ASSISTANT_OBSERVATION",
                recorded_at=_iso_from_epoch(row.get("timestamp")) or "unknown",
                source={
                    "kind": "hermes_message",
                    "session_id": session_id,
                    "source_record": message_id,
                    "role": role,
                    "locator": str(resolved),
                },
                material=_material_for_text(str(row["content"])),
                metadata={"active": bool(row.get("active")), "compacted": bool(row.get("compacted"))},
            )
        )
    artifact, source_event_type, source_metadata = _source_import_material(
        ledger,
        raw,
        source_kind="hermes_session",
        session_id=session_id,
    )
    source_events: list[dict[str, Any]] = []
    if artifact is not None and source_event_type is not None:
        source_events.append(
            project_event(
                event_id=(
                    f"hermes-source:{session_id}:"
                    f"{source_metadata['byte_start']}:{len(raw)}:"
                    f"{source_metadata['complete_through_sha256']}"
                ),
                event_type=source_event_type,
                recorded_at=_iso_from_epoch(
                    session.get("last_activity_at") or session.get("started_at")
                )
                or "unknown",
                source={
                    "kind": "hermes_session",
                    "session_id": session_id,
                    "locator": str(resolved),
                },
                material=artifact,
                metadata={
                    **source_metadata,
                    "source_message_count": raw.count(b"\n"),
                    "imported_conversation_event_count": len(events),
                    "session_model": session.get("model"),
                    "session_title": session.get("title"),
                    "includes_active_and_compacted_rows": True,
                },
            )
        )
    result = ledger.append_many([*source_events, *events])
    result.update(
        {
            "source": "hermes",
            "session_id": session_id,
            "source_message_count": raw.count(b"\n"),
            "conversation_event_count": len(events),
            "snapshot_sha256": sha256_bytes(raw),
            "source_artifact_kind": source_metadata["source_artifact_kind"],
            "source_artifact_sha256": artifact["sha256"] if artifact is not None else None,
        }
    )
    return result


def record_text_event(
    ledger: ProjectLedger,
    source_file: Path,
    *,
    event_id: str,
    event_type: str,
    source_kind: str,
    run_ids: Iterable[str] = (),
    receipt_ids: Iterable[str] = (),
    expected_head_sha256: str | None = None,
) -> dict[str, Any]:
    resolved = source_file.expanduser().resolve()
    text = resolved.read_text(encoding="utf-8")
    event = project_event(
        event_id=event_id,
        event_type=event_type,
        recorded_at=_iso_from_epoch(resolved.stat().st_mtime) or "unknown",
        source={"kind": source_kind, "locator": str(resolved)},
        material=_material_for_text(text),
        run_ids=run_ids,
        receipt_ids=receipt_ids,
        metadata={"source_name": resolved.name},
    )
    return ledger.append_many([event], expected_head_sha256=expected_head_sha256)


def render_current_view(ledger: ProjectLedger) -> bytes:
    verified = ledger.verify()
    rows = ledger._rows()
    events = [row["event"] for row in rows]
    generated_at = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")
    last_event_at = str(events[-1]["recorded_at"]) if events else "none"
    type_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    for event in events:
        event_type = str(event["event_type"])
        source_kind = str(event["source"]["kind"])
        type_counts[event_type] = type_counts.get(event_type, 0) + 1
        source_counts[source_kind] = source_counts.get(source_kind, 0) + 1
    plans = [event for event in events if event["event_type"] == "PLAN_REVISION"]
    progress = [event for event in events if event["event_type"] == "PROGRESS_UPDATE"]
    snapshots = [event for event in events if event["event_type"] == "SOURCE_SNAPSHOT_IMPORTED"]
    deltas = [event for event in events if event["event_type"] == "SOURCE_DELTA_IMPORTED"]
    lines = [
        "# ConstraintBox ZIP project — current derived view",
        "",
        "> Generated from the verified append-only ledger. This file is a projection, not authority.",
        "",
        f"- Projection generated at: `{generated_at}`",
        f"- Last ledger event recorded at: `{last_event_at}`",
        f"- Ledger events: {verified['event_count']}",
        f"- Ledger head: `{verified['head_sha256']}`",
        f"- Source snapshots: {len(snapshots)}",
        f"- Source append deltas: {len(deltas)}",
        f"- Plan revisions: {len(plans)}",
        f"- Progress updates: {len(progress)}",
        "- Promotion allowed: false",
        "",
        "## Event counts",
        "",
        *[f"- `{key}`: {type_counts[key]}" for key in sorted(type_counts)],
        "",
        "## Source counts",
        "",
        *[f"- `{key}`: {source_counts[key]}" for key in sorted(source_counts)],
        "",
        "## Imported source snapshots",
        "",
    ]
    for event in [*snapshots, *deltas]:
        source = event["source"]
        lines.append(
            f"- `{event['metadata'].get('source_artifact_kind', 'full_snapshot')}` "
            f"`{source.get('kind')}` `{source.get('session_id', source.get('locator', 'unknown'))}` "
            f"-> object `{event['material']['sha256']}`, cumulative "
            f"`{event['metadata'].get('complete_through_sha256', event['material']['sha256'])}`"
        )
    lines.extend(["", "## Latest plan revision", ""])
    if plans:
        lines.append(plans[-1]["material"]["text"])
    else:
        lines.append("No plan revision has been recorded.")
    lines.extend(["", "## Latest progress update", ""])
    if progress:
        lines.append(progress[-1]["material"]["text"])
    else:
        lines.append("No progress update has been recorded.")
    lines.extend(
        [
            "",
            "## Claim ceiling",
            "",
            "This view proves ledger integrity and retained source bytes only. It does not prove semantic completeness, model attention, host enforcement, promotion, or release.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def write_current_view(ledger: ProjectLedger, destination: Path) -> dict[str, Any]:
    data = render_current_view(ledger)
    _atomic_write(destination.expanduser().resolve(), data)
    return {
        "disposition": "PROJECT_CURRENT_VIEW_RENDERED",
        "path": str(destination.expanduser().resolve()),
        "sha256": sha256_bytes(data),
        "promotion_allowed": False,
    }


def run_append_project_ledger(task: Any, workspace: dict[str, bytes]) -> dict[str, bytes]:
    from .protocol import TaskSpec, strict_json_loads

    if not isinstance(task, TaskSpec):
        raise ZipJobRefusal("REFUSE_PROJECT_LEDGER_SCHEMA", "task")
    if len(task.input_paths) != 1 or len(task.output_paths) != 1:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    intent = strict_json_loads(workspace[task.input_paths[0]], label=task.input_paths[0])
    if not isinstance(intent, dict) or intent.get("schema") != "constraintbox.project-ledger-append.v1":
        raise ZipJobRefusal("REFUSE_PROJECT_LEDGER_SCHEMA", "intent")
    root = Path(str(intent.get("root") or Path(__file__).resolve().parents[2] / "project_state"))
    if not root.is_absolute():
        raise ZipJobRefusal("REFUSE_PROJECT_LEDGER_ROOT", str(root))
    text = str(intent.get("text") or "")
    if not text:
        raise ZipJobRefusal("REFUSE_PROJECT_LEDGER_SCHEMA", "text")
    source = root / "inbox" / f"{intent.get('event_id', 'event')}.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(text, encoding="utf-8")
    result = record_text_event(
        ProjectLedger(root),
        source,
        event_id=str(intent.get("event_id") or f"append:{sha256_bytes(text.encode())}"),
        event_type=str(intent.get("event_type") or "PROGRESS_UPDATE"),
        source_kind=str(intent.get("source") or "cb_packet"),
        expected_head_sha256=(
            str(intent["expected_head_sha256"])
            if intent.get("expected_head_sha256") is not None
            else None
        ),
    )
    result["current_view"] = write_current_view(ProjectLedger(root), root / "CURRENT.md")
    return {task.output_paths[0]: canonical_json_bytes(result)}
