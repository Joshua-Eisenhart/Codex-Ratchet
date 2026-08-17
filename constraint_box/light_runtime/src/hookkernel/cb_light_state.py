"""SQLite retained-state spine for CB Light domain, probes, and hook events."""

from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping

from .cb_light_domain import canonical_json, sha256_bytes


SCHEMA_VERSION = 1
REQUIRED_CASE_KINDS = {
    "candidate",
    "install",
    "import",
    "positive",
    "negative",
    "boundary",
    "replay",
    "severance",
    "reference",
}
_CORE_REGISTRY = (
    Path(__file__).with_name("cb_light_data")
    / "config"
    / "core_tool_registry_v9.json"
)


class StateError(RuntimeError):
    """A retained-state write or validation failed closed."""


def _expected_core_contract_ids() -> tuple[str, ...]:
    """Read the contained registry instead of retaining a stale tool count."""

    try:
        body = json.loads(_CORE_REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StateError(
            f"cannot read contained CB Light core registry: {_CORE_REGISTRY}"
        ) from exc
    rows = body.get("tools") if isinstance(body, dict) else None
    if not isinstance(rows, list):
        raise StateError("contained CB Light core registry has no tools list")
    ids = tuple(row.get("id") for row in rows if isinstance(row, dict))
    if (
        not ids
        or len(ids) != len(rows)
        or any(not isinstance(contract_id, str) or not contract_id for contract_id in ids)
        or len(ids) != len(set(ids))
    ):
        raise StateError("contained CB Light core registry has invalid tool IDs")
    return ids


def default_db_path() -> Path:
    override = os.environ.get("CB_LIGHT_STATE_DB")
    if override:
        return Path(override).expanduser().resolve()
    return (
        Path.home()
        / ".local"
        / "share"
        / "codex-ratchet"
        / "state"
        / "cb-light-v1.sqlite3"
    )


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def connect(path: Path | None = None) -> sqlite3.Connection:
    target = (path or default_db_path()).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target, timeout=10.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = FULL")
    initialize(connection)
    return connection


def connect_readonly(path: Path | None = None) -> sqlite3.Connection:
    target = (path or default_db_path()).resolve()
    if not target.is_file():
        raise StateError(f"CB Light state database does not exist: {target}")
    connection = sqlite3.connect(
        f"file:{target}?mode=ro&immutable=1", uri=True, timeout=10.0
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    current = connection.execute(
        "SELECT value FROM state_meta WHERE key = 'schema_version'"
    ).fetchone()
    if current is None or int(current["value"]) != SCHEMA_VERSION:
        connection.close()
        raise StateError("unsupported or missing CB Light state schema")
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS state_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS domain_snapshot (
            snapshot_id TEXT PRIMARY KEY,
            captured_at TEXT NOT NULL,
            profile TEXT NOT NULL CHECK (profile = 'cb_light'),
            domain_sha256 TEXT NOT NULL,
            source_manifest_sha256 TEXT NOT NULL,
            observation_sha256 TEXT NOT NULL,
            completeness TEXT NOT NULL,
            counts_json TEXT NOT NULL,
            environment_json TEXT NOT NULL,
            claim_ceiling TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS domain_candidate (
            snapshot_id TEXT NOT NULL REFERENCES domain_snapshot(snapshot_id),
            candidate_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            row_json TEXT NOT NULL,
            PRIMARY KEY (snapshot_id, candidate_id)
        );

        CREATE TABLE IF NOT EXISTS probe_run (
            run_id TEXT PRIMARY KEY,
            captured_at TEXT NOT NULL,
            interpreter TEXT NOT NULL,
            python_version TEXT NOT NULL,
            contract_set_sha256 TEXT NOT NULL,
            source_set_sha256 TEXT NOT NULL,
            evidence_set_sha256 TEXT NOT NULL,
            all_contracts_satisfied INTEGER NOT NULL CHECK (all_contracts_satisfied IN (0, 1)),
            claim_ceiling TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS probe_case (
            run_id TEXT NOT NULL REFERENCES probe_run(run_id),
            contract_id TEXT NOT NULL,
            distribution TEXT NOT NULL,
            case_kind TEXT NOT NULL,
            passed INTEGER NOT NULL CHECK (passed IN (0, 1)),
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, contract_id, case_kind)
        );

        CREATE TABLE IF NOT EXISTS tool_decision (
            run_id TEXT NOT NULL REFERENCES probe_run(run_id),
            contract_id TEXT NOT NULL,
            distribution TEXT NOT NULL,
            disposition TEXT NOT NULL,
            reason_code TEXT NOT NULL,
            facts_json TEXT NOT NULL,
            decision_json TEXT NOT NULL,
            PRIMARY KEY (run_id, contract_id)
        );

        CREATE TABLE IF NOT EXISTS selection_run (
            selection_id TEXT PRIMARY KEY,
            captured_at TEXT NOT NULL,
            snapshot_id TEXT NOT NULL REFERENCES domain_snapshot(snapshot_id),
            probe_run_id TEXT REFERENCES probe_run(run_id),
            domain_sha256 TEXT NOT NULL,
            counts_json TEXT NOT NULL,
            owner_approved_adoptions INTEGER NOT NULL,
            claim_ceiling TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS selection_decision (
            selection_id TEXT NOT NULL REFERENCES selection_run(selection_id),
            candidate_id TEXT NOT NULL,
            disposition TEXT NOT NULL,
            reason_code TEXT NOT NULL,
            decision_json TEXT NOT NULL,
            PRIMARY KEY (selection_id, candidate_id)
        );

        CREATE TABLE IF NOT EXISTS candidate_evaluation (
            operation_id TEXT PRIMARY KEY,
            captured_at TEXT NOT NULL,
            request_id TEXT NOT NULL UNIQUE,
            request_sha256 TEXT NOT NULL,
            schema_sha256 TEXT NOT NULL,
            candidate_id TEXT NOT NULL,
            candidate_pin_sha256 TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            snapshot_id TEXT NOT NULL REFERENCES domain_snapshot(snapshot_id),
            probe_run_id TEXT NOT NULL REFERENCES probe_run(run_id),
            selection_id TEXT NOT NULL REFERENCES selection_run(selection_id),
            disposition TEXT NOT NULL CHECK (
                disposition = 'CANDIDATE_EVALUATED_LOCAL'
            ),
            claim_ceiling TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hook_event (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            captured_at TEXT NOT NULL,
            event TEXT NOT NULL,
            disposition TEXT NOT NULL,
            reason_code TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            details_json TEXT NOT NULL
        );
        """
    )
    current = connection.execute(
        "SELECT value FROM state_meta WHERE key = 'schema_version'"
    ).fetchone()
    if current is not None and int(current["value"]) != SCHEMA_VERSION:
        raise StateError(
            f"unsupported CB Light state schema: {current['value']} != {SCHEMA_VERSION}"
        )
    connection.execute(
        "INSERT OR REPLACE INTO state_meta(key, value) VALUES('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    connection.commit()


def validate_domain(domain: Mapping[str, Any]) -> None:
    if domain.get("schema") != "constraintbox.cb-light-proposal-domain.v1":
        raise StateError("unexpected CB Light domain schema")
    rows = domain.get("rows")
    if not isinstance(rows, list) or not rows:
        raise StateError("CB Light domain has no rows")
    candidate_ids = [row.get("candidate_id") for row in rows]
    if any(not isinstance(value, str) for value in candidate_ids):
        raise StateError("CB Light domain row lacks candidate_id")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise StateError("CB Light domain has duplicate candidate identities")
    identity_rows = [
        {key: value for key, value in row.items() if key != "observation"}
        for row in rows
    ]
    if sha256_bytes(canonical_json(identity_rows)) != domain.get("domain_sha256"):
        raise StateError("CB Light domain digest mismatch")
    counts = domain.get("counts") or {}
    if counts.get("objects") != len(rows):
        raise StateError("CB Light domain count does not match rows")


def _canonical_text(value: Any) -> str:
    """Return the one accepted on-disk representation for structured evidence."""

    return canonical_json(value).decode()


def _existing_parent_matches(
    connection: sqlite3.Connection,
    *,
    table: str,
    id_column: str,
    identity: str,
    columns: tuple[str, ...],
    expected: tuple[Any, ...],
    label: str,
) -> bool:
    """Return whether an immutable parent exists, failing on content drift.

    The content-addressed IDs used by the retained-state tables intentionally do
    not include every retained field.  A matching ID is therefore not enough to
    treat a replay as safe: all non-timestamp parent fields must match before a
    writer can return the existing identity.
    """

    selected = ", ".join(columns)
    row = connection.execute(
        f"SELECT {selected} FROM {table} WHERE {id_column} = ?", (identity,)
    ).fetchone()
    if row is None:
        return False
    actual = tuple(row[column] for column in columns)
    if actual != expected:
        raise StateError(
            f"immutable {label} identity already exists with different parent content"
        )
    return True


def _assert_existing_children_match(
    connection: sqlite3.Connection,
    *,
    table: str,
    parent_column: str,
    identity: str,
    columns: tuple[str, ...],
    order_columns: tuple[str, ...],
    expected: list[tuple[Any, ...]],
    label: str,
) -> None:
    """Fail closed if retained child evidence is not byte-for-byte canonical."""

    selected = ", ".join(columns)
    ordered = ", ".join(order_columns)
    rows = connection.execute(
        f"SELECT {selected} FROM {table} WHERE {parent_column} = ? "
        f"ORDER BY {ordered}",
        (identity,),
    ).fetchall()
    actual = [tuple(row[column] for column in columns) for row in rows]
    if actual != expected:
        raise StateError(
            f"immutable {label} identity already exists with different child content"
        )


@contextmanager
def append_only_transaction(connection: sqlite3.Connection):
    """Own only a transaction this writer opens for immutable preflight/write.

    An existing caller transaction is deliberately neither committed nor rolled
    back; a writer-local savepoint restores partial writes on failure.  When no
    transaction is active, an IMMEDIATE transaction serializes the identity
    preflight with the corresponding append-only insert.
    """

    owns_transaction = not connection.in_transaction
    savepoint_name: str | None = None
    if owns_transaction:
        connection.execute("BEGIN IMMEDIATE")
    else:
        savepoint_name = f"cb_light_append_{uuid.uuid4().hex}"
        connection.execute(f"SAVEPOINT {savepoint_name}")
    try:
        yield
    except BaseException:
        if owns_transaction and connection.in_transaction:
            connection.rollback()
        elif savepoint_name is not None:
            connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
            connection.execute(f"RELEASE SAVEPOINT {savepoint_name}")
        raise
    else:
        if owns_transaction:
            connection.commit()
        elif savepoint_name is not None:
            connection.execute(f"RELEASE SAVEPOINT {savepoint_name}")


# Keep the previous private spelling available for already-contained callers.
# New retained-state companions import the public name so the savepoint rule is
# explicit rather than an accidental private-module dependency.
_append_only_transaction = append_only_transaction


def record_domain(
    connection: sqlite3.Connection, domain: Mapping[str, Any]
) -> str:
    validate_domain(domain)
    environment = domain["environment_observation"]
    observation_sha256 = environment["observation_sha256"]
    snapshot_id = sha256_bytes(
        canonical_json(
            {
                "domain": domain["domain_sha256"],
                "source": domain["source_manifest_sha256"],
                "environment": observation_sha256,
            }
        )
    )
    parent_columns = (
        "profile",
        "domain_sha256",
        "source_manifest_sha256",
        "observation_sha256",
        "completeness",
        "counts_json",
        "environment_json",
        "claim_ceiling",
    )
    parent_values = (
        "cb_light",
        domain["domain_sha256"],
        domain["source_manifest_sha256"],
        observation_sha256,
        domain["completeness"],
        _canonical_text(domain["counts"]),
        _canonical_text(environment),
        domain["claim_ceiling"],
    )
    candidate_columns = ("candidate_id", "kind", "normalized_name", "row_json")
    candidate_rows = sorted(
        [
            (
                row["candidate_id"],
                row["kind"],
                row["normalized_name"],
                _canonical_text(row),
            )
            for row in domain["rows"]
        ],
        key=lambda row: row[0],
    )
    with append_only_transaction(connection):
        if _existing_parent_matches(
            connection,
            table="domain_snapshot",
            id_column="snapshot_id",
            identity=snapshot_id,
            columns=parent_columns,
            expected=parent_values,
            label="domain snapshot",
        ):
            _assert_existing_children_match(
                connection,
                table="domain_candidate",
                parent_column="snapshot_id",
                identity=snapshot_id,
                columns=candidate_columns,
                order_columns=("candidate_id",),
                expected=candidate_rows,
                label="domain snapshot",
            )
            return snapshot_id
        connection.execute(
            """
            INSERT INTO domain_snapshot(
                snapshot_id, captured_at, profile, domain_sha256,
                source_manifest_sha256, observation_sha256, completeness,
                counts_json, environment_json, claim_ceiling
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (snapshot_id, _now(), *parent_values),
        )
        connection.executemany(
            """
            INSERT INTO domain_candidate(
                snapshot_id, candidate_id, kind, normalized_name, row_json
            ) VALUES(?, ?, ?, ?, ?)
            """,
            [
                (snapshot_id, *row)
                for row in candidate_rows
            ],
        )
    return snapshot_id


def validate_probe_matrix(matrix: Mapping[str, Any]) -> None:
    if matrix.get("schema") != "constraintbox.cb-light-core-probes.v1":
        raise StateError("unexpected CB Light probe schema")
    decisions = matrix.get("tool_decisions")
    expected_contract_ids = _expected_core_contract_ids()
    if not isinstance(decisions, list) or len(decisions) != len(expected_contract_ids):
        raise StateError(
            "CB Light core probe matrix tool count differs from the contained registry"
        )
    contract_ids = [row.get("contract_id") for row in decisions]
    if len(contract_ids) != len(set(contract_ids)):
        raise StateError("duplicate CB Light probe contract")
    if set(contract_ids) != set(expected_contract_ids):
        raise StateError(
            "CB Light core probe contracts differ from the contained registry"
        )
    for decision in decisions:
        cases = decision.get("cases")
        if not isinstance(cases, list):
            raise StateError(f"probe contract {decision.get('contract_id')} has no cases")
        kinds = {case.get("kind") for case in cases}
        if kinds != REQUIRED_CASE_KINDS:
            raise StateError(
                f"probe contract {decision.get('contract_id')} case set mismatch: {kinds}"
            )
        all_pass = all(case.get("passed") is True for case in cases)
        expected = "ADMIT" if all_pass else "HOLD"
        if decision.get("disposition") != expected:
            raise StateError(
                f"probe contract {decision.get('contract_id')} disposition laundering"
            )
    if sha256_bytes(canonical_json(decisions)) != matrix.get("evidence_set_sha256"):
        raise StateError("CB Light probe evidence digest mismatch")
    expected_all = all(row["disposition"] == "ADMIT" for row in decisions)
    if bool(matrix.get("all_contracts_satisfied")) != expected_all:
        raise StateError("CB Light aggregate probe status does not match tool decisions")


def record_probe_matrix(
    connection: sqlite3.Connection, matrix: Mapping[str, Any]
) -> str:
    validate_probe_matrix(matrix)
    run_id = matrix["evidence_set_sha256"]
    parent_columns = (
        "interpreter",
        "python_version",
        "contract_set_sha256",
        "source_set_sha256",
        "evidence_set_sha256",
        "all_contracts_satisfied",
        "claim_ceiling",
    )
    parent_values = (
        matrix["interpreter"],
        matrix["python_version"],
        matrix["contract_set_sha256"],
        matrix["source_set_sha256"],
        matrix["evidence_set_sha256"],
        int(bool(matrix["all_contracts_satisfied"])),
        matrix["claim_ceiling"],
    )
    decision_columns = (
        "contract_id",
        "distribution",
        "disposition",
        "reason_code",
        "facts_json",
        "decision_json",
    )
    decision_rows = sorted(
        [
            (
                decision["contract_id"],
                decision["distribution"],
                decision["disposition"],
                decision["reason_code"],
                _canonical_text(decision["facts"]),
                _canonical_text(decision),
            )
            for decision in matrix["tool_decisions"]
        ],
        key=lambda row: row[0],
    )
    case_columns = (
        "contract_id",
        "distribution",
        "case_kind",
        "passed",
        "evidence_json",
    )
    case_rows = sorted(
        [
            (
                decision["contract_id"],
                decision["distribution"],
                case["kind"],
                int(bool(case["passed"])),
                _canonical_text(case),
            )
            for decision in matrix["tool_decisions"]
            for case in decision["cases"]
        ],
        key=lambda row: (row[0], row[2]),
    )
    with append_only_transaction(connection):
        if _existing_parent_matches(
            connection,
            table="probe_run",
            id_column="run_id",
            identity=run_id,
            columns=parent_columns,
            expected=parent_values,
            label="probe run",
        ):
            _assert_existing_children_match(
                connection,
                table="tool_decision",
                parent_column="run_id",
                identity=run_id,
                columns=decision_columns,
                order_columns=("contract_id",),
                expected=decision_rows,
                label="probe run",
            )
            _assert_existing_children_match(
                connection,
                table="probe_case",
                parent_column="run_id",
                identity=run_id,
                columns=case_columns,
                order_columns=("contract_id", "case_kind"),
                expected=case_rows,
                label="probe run",
            )
            return run_id
        connection.execute(
            """
            INSERT INTO probe_run(
                run_id, captured_at, interpreter, python_version,
                contract_set_sha256, source_set_sha256, evidence_set_sha256,
                all_contracts_satisfied, claim_ceiling
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, _now(), *parent_values),
        )
        connection.executemany(
            """
            INSERT INTO tool_decision(
                run_id, contract_id, distribution, disposition,
                reason_code, facts_json, decision_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            [(run_id, *row) for row in decision_rows],
        )
        connection.executemany(
            """
            INSERT INTO probe_case(
                run_id, contract_id, distribution, case_kind, passed,
                evidence_json
            ) VALUES(?, ?, ?, ?, ?, ?)
            """,
            [(run_id, *row) for row in case_rows],
        )
    return run_id


def record_selection(
    connection: sqlite3.Connection,
    selection: Mapping[str, Any],
    *,
    snapshot_id: str,
    probe_run_id: str | None,
) -> str:
    decisions = selection.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        raise StateError("CB Light selection has no row decisions")
    candidate_ids = [decision.get("candidate_id") for decision in decisions]
    if any(not isinstance(candidate_id, str) for candidate_id in candidate_ids):
        raise StateError("CB Light selection row lacks candidate_id")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise StateError("CB Light selection has duplicate candidate identities")
    selection_id = sha256_bytes(canonical_json(decisions))
    parent_columns = (
        "snapshot_id",
        "probe_run_id",
        "domain_sha256",
        "counts_json",
        "owner_approved_adoptions",
        "claim_ceiling",
    )
    parent_values = (
        snapshot_id,
        probe_run_id,
        selection["domain_sha256"],
        _canonical_text(selection["counts"]),
        int(selection["owner_approved_adoptions"]),
        selection["claim_ceiling"],
    )
    decision_columns = (
        "candidate_id",
        "disposition",
        "reason_code",
        "decision_json",
    )
    decision_rows = sorted(
        [
            (
                decision["candidate_id"],
                decision["disposition"],
                decision["reason_code"],
                _canonical_text(decision),
            )
            for decision in decisions
        ],
        key=lambda row: row[0],
    )
    with append_only_transaction(connection):
        if _existing_parent_matches(
            connection,
            table="selection_run",
            id_column="selection_id",
            identity=selection_id,
            columns=parent_columns,
            expected=parent_values,
            label="selection run",
        ):
            _assert_existing_children_match(
                connection,
                table="selection_decision",
                parent_column="selection_id",
                identity=selection_id,
                columns=decision_columns,
                order_columns=("candidate_id",),
                expected=decision_rows,
                label="selection run",
            )
            return selection_id
        connection.execute(
            """
            INSERT INTO selection_run(
                selection_id, captured_at, snapshot_id, probe_run_id,
                domain_sha256, counts_json, owner_approved_adoptions,
                claim_ceiling
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (selection_id, _now(), *parent_values),
        )
        connection.executemany(
            """
            INSERT INTO selection_decision(
                selection_id, candidate_id, disposition, reason_code,
                decision_json
            ) VALUES(?, ?, ?, ?, ?)
            """,
            [
                (selection_id, *row)
                for row in decision_rows
            ],
        )
    return selection_id


def record_candidate_evaluation(
    connection: sqlite3.Connection,
    *,
    operation_id: str,
    request_id: str,
    request_sha256: str,
    schema_sha256: str,
    candidate_id: str,
    candidate_pin_sha256: str,
    source_sha256: str,
    snapshot_id: str,
    probe_run_id: str,
    selection_id: str,
) -> str:
    """Persist a local candidate evaluation without granting any promotion."""

    existing = connection.execute(
        "SELECT operation_id, request_sha256 FROM candidate_evaluation WHERE request_id = ?",
        (request_id,),
    ).fetchone()
    if existing is not None:
        if (
            existing["request_sha256"] != request_sha256
            or existing["operation_id"] != operation_id
        ):
            raise StateError(
                "control-plane request_id already exists with different bound evidence"
            )
        return str(existing["operation_id"])
    with connection:
        connection.execute(
            """
            INSERT INTO candidate_evaluation(
                operation_id, captured_at, request_id, request_sha256,
                schema_sha256, candidate_id, candidate_pin_sha256,
                source_sha256, snapshot_id, probe_run_id, selection_id,
                disposition, claim_ceiling
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                operation_id,
                _now(),
                request_id,
                request_sha256,
                schema_sha256,
                candidate_id,
                candidate_pin_sha256,
                source_sha256,
                snapshot_id,
                probe_run_id,
                selection_id,
                "CANDIDATE_EVALUATED_LOCAL",
                (
                    "Local candidate evaluation only; no membership, adoption, "
                    "portable, provider, CB Heavy, or release claim."
                ),
            ),
        )
    return operation_id


def record_hook_event(
    connection: sqlite3.Connection,
    *,
    event: str,
    disposition: str,
    reason_code: str,
    payload: Any,
    details: Mapping[str, Any],
) -> int:
    with connection:
        cursor = connection.execute(
            """
            INSERT INTO hook_event(
                captured_at, event, disposition, reason_code,
                payload_sha256, details_json
            ) VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                _now(),
                event,
                disposition,
                reason_code,
                sha256_bytes(canonical_json(payload)),
                canonical_json(details).decode(),
            ),
        )
    return int(cursor.lastrowid)


def status(connection: sqlite3.Connection) -> dict[str, Any]:
    domain = connection.execute(
        "SELECT * FROM domain_snapshot ORDER BY captured_at DESC LIMIT 1"
    ).fetchone()
    probe = connection.execute(
        "SELECT * FROM probe_run ORDER BY captured_at DESC LIMIT 1"
    ).fetchone()
    selection = connection.execute(
        "SELECT * FROM selection_run ORDER BY captured_at DESC LIMIT 1"
    ).fetchone()
    domain_body = dict(domain) if domain is not None else None
    if domain_body is not None:
        domain_body["counts"] = json.loads(domain_body.pop("counts_json"))
        environment = json.loads(domain_body.pop("environment_json"))
        environment.pop("ambient_installed", None)
        domain_body["environment"] = environment
    selection_body = dict(selection) if selection is not None else None
    if selection_body is not None:
        selection_body["counts"] = json.loads(selection_body.pop("counts_json"))
    return {
        "schema": "constraintbox.cb-light-state-status.v1",
        "domain": domain_body,
        "probe": dict(probe) if probe is not None else None,
        "selection": selection_body,
        "claim_ceiling": "local SQLite retained state; no external tamper anchor",
    }
