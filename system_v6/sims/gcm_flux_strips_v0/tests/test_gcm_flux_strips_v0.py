from __future__ import annotations

from itertools import combinations

from gcm_flux_strips_v0 import SHELL_ORDER, build_payload, validate_payload


def test_complete_strip_table_has_all_ten_pairs() -> None:
    payload = build_payload(write=False)
    assert [row["ordered_shell_pair"] for row in payload["complete_strip_table"]] == [list(pair) for pair in combinations(SHELL_ORDER, 2)]


def test_every_strip_is_stokes_closed_and_not_leakage() -> None:
    payload = build_payload(write=False)
    assert payload["leakage_summary"]["row_count"] == 10
    assert payload["leakage_summary"]["open_count"] == 0
    assert payload["leakage_summary"]["max_abs_stokes_residual"] <= 1e-12
    assert all(row["leakage_adjudication"]["status"] == "closed_no_leakage" for row in payload["complete_strip_table"])


def test_contract_and_substrate_checks_pass() -> None:
    payload = build_payload(write=False)
    assert payload["three_axis_declaration"] == {"layers": "10-12", "nesting": "integrated", "qubit_depth": "1Q"}
    assert payload["substrate_enforcement"]["positive_payload_ok"]["ok"] is True
    assert payload["substrate_enforcement"]["lineage_free_negative"]["ok"] is False
    assert validate_payload(payload) == []

