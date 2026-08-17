"""Read-only binding verification for one CB Light candidate evaluation.

This is deliberately not a semantic replay engine.  It compares a supplied
successful control-plane output with the existing typed SQLite row and checks
only the operation's stored integrity envelope.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from hookkernel.cb_light_state import StateError, connect_readonly


RESULT_SCHEMA = "constraintbox.verify-operation.v1"
SUCCESS = "RECEIPT_DB_ENVELOPE_CONSISTENT"
REFUSE_STATE_DATABASE_UNAVAILABLE = "REFUSE_STATE_DATABASE_UNAVAILABLE"
REFUSE_UNSUPPORTED_STATE_SCHEMA = "REFUSE_UNSUPPORTED_STATE_SCHEMA"
REFUSE_SELECTOR_INVALID = "REFUSE_SELECTOR_INVALID"
REFUSE_RECEIPT_SHAPE_INVALID = "REFUSE_RECEIPT_SHAPE_INVALID"
REFUSE_RECEIPT_ROW_MISMATCH = "REFUSE_RECEIPT_ROW_MISMATCH"
REFUSE_RUNTIME_HASH_MISMATCH = "REFUSE_RUNTIME_HASH_MISMATCH"
REFUSE_OPERATION_ID_MISMATCH = "REFUSE_OPERATION_ID_MISMATCH"
HOLD_BASIN_FIELD_INCOMPLETE = "HOLD_BASIN_FIELD_INCOMPLETE"

CLAIM_CEILING = (
    "Read-only supplied-output-to-existing-CB-Light-candidate-evaluation "
    "envelope consistency only; no request-byte custody, semantic "
    "re-execution, lifecycle, promotion, wave, provider, CB Heavy, or "
    "release claim."
)

_RECEIPT_STRING_FIELDS = (
    "schema",
    "profile",
    "operation",
    "operation_id",
    "request_id",
    "request_sha256",
    "request_schema_sha256",
    "candidate_pin_sha256",
    "control_plane_source_sha256",
    "snapshot_id",
    "probe_run_id",
    "selection_id",
    "source_manifest_sha256",
    "probe_interpreter",
    "probe_python_version",
    "control_plane_runtime_sha256",
    "disposition",
)


def _canonical_json_v1(value: Any) -> bytes:
    """Freeze the current producer's exact JSON identity recipe locally."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _sha256_json_v1(value: Any) -> str:
    return hashlib.sha256(_canonical_json_v1(value)).hexdigest()


def _result(
    verification_status: str,
    *,
    selector: dict[str, str] | None = None,
    operation_id: str | None = None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "schema": RESULT_SCHEMA,
        "verification_status": verification_status,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    if selector is not None:
        body["selector"] = selector
    if operation_id is not None:
        body["operation_id"] = operation_id
    return body


def _selector(
    *, operation_id: str | None, request_id: str | None
) -> tuple[dict[str, str] | None, tuple[str, str] | None]:
    if (operation_id is None) == (request_id is None):
        return None, None
    if operation_id is not None and operation_id:
        return {"operation_id": operation_id}, ("operation_id", operation_id)
    if request_id is not None and request_id:
        return {"request_id": request_id}, ("request_id", request_id)
    return None, None


def _validate_receipt(receipt: object) -> Mapping[str, Any] | None:
    if not isinstance(receipt, Mapping):
        return None
    if any(not isinstance(receipt.get(name), str) for name in _RECEIPT_STRING_FIELDS):
        return None
    if (
        receipt.get("schema")
        != "constraintbox.control-plane-candidate-evaluation.v1"
        or receipt.get("profile") != "cb_light"
        or receipt.get("operation") != "candidate_evaluation"
        or receipt.get("disposition") != "CANDIDATE_EVALUATED_LOCAL"
        or receipt.get("promotion_allowed") is not False
    ):
        return None
    if not isinstance(receipt.get("control_plane_runtime"), Mapping):
        return None
    return receipt


def verify_operation(
    receipt: object,
    *,
    db_path: Path,
    operation_id: str | None = None,
    request_id: str | None = None,
) -> dict[str, object]:
    """Verify a supplied output against one existing CB Light SQLite row.

    The verifier opens SQLite through ``connect_readonly`` and never imports
    the evaluator, Pydantic, jsonschema, probes, solvers, or gates.
    """

    from hookkernel.cb_light_basin_view import hold_result_if_incomplete

    held = hold_result_if_incomplete()
    if held is not None:
        return {
            **_result(HOLD_BASIN_FIELD_INCOMPLETE),
            "basin_view": held["basin_view"],
        }

    selector, sql_selector = _selector(
        operation_id=operation_id,
        request_id=request_id,
    )
    if selector is None or sql_selector is None:
        return _result(REFUSE_SELECTOR_INVALID)

    parsed = _validate_receipt(receipt)
    if parsed is None:
        return _result(REFUSE_RECEIPT_SHAPE_INVALID, selector=selector)

    try:
        connection = connect_readonly(db_path)
    except StateError as exc:
        status = (
            REFUSE_UNSUPPORTED_STATE_SCHEMA
            if "schema" in str(exc).lower()
            else REFUSE_STATE_DATABASE_UNAVAILABLE
        )
        return _result(status, selector=selector)
    except sqlite3.Error:
        return _result(REFUSE_STATE_DATABASE_UNAVAILABLE, selector=selector)

    try:
        column, value = sql_selector
        row = connection.execute(
            f"SELECT * FROM candidate_evaluation WHERE {column} = ?",
            (value,),
        ).fetchone()
        if row is None:
            return _result(REFUSE_RECEIPT_ROW_MISMATCH, selector=selector)

        pairs = (
            ("request_id", "request_id"),
            ("request_sha256", "request_sha256"),
            ("request_schema_sha256", "schema_sha256"),
            ("candidate_pin_sha256", "candidate_pin_sha256"),
            ("control_plane_source_sha256", "source_sha256"),
            ("snapshot_id", "snapshot_id"),
            ("probe_run_id", "probe_run_id"),
            ("selection_id", "selection_id"),
        )
        if any(parsed[receipt_key] != row[row_key] for receipt_key, row_key in pairs):
            return _result(REFUSE_RECEIPT_ROW_MISMATCH, selector=selector)
        # Producer v1 output may omit candidate_id; row must still name an allowed
        # typed-envelope candidate under the control-plane literal set.
        if (
            row["candidate_id"] not in {"pydantic", "jsonschema"}
            or row["disposition"] != "CANDIDATE_EVALUATED_LOCAL"
        ):
            return _result(REFUSE_RECEIPT_ROW_MISMATCH, selector=selector)

        selection = connection.execute(
            """
            SELECT
                selection_run.snapshot_id,
                selection_run.probe_run_id,
                domain_snapshot.source_manifest_sha256,
                probe_run.all_contracts_satisfied,
                probe_run.interpreter AS probe_interpreter,
                probe_run.python_version AS probe_python_version
            FROM selection_run
            JOIN domain_snapshot
                ON domain_snapshot.snapshot_id = selection_run.snapshot_id
            JOIN probe_run
                ON probe_run.run_id = selection_run.probe_run_id
            WHERE selection_run.selection_id = ?
            """,
            (row["selection_id"],),
        ).fetchone()
        if (
            selection is None
            or selection["snapshot_id"] != row["snapshot_id"]
            or selection["probe_run_id"] != row["probe_run_id"]
            or selection["source_manifest_sha256"]
            != parsed["source_manifest_sha256"]
            or selection["all_contracts_satisfied"] != 1
            or selection["probe_interpreter"] != parsed["probe_interpreter"]
            or selection["probe_python_version"] != parsed["probe_python_version"]
        ):
            return _result(REFUSE_RECEIPT_ROW_MISMATCH, selector=selector)

        runtime_sha256 = _sha256_json_v1(parsed["control_plane_runtime"])
        if runtime_sha256 != parsed["control_plane_runtime_sha256"]:
            return _result(REFUSE_RUNTIME_HASH_MISMATCH, selector=selector)

        recomputed_operation_id = _sha256_json_v1(
            {
                "request_sha256": parsed["request_sha256"],
                "schema_sha256": parsed["request_schema_sha256"],
                "candidate_pin_sha256": parsed["candidate_pin_sha256"],
                "selection_id": parsed["selection_id"],
                "source_sha256": parsed["control_plane_source_sha256"],
                "runtime_sha256": runtime_sha256,
            }
        )
        if (
            recomputed_operation_id != parsed["operation_id"]
            or recomputed_operation_id != row["operation_id"]
        ):
            return _result(REFUSE_OPERATION_ID_MISMATCH, selector=selector)

        return _result(
            SUCCESS,
            selector=selector,
            operation_id=str(row["operation_id"]),
        )
    except sqlite3.Error:
        return _result(REFUSE_STATE_DATABASE_UNAVAILABLE, selector=selector)
    finally:
        connection.close()


def verify_operation_file(
    receipt_path: Path,
    *,
    db_path: Path,
    operation_id: str | None = None,
    request_id: str | None = None,
) -> dict[str, object]:
    """Load one explicit output object, then perform binding-only verification."""

    try:
        receipt: object = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        selector, _ = _selector(operation_id=operation_id, request_id=request_id)
        return _result(REFUSE_RECEIPT_SHAPE_INVALID, selector=selector)
    return verify_operation(
        receipt,
        db_path=db_path,
        operation_id=operation_id,
        request_id=request_id,
    )
