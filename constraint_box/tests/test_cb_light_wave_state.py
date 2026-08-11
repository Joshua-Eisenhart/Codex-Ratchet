from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from constraint_box.hookkernel import cb_light_wave_state
from constraint_box.hookkernel.cb_light_domain import canonical_json, sha256_bytes
from constraint_box.hookkernel.cb_light_state import StateError, connect, connect_readonly
from constraint_box.hookkernel.cb_light_wave_state import (
    initialize_wave_state,
    load_wave_attempt,
    record_artifact,
    record_asset_binding,
    record_wave_attempt,
    record_wave_settlement,
    verify_wave_attempt,
)


CLAIM = "fixture ledger only; no invocation, provider, adoption, or CB Heavy claim"
ROOT = Path(__file__).resolve().parents[1]


def test_packaged_hookkernel_mirrors_match_root_sources() -> None:
    """The contained wheel must receive the same state implementation we test."""

    for relative in (
        "cb_light_state.py",
        "cb_light_wave_state.py",
    ):
        assert (ROOT / "hookkernel" / relative).read_bytes() == (
            ROOT / "light_runtime" / "src" / "hookkernel" / relative
        ).read_bytes()


def _plan_fingerprint() -> str:
    return sha256_bytes(canonical_json({"fixture_plan": "nested-wave-v1"}))


def _artifact(connection: sqlite3.Connection, kind: str, payload: object) -> str:
    return record_artifact(
        connection,
        artifact_kind=kind,
        payload=payload,
        claim_ceiling=CLAIM,
    )


def _attempt(
    connection: sqlite3.Connection, *, fixture_mode: bool = True
) -> tuple[str, dict[str, str]]:
    artifacts = {
        "topology": _artifact(
            connection,
            "topology",
            {"wave": "fixture", "councils": ["generator", "falsifier"]},
        ),
        "input": _artifact(
            connection,
            "input",
            {"issue": "fixture issue", "scope": "CB Light only"},
        ),
        "asset": _artifact(
            connection,
            "asset_descriptor",
            {"asset_id": "fixture:formal-check", "roles": ["probe", "gate"]},
        ),
        "reference": _artifact(
            connection,
            "asset_reference",
            {"asset_id": "fixture:formal-check", "reference": "declared local"},
        ),
        "invocation": _artifact(
            connection,
            "invocation",
            {"asset_id": "fixture:formal-check", "result": "not-for-fixture"},
        ),
        "receipt": _artifact(
            connection,
            "gate_receipt",
            {"gate": "fixture", "result": "HOLD"},
        ),
    }
    attempt = record_wave_attempt(
        connection,
        plan_fingerprint=_plan_fingerprint(),
        topology_artifact_sha256=artifacts["topology"],
        input_artifact_sha256=artifacts["input"],
        fixture_mode=fixture_mode,
        claim_ceiling=CLAIM,
    )
    return attempt, artifacts


def _bound_fixture(
    connection: sqlite3.Connection,
) -> tuple[str, dict[str, str], str]:
    attempt, artifacts = _attempt(connection)
    binding = record_asset_binding(
        connection,
        attempt_id=attempt,
        council_id="fixture-council",
        member_id="fixture-member",
        asset_id="fixture:formal-check",
        purpose="counterexample-probe",
        binding_state="bound_reference",
        fixture_mode=True,
        asset_artifact_sha256=artifacts["asset"],
        reference_artifact_sha256=artifacts["reference"],
        claim_ceiling=CLAIM,
    )
    return attempt, artifacts, binding


def test_plan_fingerprint_is_nonunique_and_attempt_identity_is_fresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    timestamps = iter(
        (
            "topology",
            "input",
            "asset",
            "reference",
            "invocation",
            "receipt",
            "attempt-one",
            "attempt-two",
        )
    )
    monkeypatch.setattr(cb_light_wave_state, "_now", lambda: next(timestamps))
    connection = connect(tmp_path / "state.sqlite3")
    first, artifacts = _attempt(connection)
    second = record_wave_attempt(
        connection,
        plan_fingerprint=_plan_fingerprint(),
        topology_artifact_sha256=artifacts["topology"],
        input_artifact_sha256=artifacts["input"],
        fixture_mode=True,
        claim_ceiling=CLAIM,
    )

    assert first != second
    rows = connection.execute(
        """
        SELECT attempt_id, captured_at FROM cb_light_wave_attempt
        WHERE plan_fingerprint = ? ORDER BY captured_at
        """,
        (_plan_fingerprint(),),
    ).fetchall()
    assert [(row["attempt_id"], row["captured_at"]) for row in rows] == [
        (first, "attempt-one"),
        (second, "attempt-two"),
    ]
    assert (
        record_wave_attempt(
            connection,
            attempt_id=first,
            plan_fingerprint=_plan_fingerprint(),
            topology_artifact_sha256=artifacts["topology"],
            input_artifact_sha256=artifacts["input"],
            fixture_mode=True,
            claim_ceiling=CLAIM,
        )
        == first
    )
    assert connection.execute(
        "SELECT COUNT(*) FROM cb_light_wave_attempt"
    ).fetchone()[0] == 2
    connection.close()


def test_content_addressed_replay_and_immutable_rows(tmp_path: Path) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    attempt, artifacts, binding = _bound_fixture(connection)
    settlement = record_wave_settlement(
        connection,
        attempt_id=attempt,
        outcome="HOLD",
        reason_code="FIXTURE_NO_EXTERNAL_INVOCATION",
        gate_artifact_sha256=artifacts["receipt"],
        receipt_artifact_sha256=artifacts["receipt"],
        claim_ceiling=CLAIM,
    )
    assert (
        record_asset_binding(
            connection,
            attempt_id=attempt,
            council_id="fixture-council",
            member_id="fixture-member",
            asset_id="fixture:formal-check",
            purpose="counterexample-probe",
            binding_state="bound_reference",
            fixture_mode=True,
            asset_artifact_sha256=artifacts["asset"],
            reference_artifact_sha256=artifacts["reference"],
            claim_ceiling=CLAIM,
        )
        == binding
    )
    assert (
        record_wave_settlement(
            connection,
            attempt_id=attempt,
            outcome="HOLD",
            reason_code="FIXTURE_NO_EXTERNAL_INVOCATION",
            gate_artifact_sha256=artifacts["receipt"],
            receipt_artifact_sha256=artifacts["receipt"],
            claim_ceiling=CLAIM,
        )
        == settlement
    )
    with pytest.raises(StateError, match="freezes this attempt's binding set"):
        record_asset_binding(
            connection,
            attempt_id=attempt,
            council_id="fixture-council",
            member_id="fixture-member",
            asset_id="fixture:formal-check",
            purpose="late-extra-probe",
            binding_state="bound_reference",
            fixture_mode=True,
            asset_artifact_sha256=artifacts["asset"],
            reference_artifact_sha256=artifacts["reference"],
            claim_ceiling=CLAIM,
        )

    identifiers = {
        "cb_light_wave_artifact": ("artifact_sha256", artifacts["asset"]),
        "cb_light_wave_attempt": ("attempt_id", attempt),
        "cb_light_wave_asset_binding": ("binding_id", binding),
        "cb_light_wave_settlement": ("settlement_id", settlement),
    }
    for table, (column, identity) in identifiers.items():
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                f"UPDATE {table} SET captured_at = ? WHERE {column} = ?",
                ("forged", identity),
            )
        connection.rollback()
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                f"DELETE FROM {table} WHERE {column} = ?", (identity,)
            )
        connection.rollback()
    assert verify_wave_attempt(connection, attempt)["settlement"]["settlement_id"] == settlement
    connection.close()


def test_failed_child_binding_write_rolls_back_its_savepoint_not_caller_work(
    tmp_path: Path,
) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    attempt, artifacts = _attempt(connection)
    connection.execute("BEGIN")
    connection.execute(
        """
        INSERT INTO hook_event(
            captured_at, event, disposition, reason_code,
            payload_sha256, details_json
        ) VALUES(?, ?, ?, ?, ?, ?)
        """,
        ("outer", "fixture", "ADMIT", "OUTER_WORK", "payload", "{}"),
    )
    connection.execute(
        """
        CREATE TEMP TRIGGER fixture_fail_wave_binding
        BEFORE INSERT ON cb_light_wave_asset_binding
        BEGIN
            SELECT RAISE(ABORT, 'fixture binding child failure');
        END
        """
    )

    with pytest.raises(sqlite3.IntegrityError, match="fixture binding child failure"):
        record_asset_binding(
            connection,
            attempt_id=attempt,
            council_id="fixture-council",
            member_id="fixture-member",
            asset_id="fixture:formal-check",
            purpose="counterexample-probe",
            binding_state="bound_reference",
            fixture_mode=True,
            asset_artifact_sha256=artifacts["asset"],
            reference_artifact_sha256=artifacts["reference"],
            claim_ceiling=CLAIM,
        )

    assert connection.in_transaction
    assert connection.execute("SELECT COUNT(*) FROM hook_event").fetchone()[0] == 1
    assert connection.execute(
        "SELECT COUNT(*) FROM cb_light_wave_asset_binding"
    ).fetchone()[0] == 0
    connection.commit()
    assert connection.execute("SELECT COUNT(*) FROM hook_event").fetchone()[0] == 1
    connection.close()


def test_foreign_keys_are_enforced_for_bindings(tmp_path: Path) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    _attempt_id, artifacts = _attempt(connection)
    with pytest.raises(StateError, match="attempt is absent"):
        record_asset_binding(
            connection,
            attempt_id="missing-attempt",
            council_id="fixture-council",
            member_id="fixture-member",
            asset_id="fixture:formal-check",
            purpose="counterexample-probe",
            binding_state="declared",
            fixture_mode=True,
            asset_artifact_sha256=artifacts["asset"],
            claim_ceiling=CLAIM,
        )
    with pytest.raises(sqlite3.IntegrityError):
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
            (
                "b" * 64,
                "forged",
                "missing-attempt",
                "fixture-council",
                "fixture-member",
                "fixture:formal-check",
                "counterexample-probe",
                "declared",
                1,
                artifacts["asset"],
                None,
                None,
                None,
                CLAIM,
            ),
        )
    connection.rollback()
    connection.close()


@pytest.mark.parametrize("binding_state", ("invoked", "receipt_verified"))
def test_fixture_bindings_refuse_invoked_and_receipt_verified(
    tmp_path: Path, binding_state: str
) -> None:
    connection = connect(tmp_path / f"{binding_state}.sqlite3")
    attempt, artifacts = _attempt(connection)
    kwargs: dict[str, str] = {
        "reference_artifact_sha256": artifacts["reference"],
        "invocation_artifact_sha256": artifacts["invocation"],
    }
    if binding_state == "receipt_verified":
        kwargs["receipt_artifact_sha256"] = artifacts["receipt"]
    with pytest.raises(StateError, match="cannot claim invoked or receipt_verified"):
        record_asset_binding(
            connection,
            attempt_id=attempt,
            council_id="fixture-council",
            member_id="fixture-member",
            asset_id="fixture:formal-check",
            purpose="counterexample-probe",
            binding_state=binding_state,
            fixture_mode=True,
            asset_artifact_sha256=artifacts["asset"],
            claim_ceiling=CLAIM,
            **kwargs,
        )
    assert connection.execute(
        "SELECT COUNT(*) FROM cb_light_wave_asset_binding"
    ).fetchone()[0] == 0
    connection.close()


def test_raw_binding_cannot_lie_about_a_fixture_attempt_mode(tmp_path: Path) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    attempt, artifacts = _attempt(connection, fixture_mode=True)
    with pytest.raises(sqlite3.IntegrityError, match="fixture mode does not match attempt"):
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
            (
                "c" * 64,
                "forged",
                attempt,
                "fixture-council",
                "fixture-member",
                "fixture:formal-check",
                "counterexample-probe",
                "invoked",
                0,
                artifacts["asset"],
                artifacts["reference"],
                artifacts["invocation"],
                None,
                CLAIM,
            ),
        )
    connection.rollback()
    connection.close()


def test_load_path_refuses_trigger_and_content_tampering(tmp_path: Path) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    attempt, artifacts, _binding = _bound_fixture(connection)
    record_wave_settlement(
        connection,
        attempt_id=attempt,
        outcome="HOLD",
        reason_code="FIXTURE_NO_EXTERNAL_INVOCATION",
        gate_artifact_sha256=artifacts["receipt"],
        receipt_artifact_sha256=artifacts["receipt"],
        claim_ceiling=CLAIM,
    )
    assert load_wave_attempt(connection, attempt)["attempt"]["attempt_id"] == attempt

    connection.execute("DROP TRIGGER cb_light_wave_artifact_no_update")
    connection.execute(
        "UPDATE cb_light_wave_artifact SET content_json = ? WHERE artifact_sha256 = ?",
        ('{"forged":true}', artifacts["asset"]),
    )
    connection.commit()
    with pytest.raises(StateError, match="immutable trigger is missing or invalid"):
        load_wave_attempt(connection, attempt)

    initialize_wave_state(connection)
    with pytest.raises(StateError, match="content address mismatch"):
        load_wave_attempt(connection, attempt)
    connection.close()


def test_readonly_loader_uses_the_existing_cb_light_state_database(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite3"
    connection = connect(path)
    attempt, artifacts, _binding = _bound_fixture(connection)
    record_wave_settlement(
        connection,
        attempt_id=attempt,
        outcome="HOLD",
        reason_code="FIXTURE_NO_EXTERNAL_INVOCATION",
        gate_artifact_sha256=artifacts["receipt"],
        receipt_artifact_sha256=artifacts["receipt"],
        claim_ceiling=CLAIM,
    )
    connection.close()

    readonly = connect_readonly(path)
    loaded = verify_wave_attempt(readonly, attempt)
    assert loaded["settlement"]["outcome"] == "HOLD"
    readonly.close()
