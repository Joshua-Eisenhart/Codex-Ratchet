#!/usr/bin/env python3
"""Focused tests for ring_checkerboard_qca_v3."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PACKET = Path(__file__).resolve().parents[1]
RESULT = PACKET / "results" / "ring_checkerboard_qca_v3_envelope_results.json"
sys.path.insert(0, str(PACKET))

import ring_checkerboard_qca_v3_common as common  # noqa: E402


def rows_by_id(packet: dict) -> dict:
    return {row["rule_id"]: row for row in packet["index_table"]}


def test_open_chain_calibrations_are_extracted_from_ranks() -> None:
    packet = common.build_packet()
    rows = rows_by_id(packet)
    assert rows["calibration_right_shift"]["right_crossing_rank"]["support_factor_vector_space_dim"] == 4
    assert rows["calibration_right_shift"]["left_crossing_rank"]["support_factor_vector_space_dim"] == 1
    assert rows["calibration_right_shift"]["signed_log2_index"] == 1
    assert rows["calibration_left_shift"]["right_crossing_rank"]["support_factor_vector_space_dim"] == 1
    assert rows["calibration_left_shift"]["left_crossing_rank"]["support_factor_vector_space_dim"] == 4
    assert rows["calibration_left_shift"]["signed_log2_index"] == -1
    assert rows["calibration_nonshifting_onsite"]["signed_log2_index"] == 0
    assert rows["paired_block_index0"]["signed_log2_index"] == 0
    assert all(row["metadata_flow_fields_present"] is False for row in rows.values())
    assert all("wire_flow" not in row for row in rows.values())


def test_lr_gauge_and_real_flip_controls() -> None:
    packet = common.build_packet()
    rows = rows_by_id(packet)
    controls = packet["index_controls"]
    assert rows["engine_L_flux_IN_left_O1"]["signed_log2_index"] == -1
    assert rows["engine_R_flux_OUT_right_O1"]["signed_log2_index"] == 1
    assert controls["L_R_realization"]["opposite_signs"] is True
    assert "brickwork" in rows["engine_L_flux_IN_left_O1"]["construction"]
    assert "brickwork" in rows["engine_R_flux_OUT_right_O1"]["construction"]
    distinctness = controls["engine_calibration_distinctness"]
    assert distinctness["all_engine_rows_distinct_from_calibrations"] is True
    assert distinctness["self_rejection_gate_falsifier"]["would_self_reject"] is True
    assert distinctness["self_rejecting_matches"] == []
    assert rows["engine_L_index0_control"]["signed_log2_index"] == 0
    assert rows["engine_R_index0_control"]["signed_log2_index"] == 0
    assert controls["index0_control"]["lr_distinction_detected"] is False
    assert rows["gauge_engine_R_inserted_H"]["signed_log2_index"] == rows["engine_R_flux_OUT_right_O1"]["signed_log2_index"]
    assert controls["gauge_local_basis_invariance"]["rank_recomputed"] is True
    assert rows["falsifier_R_engine_forced_left_unitary"]["signed_log2_index"] == -1
    assert controls["real_unitary_falsifier_branch"]["opposite_signs_after_mutation"] is False


def test_ring_closure_rows_trivialize() -> None:
    packet = common.build_packet()
    assert packet["index_controls"]["ring_closure"]["automorphism_class_all_trivial"] is True
    assert packet["index_controls"]["ring_closure"]["finite_cut_rows_all_zero"] is True
    assert packet["index_controls"]["ring_closure"]["nonzero_ring_index_claimed"] is False
    for row in packet["ring_closure_rows"]:
        assert row["signed_log2_index"] == 0
        assert row["ring_triviality_boundary"]["automorphism_class_signed_log2_index"] == 0
        assert (
            row["ring_triviality_boundary"]["any_nonzero_ring_index_status"]
            == "circuit_presentation_or_phase_convention_relative_only_not_claimed_here"
        )


def test_dephased_classical_limit_uses_corrected_v0_floor() -> None:
    classical = common.build_packet()["classical_dephased_limit"]
    assert classical["phase_structure_reproduced"] is True
    assert classical["corrected_structural_floor"]["alternating_transient_scc_count"] == 352
    assert classical["corrected_structural_floor"]["paired_transient_scc_count"] == 128
    assert classical["period_rows_kept_as_implementation_checks"]["alternating_period_histogram"] == {"2": 576}
    assert classical["period_rows_kept_as_implementation_checks"]["paired_period_histogram"] == {"4": 576}


def test_smt_rows_bind_computed_values() -> None:
    packet = common.build_packet()
    assert packet["crossover_proofs"]["z3"]["verdict"] == "unsat"
    assert packet["crossover_proofs"]["z3"]["computed_real_unitary_flip_verdict"] == "sat"
    assert packet["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
    assert packet["crossover_proofs"]["cvc5"]["computed_real_unitary_flip_verdict"] == "sat"


def test_envelope_boundary_if_generated() -> None:
    if not RESULT.exists():
        return
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["no_builder_audit_verdict"] is True
    assert payload["builder_gates"]["no_builder_audit_verdict"] is True
    assert payload["object"]["automorphism_class_index_on_finite_ring"] == "trivial_by_amendment"
    assert payload["build_gates"]["L_R_opposite_indices"] is True
    assert payload["build_gates"]["engine_distinct_from_calibrations"] is True
    assert payload["build_gates"]["self_rejection_gate_falsifier_fires"] is True
    assert payload["build_gates"]["ring_closure_trivial"] is True
    assert payload["build_gates"]["classical_dephased_limit_reproduces_v0"] is True
