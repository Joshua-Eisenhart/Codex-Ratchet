#!/usr/bin/env python3
"""Focused tests for ring_checkerboard_qca_v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PACKET = Path(__file__).resolve().parents[1]
RESULT = PACKET / "results" / "ring_checkerboard_qca_v1_envelope_results.json"
sys.path.insert(0, str(PACKET))

import ring_checkerboard_qca_v1_common as common  # noqa: E402


def test_index_calibrations_and_lr_rows_are_exact() -> None:
    packet = common.build_packet()
    rows = {row["rule_id"]: row for row in packet["index_table"]}
    assert rows["calibration_right_shift"]["signed_log2_index"] == 1
    assert rows["calibration_right_shift"]["standard_index_ratio"] == "2/1"
    assert rows["calibration_left_shift"]["signed_log2_index"] == -1
    assert rows["calibration_left_shift"]["standard_index_ratio"] == "1/2"
    assert rows["calibration_nonshifting_onsite"]["signed_log2_index"] == 0
    assert rows["engine_L_flux_in_left"]["signed_log2_index"] == -1
    assert rows["engine_R_flux_out_right"]["signed_log2_index"] == 1
    assert rows["engine_L_index0_control"]["signed_log2_index"] == 0
    assert rows["engine_R_index0_control"]["signed_log2_index"] == 0
    assert rows["gauge_reparameterized_right_shift"]["signed_log2_index"] == rows["calibration_right_shift"]["signed_log2_index"]


def test_index_controls_and_falsifier_branch_pass() -> None:
    controls = common.build_packet()["index_controls"]
    assert controls["all_pass"] is True
    assert controls["L_R_realization"]["opposite_signs"] is True
    assert controls["L_R_realization"]["expectation_2_status"] == "earned"
    assert controls["index0_control"]["lr_distinction_detected"] is False
    assert controls["gauge_local_basis_invariance"]["same_index"] is True
    assert controls["falsifier_branch"]["reachable"] is True
    assert controls["falsifier_branch"]["expectation_2_status"] == "killed_as_expected"


def test_locality_comparison_uses_matched_state_counts_and_differs() -> None:
    locality = common.build_packet()["locality_comparison"]
    assert locality["matched_state_count"] == 6400
    assert locality["terminal_or_orbit_structure_differs"] is True
    assert locality["order_shuffle_changes_local_structure"] is True
    assert locality["local_brickwork"]["signature"]["terminal_class_count"] == 1600
    assert locality["global_v3_style"]["signature"]["terminal_class_count"] == 160
    assert locality["local_brickwork"]["signature"]["period_histogram"] == {"4": 6400}
    assert locality["global_v3_style"]["signature"]["period_histogram"] == {"40": 6400}


def test_classical_limit_reproduces_committed_v0_phase_structure() -> None:
    classical = common.build_packet()["classical_limit"]
    assert classical["v0_verdict"] == "PASS_DISTINGUISHABLE_CLASSICAL_FLOOR"
    assert classical["phase_structure_reproduced"] is True
    assert classical["alternating_period_histogram"] == {"2": 576}
    assert classical["paired_period_histogram"] == {"4": 576}


def test_typed_flux_and_smt_rows_are_bound() -> None:
    packet = common.build_packet()
    typed = {row["rule_id"]: row for row in packet["typed_information_flux_rows"]}
    assert typed["engine_L_flux_in_left"]["information_flux_qubits_per_step"] == -1
    assert typed["engine_R_flux_out_right"]["information_flux_qubits_per_step"] == 1
    assert typed["engine_L_index0_control"]["von_neumann_entropy_flux_nats_exact"] == "0"
    assert typed["engine_R_index0_control"]["von_neumann_entropy_flux_nats_exact"] == "0"
    assert packet["crossover_proofs"]["z3"]["verdict"] == "unsat"
    assert packet["crossover_proofs"]["z3"]["computed_perturbation_flip_verdict"] == "sat"
    assert packet["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
    assert packet["crossover_proofs"]["cvc5"]["computed_perturbation_flip_verdict"] == "sat"


def test_envelope_boundary_if_generated() -> None:
    if not RESULT.exists():
        return
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["no_builder_audit_verdict"] is True
    assert payload["builder_gates"]["no_builder_audit_verdict"] is True
    assert payload["object"]["index_definition_status"] == "standard_math_alignment_not_owner_source"
    assert payload["build_gates"]["L_R_opposite_indices"] is True
    assert payload["build_gates"]["index0_no_LR_distinction"] is True
    assert payload["build_gates"]["locality_comparison_differs"] is True
