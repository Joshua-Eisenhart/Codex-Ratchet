"""Append-only SQLite evidence ledger for contained CB Light fixture waves.

This module deliberately persists the management-plane facts of a wave rather
than interpreting them.  A plan fingerprint can recur across attempts; an
attempt identity is a fresh append-only nonce.  Artifacts and binding assertions
are content addressed, and a settlement freezes the binding set that a
deterministic gate actually inspected.

No provider, network, PydanticAI, or CB Heavy dependency is imported here.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
import uuid
from collections.abc import Mapping
from typing import Any

from .cb_light_domain import canonical_json, sha256_bytes
from .cb_light_state import StateError, append_only_transaction


WAVE_SCHEMA = "constraintbox.cb-light-wave-state.v1"
WAVE_SCHEMA_VERSION = 1
BINDING_STATES = frozenset(
    {"declared", "bound_reference", "invoked", "receipt_verified"}
)
SETTLEMENT_OUTCOMES = frozenset({"SETTLED", "HOLD", "REFUSE", "EXPIRED"})


_TABLE_COLUMNS: dict[str, frozenset[str]] = {
    "cb_light_wave_artifact": frozenset(
        {
            "artifact_sha256",
            "captured_at",
            "artifact_kind",
            "content_json",
            "claim_ceiling",
        }
    ),
    "cb_light_wave_attempt": frozenset(
        {
            "attempt_id",
            "captured_at",
            "plan_fingerprint",
            "parent_attempt_id",
            "topology_artifact_sha256",
            "input_artifact_sha256",
            "fixture_mode",
            "claim_ceiling",
        }
    ),
    "cb_light_wave_asset_binding": frozenset(
        {
            "binding_id",
            "captured_at",
            "attempt_id",
            "council_id",
            "member_id",
            "asset_id",
            "purpose",
            "binding_state",
            "fixture_mode",
            "asset_artifact_sha256",
            "reference_artifact_sha256",
            "invocation_artifact_sha256",
            "receipt_artifact_sha256",
            "claim_ceiling",
        }
    ),
    "cb_light_wave_settlement": frozenset(
        {
            "settlement_id",
            "captured_at",
            "attempt_id",
            "outcome",
            "reason_code",
            "gate_artifact_sha256",
            "receipt_artifact_sha256",
            "binding_set_sha256",
            "claim_ceiling",
        }
    ),
}

_FOREIGN_KEYS = (
    ("cb_light_wave_attempt", "parent_attempt_id", "cb_light_wave_attempt"),
    ("cb_light_wave_attempt", "topology_artifact_sha256", "cb_light_wave_artifact"),
    ("cb_light_wave_attempt", "input_artifact_sha256", "cb_light_wave_artifact"),
    ("cb_light_wave_asset_binding", "attempt_id", "cb_light_wave_attempt"),
    (
        "cb_light_wave_asset_binding",
        "asset_artifact_sha256",
        "cb_light_wave_artifact",
    ),
    (
        "cb_light_wave_asset_binding",
        "reference_artifact_sha256",
        "cb_light_wave_artifact",
    ),
    (
        "cb_light_wave_asset_binding",
        "invocation_artifact_sha256",
        "cb_light_wave_artifact",
    ),
    (
        "cb_light_wave_asset_binding",
        "receipt_artifact_sha256",
        "cb_light_wave_artifact",
    ),
    ("cb_light_wave_settlement", "attempt_id", "cb_light_wave_attempt"),
    (
        "cb_light_wave_settlement",
        "gate_artifact_sha256",
        "cb_light_wave_artifact",
    ),
    (
        "cb_light_wave_settlement",
        "receipt_artifact_sha256",
        "cb_light_wave_artifact",
    ),
)

_TRIGGER_SPECS = tuple(
    (f"{table}_{suffix}", table, operation)
    for table in _TABLE_COLUMNS
    for suffix, operation in (("no_update", "UPDATE"), ("no_delete", "DELETE"))
)

_BINDING_ATTEMPT_MODE_GUARD = "cb_light_wave_binding_fixture_mode_guard"

_CREATE_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS cb_light_wave_artifact (
        artifact_sha256 TEXT PRIMARY KEY,
        captured_at TEXT NOT NULL,
        artifact_kind TEXT NOT NULL,
        content_json TEXT NOT NULL,
        claim_ceiling TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cb_light_wave_attempt (
        attempt_id TEXT PRIMARY KEY,
        captured_at TEXT NOT NULL,
        plan_fingerprint TEXT NOT NULL,
        parent_attempt_id TEXT REFERENCES cb_light_wave_attempt(attempt_id),
        topology_artifact_sha256 TEXT NOT NULL
            REFERENCES cb_light_wave_artifact(artifact_sha256),
        input_artifact_sha256 TEXT NOT NULL
            REFERENCES cb_light_wave_artifact(artifact_sha256),
        fixture_mode INTEGER NOT NULL CHECK (fixture_mode IN (0, 1)),
        claim_ceiling TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cb_light_wave_asset_binding (
        binding_id TEXT PRIMARY KEY,
        captured_at TEXT NOT NULL,
        attempt_id TEXT NOT NULL REFERENCES cb_light_wave_attempt(attempt_id),
        council_id TEXT NOT NULL,
        member_id TEXT NOT NULL,
        asset_id TEXT NOT NULL,
        purpose TEXT NOT NULL,
        binding_state TEXT NOT NULL CHECK (
            binding_state IN (
                'declared', 'bound_reference', 'invoked', 'receipt_verified'
            )
        ),
        fixture_mode INTEGER NOT NULL CHECK (fixture_mode IN (0, 1)),
        asset_artifact_sha256 TEXT NOT NULL
            REFERENCES cb_light_wave_artifact(artifact_sha256),
        reference_artifact_sha256 TEXT
            REFERENCES cb_light_wave_artifact(artifact_sha256),
        invocation_artifact_sha256 TEXT
            REFERENCES cb_light_wave_artifact(artifact_sha256),
        receipt_artifact_sha256 TEXT
            REFERENCES cb_light_wave_artifact(artifact_sha256),
        claim_ceiling TEXT NOT NULL,
        CHECK (
            (binding_state = 'declared'
                AND reference_artifact_sha256 IS NULL
                AND invocation_artifact_sha256 IS NULL
                AND receipt_artifact_sha256 IS NULL)
            OR
            (binding_state = 'bound_reference'
                AND reference_artifact_sha256 IS NOT NULL
                AND invocation_artifact_sha256 IS NULL
                AND receipt_artifact_sha256 IS NULL)
            OR
            (binding_state = 'invoked'
                AND reference_artifact_sha256 IS NOT NULL
                AND invocation_artifact_sha256 IS NOT NULL
                AND receipt_artifact_sha256 IS NULL)
            OR
            (binding_state = 'receipt_verified'
                AND reference_artifact_sha256 IS NOT NULL
                AND invocation_artifact_sha256 IS NOT NULL
                AND receipt_artifact_sha256 IS NOT NULL)
        ),
        CHECK (
            fixture_mode = 0
            OR binding_state IN ('declared', 'bound_reference')
        )
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cb_light_wave_settlement (
        settlement_id TEXT PRIMARY KEY,
        captured_at TEXT NOT NULL,
        attempt_id TEXT NOT NULL UNIQUE REFERENCES cb_light_wave_attempt(attempt_id),
        outcome TEXT NOT NULL CHECK (
            outcome IN ('SETTLED', 'HOLD', 'REFUSE', 'EXPIRED')
        ),
        reason_code TEXT NOT NULL,
        gate_artifact_sha256 TEXT NOT NULL
            REFERENCES cb_light_wave_artifact(artifact_sha256),
        receipt_artifact_sha256 TEXT NOT NULL
            REFERENCES cb_light_wave_artifact(artifact_sha256),
        binding_set_sha256 TEXT NOT NULL,
        claim_ceiling TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS cb_light_wave_attempt_plan_fingerprint_idx
    ON cb_light_wave_attempt(plan_fingerprint, captured_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS cb_light_wave_binding_attempt_idx
    ON cb_light_wave_asset_binding(attempt_id, council_id, member_id, asset_id)
    """,
)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _canonical_text(value: Any) -> str:
    try:
        return canonical_json(value).decode("utf-8")
    except (TypeError, ValueError) as exc:
        raise StateError("wave evidence is not canonical JSON") from exc


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise StateError(f"wave {label} must be a nonempty string")
    return value


def _require_sha256(value: Any, label: str) -> str:
    text = _require_text(value, label)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise StateError(f"wave {label} must be a lowercase SHA-256 digest")
    return text


def _require_flag(value: Any, label: str) -> int:
    if not isinstance(value, bool):
        raise StateError(f"wave {label} must be boolean")
    return int(value)


def _trigger_sql(name: str, table: str, operation: str) -> str:
    return f"""
    CREATE TRIGGER IF NOT EXISTS {name}
    BEFORE {operation} ON {table}
    BEGIN
        SELECT RAISE(ABORT, '{table} is append-only');
    END
    """


def _binding_attempt_mode_guard_sql() -> str:
    """Reject a raw binding that lies about its enclosing attempt's mode."""

    return f"""
    CREATE TRIGGER IF NOT EXISTS {_BINDING_ATTEMPT_MODE_GUARD}
    BEFORE INSERT ON cb_light_wave_asset_binding
    BEGIN
        SELECT CASE
            WHEN NOT EXISTS (
                SELECT 1 FROM cb_light_wave_attempt
                WHERE attempt_id = NEW.attempt_id
                AND fixture_mode = NEW.fixture_mode
            ) THEN RAISE(ABORT, 'wave binding fixture mode does not match attempt')
        END;
    END
    """


def _assert_wave_schema(connection: sqlite3.Connection) -> None:
    for table, expected_columns in _TABLE_COLUMNS.items():
        rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
        actual_columns = {str(row["name"]) for row in rows}
        if not expected_columns.issubset(actual_columns):
            raise StateError(f"CB Light wave table is missing required columns: {table}")

    for table, column, referenced_table in _FOREIGN_KEYS:
        rows = connection.execute(f"PRAGMA foreign_key_list({table})").fetchall()
        if not any(
            row["from"] == column and row["table"] == referenced_table
            for row in rows
        ):
            raise StateError(
                "CB Light wave table is missing required foreign key: "
                f"{table}.{column} -> {referenced_table}"
            )

    for name, table, operation in _TRIGGER_SPECS:
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?",
            (name,),
        ).fetchone()
        normalized = str(row["sql"] or "").upper() if row is not None else ""
        expected_clause = f"BEFORE {operation} ON {table}".upper()
        if expected_clause not in normalized or "RAISE(ABORT" not in normalized:
            raise StateError(f"CB Light wave immutable trigger is missing or invalid: {name}")
    guard = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?",
        (_BINDING_ATTEMPT_MODE_GUARD,),
    ).fetchone()
    guard_sql = str(guard["sql"] or "").upper() if guard is not None else ""
    if (
        "BEFORE INSERT ON CB_LIGHT_WAVE_ASSET_BINDING" not in guard_sql
        or "RAISE(ABORT" not in guard_sql
    ):
        raise StateError("CB Light wave binding fixture-mode guard is missing or invalid")


def initialize_wave_state(connection: sqlite3.Connection) -> None:
    """Add the versioned wave tables to the existing CB Light state database.

    ``sqlite3.Connection.executescript`` commits a caller transaction before it
    runs.  Execute each DDL statement inside the public append-only transaction
    helper instead, so schema initialization respects an outer caller
    transaction just like a retained-state writer.
    """

    with append_only_transaction(connection):
        for statement in _CREATE_TABLES:
            connection.execute(statement)
        for name, table, operation in _TRIGGER_SPECS:
            connection.execute(_trigger_sql(name, table, operation))
        connection.execute(_binding_attempt_mode_guard_sql())
        _assert_wave_schema(connection)


def new_wave_attempt_id() -> str:
    """Create a fresh non-content-addressed attempt identity."""

    return f"wave-attempt-{uuid.uuid4().hex}"


def _artifact_envelope(
    *, artifact_kind: str, payload: Any, claim_ceiling: str
) -> dict[str, Any]:
    return {
        "artifact_kind": artifact_kind,
        "payload": payload,
        "claim_ceiling": claim_ceiling,
    }


def artifact_sha256_for(
    *, artifact_kind: str, payload: Any, claim_ceiling: str
) -> str:
    """Return the content address used by :func:`record_artifact`."""

    kind = _require_text(artifact_kind, "artifact kind")
    ceiling = _require_text(claim_ceiling, "artifact claim ceiling")
    return sha256_bytes(
        _canonical_text(
            _artifact_envelope(
                artifact_kind=kind, payload=payload, claim_ceiling=ceiling
            )
        ).encode("utf-8")
    )


def _artifact_row(
    connection: sqlite3.Connection, artifact_sha256: str
) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT artifact_sha256, artifact_kind, content_json, claim_ceiling
        FROM cb_light_wave_artifact WHERE artifact_sha256 = ?
        """,
        (artifact_sha256,),
    ).fetchone()
    if row is None:
        raise StateError(f"CB Light wave artifact is absent: {artifact_sha256}")
    try:
        payload = json.loads(row["content_json"])
    except (TypeError, json.JSONDecodeError) as exc:
        raise StateError("CB Light wave artifact has invalid retained JSON") from exc
    if _canonical_text(payload) != row["content_json"]:
        raise StateError("CB Light wave artifact JSON is not canonical")
    expected = artifact_sha256_for(
        artifact_kind=row["artifact_kind"],
        payload=payload,
        claim_ceiling=row["claim_ceiling"],
    )
    if expected != row["artifact_sha256"]:
        raise StateError("CB Light wave artifact content address mismatch")
    return row


def _require_artifact(connection: sqlite3.Connection, artifact_sha256: Any) -> str:
    digest = _require_sha256(artifact_sha256, "artifact SHA-256")
    _artifact_row(connection, digest)
    return digest


def record_artifact(
    connection: sqlite3.Connection,
    *,
    artifact_kind: str,
    payload: Any,
    claim_ceiling: str,
) -> str:
    """Append or exactly replay a content-addressed wave artifact."""

    initialize_wave_state(connection)
    kind = _require_text(artifact_kind, "artifact kind")
    ceiling = _require_text(claim_ceiling, "artifact claim ceiling")
    content_json = _canonical_text(payload)
    artifact_sha256 = artifact_sha256_for(
        artifact_kind=kind, payload=payload, claim_ceiling=ceiling
    )
    with append_only_transaction(connection):
        existing = connection.execute(
            """
            SELECT artifact_kind, content_json, claim_ceiling
            FROM cb_light_wave_artifact WHERE artifact_sha256 = ?
            """,
            (artifact_sha256,),
        ).fetchone()
        if existing is not None:
            if (
                existing["artifact_kind"],
                existing["content_json"],
                existing["claim_ceiling"],
            ) != (kind, content_json, ceiling):
                raise StateError(
                    "immutable wave artifact identity already exists with different content"
                )
            _artifact_row(connection, artifact_sha256)
            return artifact_sha256
        connection.execute(
            """
            INSERT INTO cb_light_wave_artifact(
                artifact_sha256, captured_at, artifact_kind, content_json,
                claim_ceiling
            ) VALUES(?, ?, ?, ?, ?)
            """,
            (artifact_sha256, _now(), kind, content_json, ceiling),
        )
    return artifact_sha256


def _attempt_values(
    *,
    plan_fingerprint: str,
    parent_attempt_id: str | None,
    topology_artifact_sha256: str,
    input_artifact_sha256: str,
    fixture_mode: int,
    claim_ceiling: str,
) -> tuple[Any, ...]:
    return (
        plan_fingerprint,
        parent_attempt_id,
        topology_artifact_sha256,
        input_artifact_sha256,
        fixture_mode,
        claim_ceiling,
    )


def record_wave_attempt(
    connection: sqlite3.Connection,
    *,
    plan_fingerprint: str,
    topology_artifact_sha256: str,
    input_artifact_sha256: str,
    fixture_mode: bool,
    claim_ceiling: str,
    attempt_id: str | None = None,
    parent_attempt_id: str | None = None,
) -> str:
    """Append one fresh wave attempt, or exactly replay an explicit identity.

    A plan fingerprint intentionally has no uniqueness constraint.  Re-running
    the same plan is a new attempt unless the caller explicitly replays the
    returned ``attempt_id``.
    """

    initialize_wave_state(connection)
    plan = _require_sha256(plan_fingerprint, "plan fingerprint")
    attempt = (
        new_wave_attempt_id()
        if attempt_id is None
        else _require_text(attempt_id, "attempt ID")
    )
    parent = (
        _require_text(parent_attempt_id, "parent attempt ID")
        if parent_attempt_id is not None
        else None
    )
    if parent == attempt:
        raise StateError("wave attempt cannot be its own parent")
    topology = _require_artifact(connection, topology_artifact_sha256)
    wave_input = _require_artifact(connection, input_artifact_sha256)
    fixture = _require_flag(fixture_mode, "fixture mode")
    ceiling = _require_text(claim_ceiling, "attempt claim ceiling")
    with append_only_transaction(connection):
        if parent is not None:
            parent_row = connection.execute(
                "SELECT attempt_id FROM cb_light_wave_attempt WHERE attempt_id = ?",
                (parent,),
            ).fetchone()
            if parent_row is None:
                raise StateError("wave parent attempt is absent")
        expected = _attempt_values(
            plan_fingerprint=plan,
            parent_attempt_id=parent,
            topology_artifact_sha256=topology,
            input_artifact_sha256=wave_input,
            fixture_mode=fixture,
            claim_ceiling=ceiling,
        )
        existing = connection.execute(
            """
            SELECT plan_fingerprint, parent_attempt_id, topology_artifact_sha256,
                   input_artifact_sha256, fixture_mode, claim_ceiling
            FROM cb_light_wave_attempt WHERE attempt_id = ?
            """,
            (attempt,),
        ).fetchone()
        if existing is not None:
            actual = tuple(existing[column] for column in existing.keys())
            if actual != expected:
                raise StateError(
                    "immutable wave attempt identity already exists with different content"
                )
            return attempt
        connection.execute(
            """
            INSERT INTO cb_light_wave_attempt(
                attempt_id, captured_at, plan_fingerprint, parent_attempt_id,
                topology_artifact_sha256, input_artifact_sha256, fixture_mode,
                claim_ceiling
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (attempt, _now(), *expected),
        )
    return attempt


def _binding_envelope(
    *,
    attempt_id: str,
    council_id: str,
    member_id: str,
    asset_id: str,
    purpose: str,
    binding_state: str,
    fixture_mode: int,
    asset_artifact_sha256: str,
    reference_artifact_sha256: str | None,
    invocation_artifact_sha256: str | None,
    receipt_artifact_sha256: str | None,
    claim_ceiling: str,
) -> dict[str, Any]:
    return {
        "attempt_id": attempt_id,
        "council_id": council_id,
        "member_id": member_id,
        "asset_id": asset_id,
        "purpose": purpose,
        "binding_state": binding_state,
        "fixture_mode": bool(fixture_mode),
        "asset_artifact_sha256": asset_artifact_sha256,
        "reference_artifact_sha256": reference_artifact_sha256,
        "invocation_artifact_sha256": invocation_artifact_sha256,
        "receipt_artifact_sha256": receipt_artifact_sha256,
        "claim_ceiling": claim_ceiling,
    }


def _binding_id(**kwargs: Any) -> str:
    return sha256_bytes(canonical_json(_binding_envelope(**kwargs)))


def _validate_binding_state(
    *,
    binding_state: str,
    fixture_mode: int,
    reference_artifact_sha256: str | None,
    invocation_artifact_sha256: str | None,
    receipt_artifact_sha256: str | None,
) -> None:
    if binding_state not in BINDING_STATES:
        raise StateError(f"unexpected CB Light wave binding state: {binding_state}")
    if fixture_mode and binding_state in {"invoked", "receipt_verified"}:
        raise StateError(
            "fixture wave bindings cannot claim invoked or receipt_verified state"
        )
    expected = {
        "declared": (False, False, False),
        "bound_reference": (True, False, False),
        "invoked": (True, True, False),
        "receipt_verified": (True, True, True),
    }[binding_state]
    actual = (
        reference_artifact_sha256 is not None,
        invocation_artifact_sha256 is not None,
        receipt_artifact_sha256 is not None,
    )
    if actual != expected:
        raise StateError(
            "wave binding evidence fields do not match its asserted binding state"
        )


def _optional_artifact(
    connection: sqlite3.Connection, artifact_sha256: str | None
) -> str | None:
    if artifact_sha256 is None:
        return None
    return _require_artifact(connection, artifact_sha256)


def record_asset_binding(
    connection: sqlite3.Connection,
    *,
    attempt_id: str,
    council_id: str,
    member_id: str,
    asset_id: str,
    purpose: str,
    binding_state: str,
    fixture_mode: bool,
    asset_artifact_sha256: str,
    claim_ceiling: str,
    reference_artifact_sha256: str | None = None,
    invocation_artifact_sha256: str | None = None,
    receipt_artifact_sha256: str | None = None,
) -> str:
    """Append one many-to-many council/member/asset binding assertion.

    Binding records are assertions, not mutable lifecycle rows.  A later,
    better-evidenced binding has a different content address.  Fixture bindings
    can only be ``declared`` or ``bound_reference`` and cannot impersonate an
    invocation or verified receipt.
    """

    initialize_wave_state(connection)
    attempt = _require_text(attempt_id, "attempt ID")
    council = _require_text(council_id, "council ID")
    member = _require_text(member_id, "member ID")
    asset = _require_text(asset_id, "asset ID")
    binding_purpose = _require_text(purpose, "binding purpose")
    state = _require_text(binding_state, "binding state")
    fixture = _require_flag(fixture_mode, "fixture mode")
    asset_artifact = _require_artifact(connection, asset_artifact_sha256)
    reference_artifact = _optional_artifact(connection, reference_artifact_sha256)
    invocation_artifact = _optional_artifact(connection, invocation_artifact_sha256)
    receipt_artifact = _optional_artifact(connection, receipt_artifact_sha256)
    ceiling = _require_text(claim_ceiling, "binding claim ceiling")
    _validate_binding_state(
        binding_state=state,
        fixture_mode=fixture,
        reference_artifact_sha256=reference_artifact,
        invocation_artifact_sha256=invocation_artifact,
        receipt_artifact_sha256=receipt_artifact,
    )
    binding_id = _binding_id(
        attempt_id=attempt,
        council_id=council,
        member_id=member,
        asset_id=asset,
        purpose=binding_purpose,
        binding_state=state,
        fixture_mode=fixture,
        asset_artifact_sha256=asset_artifact,
        reference_artifact_sha256=reference_artifact,
        invocation_artifact_sha256=invocation_artifact,
        receipt_artifact_sha256=receipt_artifact,
        claim_ceiling=ceiling,
    )
    expected = (
        attempt,
        council,
        member,
        asset,
        binding_purpose,
        state,
        fixture,
        asset_artifact,
        reference_artifact,
        invocation_artifact,
        receipt_artifact,
        ceiling,
    )
    with append_only_transaction(connection):
        attempt_row = connection.execute(
            "SELECT fixture_mode FROM cb_light_wave_attempt WHERE attempt_id = ?",
            (attempt,),
        ).fetchone()
        if attempt_row is None:
            raise StateError("wave binding attempt is absent")
        if int(attempt_row["fixture_mode"]) != fixture:
            raise StateError("wave binding fixture mode does not match its attempt")
        existing = connection.execute(
            """
            SELECT attempt_id, council_id, member_id, asset_id, purpose,
                   binding_state, fixture_mode, asset_artifact_sha256,
                   reference_artifact_sha256, invocation_artifact_sha256,
                   receipt_artifact_sha256, claim_ceiling
            FROM cb_light_wave_asset_binding WHERE binding_id = ?
            """,
            (binding_id,),
        ).fetchone()
        if existing is not None:
            actual = tuple(existing[column] for column in existing.keys())
            if actual != expected:
                raise StateError(
                    "immutable wave binding identity already exists with different content"
                )
            return binding_id
        settlement = connection.execute(
            "SELECT settlement_id FROM cb_light_wave_settlement WHERE attempt_id = ?",
            (attempt,),
        ).fetchone()
        if settlement is not None:
            raise StateError("wave settlement already freezes this attempt's binding set")
        connection.execute(
            """
            INSERT INTO cb_light_wave_asset_binding(
                binding_id, captured_at, attempt_id, council_id, member_id,
                asset_id, purpose, binding_state, fixture_mode,
                asset_artifact_sha256, reference_artifact_sha256,
                invocation_artifact_sha256, receipt_artifact_sha256,
                claim_ceiling
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (binding_id, _now(), *expected),
        )
    return binding_id


def _binding_ids(connection: sqlite3.Connection, attempt_id: str) -> list[str]:
    rows = connection.execute(
        """
        SELECT binding_id FROM cb_light_wave_asset_binding
        WHERE attempt_id = ? ORDER BY binding_id
        """,
        (attempt_id,),
    ).fetchall()
    return [str(row["binding_id"]) for row in rows]


def _binding_set_sha256(binding_ids: list[str]) -> str:
    if not binding_ids:
        raise StateError("wave settlement requires at least one asset binding")
    return sha256_bytes(canonical_json(binding_ids))


def _settlement_envelope(
    *,
    attempt_id: str,
    outcome: str,
    reason_code: str,
    gate_artifact_sha256: str,
    receipt_artifact_sha256: str,
    binding_set_sha256: str,
    claim_ceiling: str,
) -> dict[str, str]:
    return {
        "attempt_id": attempt_id,
        "outcome": outcome,
        "reason_code": reason_code,
        "gate_artifact_sha256": gate_artifact_sha256,
        "receipt_artifact_sha256": receipt_artifact_sha256,
        "binding_set_sha256": binding_set_sha256,
        "claim_ceiling": claim_ceiling,
    }


def _settlement_id(**kwargs: str) -> str:
    return sha256_bytes(canonical_json(_settlement_envelope(**kwargs)))


def record_wave_settlement(
    connection: sqlite3.Connection,
    *,
    attempt_id: str,
    outcome: str,
    reason_code: str,
    gate_artifact_sha256: str,
    receipt_artifact_sha256: str,
    claim_ceiling: str,
) -> str:
    """Freeze a deterministic gate outcome and the exact bound asset set."""

    initialize_wave_state(connection)
    attempt = _require_text(attempt_id, "attempt ID")
    settlement_outcome = _require_text(outcome, "settlement outcome")
    if settlement_outcome not in SETTLEMENT_OUTCOMES:
        raise StateError(f"unexpected CB Light wave settlement outcome: {outcome}")
    reason = _require_text(reason_code, "settlement reason code")
    gate_artifact = _require_artifact(connection, gate_artifact_sha256)
    receipt_artifact = _require_artifact(connection, receipt_artifact_sha256)
    ceiling = _require_text(claim_ceiling, "settlement claim ceiling")
    with append_only_transaction(connection):
        attempt_row = connection.execute(
            "SELECT attempt_id FROM cb_light_wave_attempt WHERE attempt_id = ?",
            (attempt,),
        ).fetchone()
        if attempt_row is None:
            raise StateError("wave settlement attempt is absent")
        binding_set = _binding_set_sha256(_binding_ids(connection, attempt))
        expected = _settlement_envelope(
            attempt_id=attempt,
            outcome=settlement_outcome,
            reason_code=reason,
            gate_artifact_sha256=gate_artifact,
            receipt_artifact_sha256=receipt_artifact,
            binding_set_sha256=binding_set,
            claim_ceiling=ceiling,
        )
        settlement_id = _settlement_id(**expected)
        existing = connection.execute(
            """
            SELECT settlement_id, outcome, reason_code, gate_artifact_sha256,
                   receipt_artifact_sha256, binding_set_sha256, claim_ceiling
            FROM cb_light_wave_settlement WHERE attempt_id = ?
            """,
            (attempt,),
        ).fetchone()
        if existing is not None:
            actual = {
                "attempt_id": attempt,
                "outcome": existing["outcome"],
                "reason_code": existing["reason_code"],
                "gate_artifact_sha256": existing["gate_artifact_sha256"],
                "receipt_artifact_sha256": existing["receipt_artifact_sha256"],
                "binding_set_sha256": existing["binding_set_sha256"],
                "claim_ceiling": existing["claim_ceiling"],
            }
            if actual != expected or existing["settlement_id"] != settlement_id:
                raise StateError(
                    "wave attempt already has a different immutable settlement"
                )
            return str(existing["settlement_id"])
        connection.execute(
            """
            INSERT INTO cb_light_wave_settlement(
                settlement_id, captured_at, attempt_id, outcome, reason_code,
                gate_artifact_sha256, receipt_artifact_sha256,
                binding_set_sha256, claim_ceiling
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                settlement_id,
                _now(),
                attempt,
                settlement_outcome,
                reason,
                gate_artifact,
                receipt_artifact,
                binding_set,
                ceiling,
            ),
        )
    return settlement_id


def _verify_binding(connection: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    binding_state = _require_text(row["binding_state"], "binding state")
    fixture_mode = int(row["fixture_mode"])
    if fixture_mode not in (0, 1):
        raise StateError("wave binding has invalid fixture mode")
    _validate_binding_state(
        binding_state=binding_state,
        fixture_mode=fixture_mode,
        reference_artifact_sha256=row["reference_artifact_sha256"],
        invocation_artifact_sha256=row["invocation_artifact_sha256"],
        receipt_artifact_sha256=row["receipt_artifact_sha256"],
    )
    for column in (
        "asset_artifact_sha256",
        "reference_artifact_sha256",
        "invocation_artifact_sha256",
        "receipt_artifact_sha256",
    ):
        artifact = row[column]
        if artifact is not None:
            _artifact_row(connection, _require_sha256(artifact, column))
    expected_id = _binding_id(
        attempt_id=row["attempt_id"],
        council_id=row["council_id"],
        member_id=row["member_id"],
        asset_id=row["asset_id"],
        purpose=row["purpose"],
        binding_state=binding_state,
        fixture_mode=fixture_mode,
        asset_artifact_sha256=row["asset_artifact_sha256"],
        reference_artifact_sha256=row["reference_artifact_sha256"],
        invocation_artifact_sha256=row["invocation_artifact_sha256"],
        receipt_artifact_sha256=row["receipt_artifact_sha256"],
        claim_ceiling=row["claim_ceiling"],
    )
    if expected_id != row["binding_id"]:
        raise StateError("CB Light wave binding content address mismatch")
    return dict(row)


def _verify_settlement(
    connection: sqlite3.Connection, attempt_id: str, row: sqlite3.Row, binding_ids: list[str]
) -> dict[str, Any]:
    outcome = _require_text(row["outcome"], "settlement outcome")
    if outcome not in SETTLEMENT_OUTCOMES:
        raise StateError("CB Light wave settlement has invalid outcome")
    expected_binding_set = _binding_set_sha256(binding_ids)
    if row["binding_set_sha256"] != expected_binding_set:
        raise StateError("CB Light wave settlement binding set has drifted")
    gate = _require_artifact(connection, row["gate_artifact_sha256"])
    receipt = _require_artifact(connection, row["receipt_artifact_sha256"])
    expected = _settlement_envelope(
        attempt_id=attempt_id,
        outcome=outcome,
        reason_code=row["reason_code"],
        gate_artifact_sha256=gate,
        receipt_artifact_sha256=receipt,
        binding_set_sha256=expected_binding_set,
        claim_ceiling=row["claim_ceiling"],
    )
    if _settlement_id(**expected) != row["settlement_id"]:
        raise StateError("CB Light wave settlement content address mismatch")
    return dict(row)


def load_wave_attempt(
    connection: sqlite3.Connection, attempt_id: str
) -> dict[str, Any]:
    """Load one wave attempt only after rechecking retained integrity.

    The verifier intentionally does not create or repair schema.  A missing
    trigger, altered artifact, forged binding, or settlement/binding mismatch is
    a refusal, not a quietly repaired ledger.
    """

    _assert_wave_schema(connection)
    attempt = _require_text(attempt_id, "attempt ID")
    row = connection.execute(
        """
        SELECT attempt_id, captured_at, plan_fingerprint, parent_attempt_id,
               topology_artifact_sha256, input_artifact_sha256, fixture_mode,
               claim_ceiling
        FROM cb_light_wave_attempt WHERE attempt_id = ?
        """,
        (attempt,),
    ).fetchone()
    if row is None:
        raise StateError("CB Light wave attempt is absent")
    if _require_sha256(row["plan_fingerprint"], "plan fingerprint") != row[
        "plan_fingerprint"
    ]:
        raise StateError("CB Light wave attempt plan fingerprint is malformed")
    fixture_mode = int(row["fixture_mode"])
    if fixture_mode not in (0, 1):
        raise StateError("CB Light wave attempt has invalid fixture mode")
    _artifact_row(connection, _require_sha256(row["topology_artifact_sha256"], "topology artifact"))
    _artifact_row(connection, _require_sha256(row["input_artifact_sha256"], "input artifact"))
    if row["parent_attempt_id"] is not None:
        parent = connection.execute(
            "SELECT attempt_id FROM cb_light_wave_attempt WHERE attempt_id = ?",
            (row["parent_attempt_id"],),
        ).fetchone()
        if parent is None or row["parent_attempt_id"] == attempt:
            raise StateError("CB Light wave attempt parent linkage is invalid")

    binding_rows = connection.execute(
        """
        SELECT binding_id, captured_at, attempt_id, council_id, member_id,
               asset_id, purpose, binding_state, fixture_mode,
               asset_artifact_sha256, reference_artifact_sha256,
               invocation_artifact_sha256, receipt_artifact_sha256,
               claim_ceiling
        FROM cb_light_wave_asset_binding
        WHERE attempt_id = ? ORDER BY binding_id
        """,
        (attempt,),
    ).fetchall()
    bindings = []
    for binding_row in binding_rows:
        if int(binding_row["fixture_mode"]) != fixture_mode:
            raise StateError("CB Light wave binding fixture mode differs from attempt")
        bindings.append(_verify_binding(connection, binding_row))
    binding_ids = [str(binding["binding_id"]) for binding in bindings]

    settlements = connection.execute(
        """
        SELECT settlement_id, captured_at, attempt_id, outcome, reason_code,
               gate_artifact_sha256, receipt_artifact_sha256,
               binding_set_sha256, claim_ceiling
        FROM cb_light_wave_settlement WHERE attempt_id = ?
        """,
        (attempt,),
    ).fetchall()
    if len(settlements) > 1:
        raise StateError("CB Light wave attempt has more than one settlement")
    settlement = (
        _verify_settlement(connection, attempt, settlements[0], binding_ids)
        if settlements
        else None
    )
    return {
        "schema": WAVE_SCHEMA,
        "schema_version": WAVE_SCHEMA_VERSION,
        "attempt": dict(row),
        "bindings": bindings,
        "settlement": settlement,
        "claim_ceiling": (
            "local append-only wave state only; no provider, adoption, "
            "or CB Heavy claim"
        ),
    }


def verify_wave_attempt(
    connection: sqlite3.Connection, attempt_id: str
) -> dict[str, Any]:
    """Public verifier alias for future deterministic controllers."""

    return load_wave_attempt(connection, attempt_id)
