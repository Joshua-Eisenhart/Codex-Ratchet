from __future__ import annotations

import copy
import inspect
import sqlite3
from pathlib import Path

import pytest

from constraint_box.hookkernel import cb_light_state
from constraint_box.hookkernel.cb_light_domain import (
    canonical_json,
    compile_domain,
    sha256_bytes,
)
from constraint_box.hookkernel.cb_light_state import (
    REQUIRED_CASE_KINDS,
    StateError,
    connect,
    record_domain,
    record_probe_matrix,
    record_selection,
)


MANDATED = Path(__file__).resolve().parents[1] / ".venv/bin/python"


def _domain() -> dict:
    return compile_domain(
        installed={"z3-solver": "4.16.0.0"},
        distribution_imports={"z3-solver": ["z3"]},
        interpreter=str(MANDATED),
    )


def _matrix() -> dict:
    decisions = []
    for index in range(5):
        cases = [
            {"kind": kind, "passed": True, "fixture": f"case-{index}-{kind}"}
            for kind in sorted(REQUIRED_CASE_KINDS)
        ]
        decisions.append(
            {
                "contract_id": f"fixture-contract-{index}",
                "distribution": f"fixture-distribution-{index}",
                "disposition": "ADMIT",
                "reason_code": "FIXTURE_CONTRACT_SATISFIED",
                "facts": {"fixture": index},
                "cases": cases,
            }
        )
    return {
        "schema": "constraintbox.cb-light-core-probes.v1",
        "interpreter": str(MANDATED),
        "python_version": "3.fixture",
        "contract_set_sha256": "fixture-contract-set",
        "source_set_sha256": "fixture-source-set",
        "evidence_set_sha256": sha256_bytes(canonical_json(decisions)),
        "all_contracts_satisfied": True,
        "claim_ceiling": "fixture local probe evidence only",
        "tool_decisions": decisions,
    }


def _selection(domain: dict) -> dict:
    return {
        "domain_sha256": domain["domain_sha256"],
        "counts": {"fixture": 2},
        "owner_approved_adoptions": 0,
        "claim_ceiling": "fixture local selection only",
        "decisions": [
            {
                "candidate_id": "fixture:alpha",
                "disposition": "SELECTED_FOR_WORK",
                "reason_code": "FIXTURE_SELECTED",
            },
            {
                "candidate_id": "fixture:beta",
                "disposition": "HOLD",
                "reason_code": "FIXTURE_HELD",
            },
        ],
    }


def _stored_state(tmp_path: Path):
    connection = connect(tmp_path / "state.sqlite3")
    domain = _domain()
    matrix = _matrix()
    selection = _selection(domain)
    snapshot_id = record_domain(connection, domain)
    run_id = record_probe_matrix(connection, matrix)
    selection_id = record_selection(
        connection,
        selection,
        snapshot_id=snapshot_id,
        probe_run_id=run_id,
    )
    return connection, domain, matrix, selection, snapshot_id, run_id, selection_id


def _retained_rows(connection):
    tables = (
        "domain_snapshot",
        "domain_candidate",
        "probe_run",
        "tool_decision",
        "probe_case",
        "selection_run",
        "selection_decision",
    )
    return {
        table: [
            tuple(row)
            for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2")
        ]
        for table in tables
    }


def test_state_writers_replay_identical_canonical_input_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    timestamps = iter(("domain-first", "probe-first", "selection-first"))
    monkeypatch.setattr(cb_light_state, "_now", lambda: next(timestamps))

    connection = connect(tmp_path / "state.sqlite3")
    domain = _domain()
    matrix = _matrix()
    selection = _selection(domain)
    snapshot_id = record_domain(connection, domain)
    run_id = record_probe_matrix(connection, matrix)
    selection_id = record_selection(
        connection,
        selection,
        snapshot_id=snapshot_id,
        probe_run_id=run_id,
    )
    before = _retained_rows(connection)

    assert record_domain(connection, domain) == snapshot_id
    assert record_probe_matrix(connection, matrix) == run_id
    assert (
        record_selection(
            connection,
            selection,
            snapshot_id=snapshot_id,
            probe_run_id=run_id,
        )
        == selection_id
    )
    assert _retained_rows(connection) == before
    connection.close()


def test_state_writers_leave_a_preexisting_caller_transaction_open(
    tmp_path: Path,
) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    domain = _domain()
    matrix = _matrix()
    selection = _selection(domain)

    connection.execute("BEGIN")
    snapshot_id = record_domain(connection, domain)
    assert connection.in_transaction
    run_id = record_probe_matrix(connection, matrix)
    assert connection.in_transaction
    selection_id = record_selection(
        connection,
        selection,
        snapshot_id=snapshot_id,
        probe_run_id=run_id,
    )
    assert connection.in_transaction
    connection.commit()
    assert not connection.in_transaction

    connection.execute("BEGIN")
    assert record_domain(connection, domain) == snapshot_id
    assert connection.in_transaction
    assert record_probe_matrix(connection, matrix) == run_id
    assert connection.in_transaction
    assert (
        record_selection(
            connection,
            selection,
            snapshot_id=snapshot_id,
            probe_run_id=run_id,
        )
        == selection_id
    )
    assert connection.in_transaction
    connection.commit()
    assert not connection.in_transaction
    connection.close()


def test_caller_transaction_savepoint_rolls_back_partial_writer_state(
    tmp_path: Path,
) -> None:
    connection = connect(tmp_path / "state.sqlite3")
    domain = _domain()

    connection.execute("BEGIN")
    connection.execute(
        """
        INSERT INTO hook_event(
            captured_at, event, disposition, reason_code,
            payload_sha256, details_json
        ) VALUES(?, ?, ?, ?, ?, ?)
        """,
        (
            "outer-transaction",
            "fixture",
            "ADMIT",
            "OUTER_WORK",
            "fixture-payload",
            "{}",
        ),
    )
    connection.execute(
        """
        CREATE TEMP TRIGGER fixture_fail_domain_candidate
        BEFORE INSERT ON domain_candidate
        BEGIN
            SELECT RAISE(ABORT, 'fixture child failure');
        END
        """
    )

    with pytest.raises(sqlite3.IntegrityError, match="fixture child failure"):
        record_domain(connection, domain)

    assert connection.in_transaction
    assert connection.execute("SELECT COUNT(*) FROM hook_event").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM domain_snapshot").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM domain_candidate").fetchone()[0] == 0

    connection.commit()
    assert not connection.in_transaction
    assert connection.execute("SELECT COUNT(*) FROM hook_event").fetchone()[0] == 1
    connection.close()


def test_state_writers_reject_same_identity_with_different_parent_content(
    tmp_path: Path,
) -> None:
    (
        connection,
        domain,
        matrix,
        selection,
        snapshot_id,
        run_id,
        _selection_id,
    ) = _stored_state(tmp_path)
    before = _retained_rows(connection)

    altered_domain = copy.deepcopy(domain)
    altered_domain["claim_ceiling"] = "different but not identity-addressed"
    with pytest.raises(StateError, match="different parent content"):
        record_domain(connection, altered_domain)
    assert _retained_rows(connection) == before

    altered_matrix = copy.deepcopy(matrix)
    altered_matrix["interpreter"] = "/fixture/different-python"
    with pytest.raises(StateError, match="different parent content"):
        record_probe_matrix(connection, altered_matrix)
    assert _retained_rows(connection) == before

    altered_selection = copy.deepcopy(selection)
    altered_selection["counts"] = {"fixture": 99}
    with pytest.raises(StateError, match="different parent content"):
        record_selection(
            connection,
            altered_selection,
            snapshot_id=snapshot_id,
            probe_run_id=run_id,
        )
    assert _retained_rows(connection) == before
    connection.close()


@pytest.mark.parametrize(
    "child_table",
    (
        "domain_candidate",
        "tool_decision",
        "probe_case",
        "selection_decision",
    ),
)
def test_state_writers_reject_existing_child_content_drift_without_rewrite(
    tmp_path: Path, child_table: str
) -> None:
    (
        connection,
        domain,
        matrix,
        selection,
        snapshot_id,
        run_id,
        selection_id,
    ) = _stored_state(tmp_path / child_table)

    with connection:
        if child_table == "domain_candidate":
            candidate_id = connection.execute(
                "SELECT candidate_id FROM domain_candidate WHERE snapshot_id = ? "
                "ORDER BY candidate_id LIMIT 1",
                (snapshot_id,),
            ).fetchone()[0]
            connection.execute(
                "UPDATE domain_candidate SET row_json = ? "
                "WHERE snapshot_id = ? AND candidate_id = ?",
                ('{"forged":true}', snapshot_id, candidate_id),
            )
        elif child_table == "tool_decision":
            contract_id = connection.execute(
                "SELECT contract_id FROM tool_decision WHERE run_id = ? "
                "ORDER BY contract_id LIMIT 1",
                (run_id,),
            ).fetchone()[0]
            connection.execute(
                "UPDATE tool_decision SET facts_json = ? "
                "WHERE run_id = ? AND contract_id = ?",
                ('{"forged":true}', run_id, contract_id),
            )
        elif child_table == "probe_case":
            case = connection.execute(
                "SELECT contract_id, case_kind FROM probe_case WHERE run_id = ? "
                "ORDER BY contract_id, case_kind LIMIT 1",
                (run_id,),
            ).fetchone()
            connection.execute(
                "UPDATE probe_case SET evidence_json = ? "
                "WHERE run_id = ? AND contract_id = ? AND case_kind = ?",
                ('{"forged":true}', run_id, case["contract_id"], case["case_kind"]),
            )
        else:
            candidate_id = connection.execute(
                "SELECT candidate_id FROM selection_decision WHERE selection_id = ? "
                "ORDER BY candidate_id LIMIT 1",
                (selection_id,),
            ).fetchone()[0]
            connection.execute(
                "UPDATE selection_decision SET decision_json = ? "
                "WHERE selection_id = ? AND candidate_id = ?",
                ('{"forged":true}', selection_id, candidate_id),
            )

    before = _retained_rows(connection)
    with pytest.raises(StateError, match="different child content"):
        if child_table == "domain_candidate":
            record_domain(connection, domain)
        elif child_table in {"tool_decision", "probe_case"}:
            record_probe_matrix(connection, matrix)
        else:
            record_selection(
                connection,
                selection,
                snapshot_id=snapshot_id,
                probe_run_id=run_id,
            )
    assert _retained_rows(connection) == before
    connection.close()


def test_state_writers_contain_no_replace_or_child_delete_sql() -> None:
    for writer in (record_domain, record_probe_matrix, record_selection):
        source = inspect.getsource(writer)
        assert "OR REPLACE" not in source
        assert "DELETE FROM" not in source
