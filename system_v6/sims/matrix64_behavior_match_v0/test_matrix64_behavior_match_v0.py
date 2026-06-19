from __future__ import annotations

import json
from pathlib import Path

import matrix64_behavior_match_v0 as packet


def test_build_result_contract_without_file_write() -> None:
    payload = packet.build()
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["objects"]["component_count"] == 16
    assert payload["subgroup"]["full_address_group_size"] == 256
    assert payload["subgroup"]["descending_subgroup_size"] == 64
    assert payload["subgroup"]["proper_subgroup"] is True
    assert payload["summary"]["breaking_generators"] == ["vertical_rotation", "trigram_swap"]
    assert payload["controls"]["identity_descends_trivially"]["descends"] is True
    assert payload["controls"]["random_stage_to_component_relabeling"]["breaks_descent_table"] is True
    assert payload["controls"]["deliberately_coarsened_quotient"]["descent_table_changed"] is True
    assert payload["builder_gates"]["g2a_boundary_helper_from_birth"] is True
    assert payload["builder_gates"]["no_hard_audit_absence_assertion"] is True


def test_generator_rows_name_breaking_components() -> None:
    payload = packet.build()
    rows = {row["generator"]: row for row in payload["generator_descent_rows"]}
    for name in [f"flip_line_{line}" for line in range(1, 7)] + ["complement"]:
        assert rows[name]["descends"] is True
        assert rows[name]["breaking_component_count"] == 0
    for name in ("vertical_rotation", "trigram_swap"):
        assert rows[name]["descends"] is False
        assert rows[name]["breaking_component_count"] == 16
        assert len(rows[name]["breaking_components"]) == 16


def test_written_result_if_present_matches_core_contract() -> None:
    if not packet.RESULT.exists():
        return
    payload = json.loads(Path(packet.RESULT).read_text(encoding="utf-8"))
    assert payload["all_pass"] is True
    assert payload["TOOL_MANIFEST"] == packet.TOOL_MANIFEST
    assert payload["TOOL_INTEGRATION_DEPTH"] == packet.TOOL_INTEGRATION_DEPTH
