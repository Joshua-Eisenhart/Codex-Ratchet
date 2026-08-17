"""Narrow append-only SQLite state for contained CB Light Mini-Lev attempts.

This is deliberately not a generic receipt ledger.  Each row binds one
finite Mini-Lev operation to the candidate-evaluation row and selection that
authorized it.  It makes no adoption, portability, provider, CB Heavy, or
release claim.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from collections.abc import Mapping
from typing import Any

from .cb_light_domain import canonical_json, sha256_bytes
from .cb_light_state import StateError, append_only_transaction


STATE_SCHEMA = "constraintbox.cb-light-mini-lev-state.v1"
SUCCESS = "MINILEV_BRIDGE_EVALUATED_LOCAL"

_TABLE = "mini_lev_bridge_attempt_v1"
_TABLE_COLUMNS = frozenset(
    {
        "attempt_id",
        "captured_at",
        "bridge_request_id",
        "candidate_operation_id",
        "request_sha256",
        "schema_sha256",
        "source_sha256",
        "selection_id",
        "topology_sha256",
        "cohort_sha256",
        "result_sha256",
        "result_json",
        "disposition",
        "claim_ceiling",
    }
)
_UPDATE_TRIGGER = f"{_TABLE}_no_update"
_DELETE_TRIGGER = f"{_TABLE}_no_delete"

_CREATE = (
    f"""
    CREATE TABLE IF NOT EXISTS {_TABLE} (
        attempt_id TEXT PRIMARY KEY,
        captured_at TEXT NOT NULL,
        bridge_request_id TEXT NOT NULL UNIQUE,
        candidate_operation_id TEXT NOT NULL
            REFERENCES candidate_evaluation(operation_id),
        request_sha256 TEXT NOT NULL,
        schema_sha256 TEXT NOT NULL,
        source_sha256 TEXT NOT NULL,
        selection_id TEXT NOT NULL REFERENCES selection_run(selection_id),
        topology_sha256 TEXT NOT NULL,
        cohort_sha256 TEXT NOT NULL,
        result_sha256 TEXT NOT NULL,
        result_json TEXT NOT NULL,
        disposition TEXT NOT NULL CHECK (disposition = '{SUCCESS}'),
        claim_ceiling TEXT NOT NULL
    )
    """,
    f"""
    CREATE INDEX IF NOT EXISTS {_TABLE}_candidate_operation_idx
    ON {_TABLE}(candidate_operation_id, captured_at)
    """,
    f"""
    CREATE TRIGGER IF NOT EXISTS {_UPDATE_TRIGGER}
    BEFORE UPDATE ON {_TABLE}
    BEGIN
        SELECT RAISE(ABORT, '{_TABLE} is append-only');
    END
    """,
    f"""
    CREATE TRIGGER IF NOT EXISTS {_DELETE_TRIGGER}
    BEFORE DELETE ON {_TABLE}
    BEGIN
        SELECT RAISE(ABORT, '{_TABLE} is append-only');
    END
    """,
)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _canonical_text(value: Any) -> str:
    try:
        return canonical_json(value).decode("utf-8")
    except (TypeError, ValueError) as exc:
        raise StateError("Mini-Lev evidence is not canonical JSON") from exc


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise StateError(f"Mini-Lev {label} must be a nonempty string")
    return value


def _require_sha256(value: Any, label: str) -> str:
    text = _require_text(value, label)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise StateError(f"Mini-Lev {label} must be a lowercase SHA-256 digest")
    return text


def _normalized_trigger_sql(trigger: str, operation: str) -> str:
    expected = f"""
    CREATE TRIGGER {trigger}
    BEFORE {operation} ON {_TABLE}
    BEGIN
        SELECT RAISE(ABORT, '{_TABLE} is append-only');
    END
    """
    return " ".join(expected.upper().split())


def _assert_schema(connection: sqlite3.Connection) -> None:
    rows = connection.execute(f"PRAGMA table_info({_TABLE})").fetchall()
    columns = {str(row["name"]) for row in rows}
    if not _TABLE_COLUMNS.issubset(columns):
        raise StateError("CB Light Mini-Lev attempt table is missing required columns")

    foreign_keys = connection.execute(f"PRAGMA foreign_key_list({_TABLE})").fetchall()
    expected_foreign_keys = {
        ("candidate_operation_id", "candidate_evaluation"),
        ("selection_id", "selection_run"),
    }
    actual_foreign_keys = {
        (str(row["from"]), str(row["table"])) for row in foreign_keys
    }
    if not expected_foreign_keys.issubset(actual_foreign_keys):
        raise StateError("CB Light Mini-Lev attempt table is missing required foreign keys")

    for trigger, operation in ((_UPDATE_TRIGGER, "UPDATE"), (_DELETE_TRIGGER, "DELETE")):
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?",
            (trigger,),
        ).fetchone()
        sql = (
            " ".join(str(row["sql"] or "").upper().split())
            if row is not None
            else ""
        )
        if sql != _normalized_trigger_sql(trigger, operation):
            raise StateError(f"CB Light Mini-Lev immutable trigger is missing: {trigger}")


def initialize(connection: sqlite3.Connection) -> None:
    """Create and validate the narrow companion table on a CB Light DB."""

    with append_only_transaction(connection):
        for statement in _CREATE:
            connection.execute(statement)
        _assert_schema(connection)


def _identity_material(
    *,
    bridge_request_id: str,
    candidate_operation_id: str,
    request_sha256: str,
    schema_sha256: str,
    source_sha256: str,
    selection_id: str,
    topology_sha256: str,
    cohort_sha256: str,
    result_sha256: str,
    claim_ceiling: str,
) -> dict[str, str]:
    return {
        "schema": STATE_SCHEMA,
        "bridge_request_id": bridge_request_id,
        "candidate_operation_id": candidate_operation_id,
        "request_sha256": request_sha256,
        "schema_sha256": schema_sha256,
        "source_sha256": source_sha256,
        "selection_id": selection_id,
        "topology_sha256": topology_sha256,
        "cohort_sha256": cohort_sha256,
        "result_sha256": result_sha256,
        "disposition": SUCCESS,
        "claim_ceiling": claim_ceiling,
    }


def record_attempt(
    connection: sqlite3.Connection,
    *,
    bridge_request_id: str,
    candidate_operation_id: str,
    request_sha256: str,
    schema_sha256: str,
    source_sha256: str,
    selection_id: str,
    topology_sha256: str,
    cohort_sha256: str,
    result: Mapping[str, Any],
    claim_ceiling: str,
) -> dict[str, str]:
    """Append or exactly replay one local Mini-Lev attempt.

    The bridge request id is a user-visible idempotency key.  Reusing it with
    any changed bound material refuses before a mutation rather than rewriting
    the old receipt.
    """

    initialize(connection)
    bridge_request_id = _require_text(bridge_request_id, "bridge request id")
    candidate_operation_id = _require_sha256(
        candidate_operation_id, "candidate operation id"
    )
    request_sha256 = _require_sha256(request_sha256, "request digest")
    schema_sha256 = _require_sha256(schema_sha256, "schema digest")
    source_sha256 = _require_sha256(source_sha256, "source digest")
    selection_id = _require_sha256(selection_id, "selection id")
    topology_sha256 = _require_sha256(topology_sha256, "topology digest")
    cohort_sha256 = _require_sha256(cohort_sha256, "cohort digest")
    claim_ceiling = _require_text(claim_ceiling, "claim ceiling")
    result_json = _canonical_text(dict(result))
    result_sha256 = sha256_bytes(result_json.encode("utf-8"))
    identity = _identity_material(
        bridge_request_id=bridge_request_id,
        candidate_operation_id=candidate_operation_id,
        request_sha256=request_sha256,
        schema_sha256=schema_sha256,
        source_sha256=source_sha256,
        selection_id=selection_id,
        topology_sha256=topology_sha256,
        cohort_sha256=cohort_sha256,
        result_sha256=result_sha256,
        claim_ceiling=claim_ceiling,
    )
    attempt_id = sha256_bytes(canonical_json(identity))
    expected = {
        "attempt_id": attempt_id,
        "bridge_request_id": bridge_request_id,
        "candidate_operation_id": candidate_operation_id,
        "request_sha256": request_sha256,
        "schema_sha256": schema_sha256,
        "source_sha256": source_sha256,
        "selection_id": selection_id,
        "topology_sha256": topology_sha256,
        "cohort_sha256": cohort_sha256,
        "result_sha256": result_sha256,
        "result_json": result_json,
        "disposition": SUCCESS,
        "claim_ceiling": claim_ceiling,
    }

    with append_only_transaction(connection):
        existing = connection.execute(
            f"SELECT attempt_id, bridge_request_id, candidate_operation_id, "
            "request_sha256, schema_sha256, source_sha256, selection_id, "
            "topology_sha256, cohort_sha256, result_sha256, result_json, "
            "disposition, claim_ceiling "
            f"FROM {_TABLE} WHERE bridge_request_id = ?",
            (bridge_request_id,),
        ).fetchone()
        if existing is not None:
            for key, value in expected.items():
                if str(existing[key]) != value:
                    raise StateError(
                        "Mini-Lev bridge_request_id already exists with different bound evidence"
                    )
            return {"attempt_id": attempt_id, "result_sha256": result_sha256}

        connection.execute(
            f"""
            INSERT INTO {_TABLE}(
                attempt_id, captured_at, bridge_request_id, candidate_operation_id,
                request_sha256, schema_sha256, source_sha256, selection_id,
                topology_sha256, cohort_sha256, result_sha256, result_json,
                disposition, claim_ceiling
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                _now(),
                bridge_request_id,
                candidate_operation_id,
                request_sha256,
                schema_sha256,
                source_sha256,
                selection_id,
                topology_sha256,
                cohort_sha256,
                result_sha256,
                result_json,
                SUCCESS,
                claim_ceiling,
            ),
        )
    return {"attempt_id": attempt_id, "result_sha256": result_sha256}
