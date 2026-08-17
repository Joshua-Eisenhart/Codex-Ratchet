from __future__ import annotations

from hookkernel.cb_light_state import (
    REQUIRED_CASE_KINDS,
    connect,
    record_probe_matrix,
)
from constraintbox.cb_light_probes import _reference, run_core_probe_matrix
from constraintbox.core_tools import load_registry


def test_cvc5_reference_rejects_sat_with_an_invalid_witness():
    invalid = _reference(
        "python.cvc5", {"status": "sat", "is_sat": True, "witness": 1}
    )
    valid = _reference(
        "python.cvc5", {"status": "sat", "is_sat": True, "witness": 0}
    )
    assert invalid["agrees"] is False
    assert valid["agrees"] is True


def test_declared_tools_fire_full_probe_contracts_and_retain_rows(tmp_path):
    matrix = run_core_probe_matrix(timeout_seconds=15)
    assert matrix["all_contracts_satisfied"] is True
    expected_count = len(load_registry()["tools"])
    assert len(matrix["tool_decisions"]) == expected_count
    for decision in matrix["tool_decisions"]:
        assert decision["disposition"] == "ADMIT"
        assert {case["kind"] for case in decision["cases"]} == REQUIRED_CASE_KINDS
        assert all(case["passed"] for case in decision["cases"])
        assert decision["facts"]["reason_specific_negative"] is True
        assert decision["facts"]["single_field_boundary_flip"] is True
        assert decision["facts"]["deterministic_replay"] is True
        assert decision["facts"]["severance_observed"] is True
        assert decision["facts"]["reference_agreement"] is True

    connection = connect(tmp_path / "state.sqlite3")
    run_id = record_probe_matrix(connection, matrix)
    cases = connection.execute(
        "SELECT COUNT(*) FROM probe_case WHERE run_id = ?", (run_id,)
    ).fetchone()[0]
    decisions = connection.execute(
        "SELECT COUNT(*) FROM tool_decision WHERE run_id = ?", (run_id,)
    ).fetchone()[0]
    assert cases == expected_count * len(REQUIRED_CASE_KINDS)
    assert decisions == expected_count
    connection.close()
