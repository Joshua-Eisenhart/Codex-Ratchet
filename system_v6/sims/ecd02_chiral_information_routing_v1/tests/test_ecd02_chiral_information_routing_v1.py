#!/usr/bin/env python3
"""Focused tests for ecd02_chiral_information_routing_v1."""

from __future__ import annotations

import json
from pathlib import Path
import sys


PACKET = Path(__file__).resolve().parents[1]
RESULT = PACKET / "results" / "ecd02_chiral_information_routing_v1_envelope_results.json"
sys.path.insert(0, str(PACKET))

import ecd02_chiral_information_routing_v1_common as common  # noqa: E402


def test_real_mi_and_flux_rows_are_computed_from_dynamics() -> None:
    core = common.build_core_result()
    discovery = core["discovery"]
    assert discovery["computed_flux_by_engine"]["R_engine"] == 1.0
    assert discovery["computed_flux_by_engine"]["L_engine"] == -1.0
    assert discovery["qit_min_signal_mi_bits"] > 0.1
    mi_rows = discovery["mutual_information_rows"]
    assert mi_rows["R_engine"]["left_injection"]["I_source_left_readout_bits"] > 0.1
    assert mi_rows["R_engine"]["left_injection"]["I_source_right_readout_bits"] == 0.0


def test_joint_state_and_projective_entropy_rows_exist() -> None:
    core = common.build_core_result()
    row = core["discovery"]["distribution_rows"]["R_engine"]["left_injection"]["joint_state_test"]
    assert row["initial_source_memory_entropy_bits"] == 2.0
    assert row["final_projective_left_right_readout_entropy_bits"] >= 1.9
    assert "P(source_bit, left_projective_readout, right_projective_readout)" in row["joint_state_shape"]


def test_strongest_szilard_baseline_kills_candidate() -> None:
    core = common.build_core_result()
    assert core["strongest_szilard_baseline"]["searched_policy_count"] == 36
    assert core["strongest_szilard_baseline"]["strongest_abs_directed_current"] >= core["discovery"]["qit_abs_directed_current"]
    assert core["verdict"]["qit_engine_pass_computed"] is True
    assert core["verdict"]["strongest_szilard_baseline_fail_computed"] is False
    assert core["verdict"]["registry_contract_pass"] is False
    assert core["verdict"]["ecd02_status"] == "DIES"


def test_controls_and_no_identity_leak() -> None:
    core = common.build_core_result()
    assert core["controls"]["mirror_control_flips_computed_flux_sign"] is True
    assert core["controls"]["scrambled_schedule_control_kills_signal"] is True
    mi_dump = json.dumps(core["discovery"]["mutual_information_rows"]).lower()
    assert "signed_index" not in mi_dump
    assert "chirality" not in mi_dump


def test_smt_death_boundary() -> None:
    core = common.build_core_result()
    assert core["crossover_proofs"]["z3"]["verdict"] == "unsat"
    assert core["crossover_proofs"]["cvc5"]["verdict"] == "unsat"


def test_envelope_if_generated() -> None:
    if not RESULT.exists():
        return
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["claim_ceiling"] == "capability_discriminator_only"
    assert payload["all_pass"] is True
    assert payload["verdict"]["ecd02_status"] == "DIES"
