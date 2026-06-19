#!/usr/bin/env python3
"""Packet-local tests for entropy_type_ratchet_v2 discovery behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import entropy_type_ratchet_v2_common as common


PACKET = Path(__file__).resolve().parent
RESULT = PACKET / "results" / "entropy_type_ratchet_v2_envelope_results.json"


def test_no_declared_enables_gate_on_claim_path() -> None:
    assert not (PACKET / "audit_verdict.md").exists()
    for source in PACKET.glob("entropy_type_ratchet_v2*.py"):
        text = source.read_text(encoding="utf-8")
        assert "PRIMARY_STEP_PLAN" not in text
        assert "declared_enable" not in text
        assert '"enables"' not in text
        assert "'enables'" not in text


def test_availability_is_constructed_from_live_state_lineage() -> None:
    packet = common.build_discovery_packet()
    rows = packet["type_admissibility_table"]["rows"]
    assert len(rows) == 9
    assert all(row["availability_source"] == "construction_attempt" for row in rows)

    first = rows[0]["entropy_types"]
    assert first["von_neumann_entropy"]["status"] == "undefined"
    assert first["von_neumann_entropy"]["failure"]["missing_structure"] == "density_quotient_rho"
    assert first["conditional_vn_and_mutual_information"]["failure"]["missing_structure"] == "bipartition_subsystem_split"
    assert first["coherent_information"]["failure"]["missing_structure"] == "channel_update_map"
    assert first["state_plus_record_conservation"]["failure"]["missing_structure"] == "record_syndrome_preimage_table"

    lens = rows[2]["entropy_types"]["von_neumann_entropy"]
    assert lens["status"] == "computable"
    assert lens["value"]["constructed_from"] == "quotient_map_partial_trace_from_live_state_vector"
    assert lens["rho"]["source"] == "state_lineage.quotient_map"

    terrain = rows[3]["entropy_types"]["conditional_vn_and_mutual_information"]
    assert terrain["status"] == "degenerate"
    assert terrain["degenerate_witness"]["product_state"] is True

    channel = rows[4]["entropy_types"]["coherent_information"]
    assert channel["status"] == "computable"
    assert channel["value"]["constructed_from"] == "lineage_update_map_channel_object"

    record = rows[5]["entropy_types"]["state_plus_record_conservation"]
    assert record["status"] == "computable"
    assert record["value"]["computed_defect_exact"] == "0"


def test_controls_reject_v0_and_type_confusion() -> None:
    packet = common.build_discovery_packet()
    controls = packet["controls"]
    assert controls["spoofed_enable"]["pass"] is True
    assert controls["spoofed_enable"]["rejected_reason"] == "declared-enable shortcut rejected before construction"
    assert controls["composed_sequence_rejection"]["pass"] is True
    assert controls["alternative_sequence"]["pass"] is True
    assert isinstance(controls["alternative_sequence"]["off_doctrine_findings"], list)
    assert controls["type_confusion"]["pass"] is True
    assert controls["degenerate_flag"]["pass"] is True
    assert all(row["pass"] for row in controls["premature_evaluation"].values())


def test_primary_sequence_is_derived_from_parent_artifacts() -> None:
    packet = common.build_discovery_packet()
    derivation = packet["sequence_derivation"]
    rows = packet["type_admissibility_table"]["rows"]
    assert derivation["sequence_source"] == "consumed_parent_artifacts"
    assert derivation["operation_order"] == [row["step_id"] for row in rows]
    assert len(derivation["parent_rows"]) == 9
    assert derivation["parent_rows"][1]["source"] == "manifold_unified_run_v0_trajectory"
    assert derivation["parent_rows"][4]["source"] == "ratchet_deep_chain_v0"
    assert derivation["source_paths"]["manifold_unified_run_v0_trajectory"]["git_head_blob"]
    assert derivation["source_paths"]["ratchet_deep_chain_v0"]["sha256"]


def test_composed_in_packet_sequence_is_rejected() -> None:
    with pytest.raises(common.ComposedSequenceRejected, match="composed-in-packet sequence rejected"):
        common.reject_composed_sequence(
            {
                "sequence_source": "packet_local_literal",
                "operation_order": ["integrated_seed", "leaf_conditioning", "lens_quotient", "terrain_restriction"],
            }
        )


def test_order_shuffle_changes_discovered_sequence() -> None:
    packet = common.build_discovery_packet()
    order = packet["controls"]["order_shuffle"]
    assert order["prediction_2_status"] == "survived"
    assert order["primary_sequence"] != order["swap_chart_and_density_sequence"]
    assert order["primary_sequence"] != order["delay_record_until_saturation_sequence"]


def test_alternative_committed_order_reports_off_doctrine_findings_plainly() -> None:
    packet = common.build_discovery_packet()
    alternative = packet["alternative_sequence_findings"]
    assert alternative["meta"]["alternative_source"] == "ratchet_order_breadth_v0.controls.live_order_blind_signatures"
    assert alternative["meta"]["alternative_token_order"] != alternative["meta"]["baseline_parent_order_token"]
    assert alternative["finding_status"] in {"FINDING", "no_off_doctrine_availability_steps_observed"}
    assert isinstance(alternative["off_doctrine_findings"], list)


def test_operator_co_ratchet_attempts_are_construction_bound() -> None:
    packet = common.build_discovery_packet()
    rows = packet["type_admissibility_table"]["rows"]
    assert rows[0]["operator_co_ratchet"]["density_CPTP_probe"]["status"] == "failed"
    assert rows[0]["operator_co_ratchet"]["density_CPTP_probe"]["missing_structure"] == "density_quotient_rho"
    assert rows[2]["operator_co_ratchet"]["density_CPTP_probe"]["status"] == "applied"
    assert rows[4]["operator_co_ratchet"]["channel_update_probe"]["status"] == "applied"
    assert rows[5]["operator_co_ratchet"]["record_conditioned_reconstruction_probe"]["status"] == "applied"


def test_envelope_if_present_records_boundary_and_smt_flip() -> None:
    if not RESULT.exists():
        pytest.skip("envelope not built yet")
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["builder_gates"]["no_builder_audit_verdict"] is True
    assert payload["builder_gates"]["sequence_from_parent"] is True
    assert payload["builder_gates"]["composed_sequence_rejected"] is True
    assert payload["sequence_derivation"]["sequence_source"] == "consumed_parent_artifacts"
    assert "alternative_sequence_findings" in payload
    assert payload["crossover_proofs"]["z3"]["verdict"] == "unsat"
    assert payload["crossover_proofs"]["z3"]["perturbed_construction_path_verdict"] == "sat"
    assert payload["crossover_proofs"]["cvc5"]["perturbed_construction_path_verdict"] == "sat"
