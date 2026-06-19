#!/usr/bin/env python3
"""Focused tests for ecd02_chiral_information_routing_v0."""

from __future__ import annotations

import json
from pathlib import Path
import sys


PACKET = Path(__file__).resolve().parents[1]
RESULT = PACKET / "results" / "ecd02_chiral_information_routing_v0_envelope_results.json"
sys.path.insert(0, str(PACKET))

import ecd02_chiral_information_routing_v0_common as common  # noqa: E402


def test_index_sign_predicts_endpoint_routing() -> None:
    core = common.build_core_result()
    assert core["qca_v3_indices_consumed"]["R"] == 1
    assert core["qca_v3_indices_consumed"]["L"] == -1
    asym = core["routing"]["routing_asymmetry"]
    assert asym["R_engine_left_to_right_minus_right_to_left"] == 1.0
    assert asym["L_engine_left_to_right_minus_right_to_left"] == -1.0
    assert core["controls"]["index_sign_predicts_routing_direction"] is True


def test_szilard_and_index0_fail_directional_routing() -> None:
    core = common.build_core_result()
    assert core["routing"]["szilard_baseline"]["passes_capability"] is False
    assert core["routing"]["szilard_baseline"]["routing_asymmetry"] == 0.0
    assert core["routing"]["index0_control"]["symmetric"] is True
    assert core["routing"]["index0_control"]["routing_asymmetry"] == 0.0


def test_diode_and_mirror_rows() -> None:
    routing = common.build_core_result()["routing"]
    assert routing["diode_row"]["diode_pass"] is True
    assert routing["diode_row"]["passes_L_to_R_bits"] == 1.0
    assert routing["diode_row"]["attenuation_R_to_L"] == 1.0
    assert routing["mirror_diode_row"]["mirror_pass"] is True
    assert routing["mirror_diode_row"]["passes_R_to_L_bits"] == 1.0


def test_smt_controls() -> None:
    core = common.build_core_result()
    assert core["crossover_proofs"]["z3"]["verdict"] == "unsat"
    assert core["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
    assert core["crossover_proofs"]["z3"]["forced_R_left_falsifier_verdict"] == "unsat"
    assert core["crossover_proofs"]["cvc5"]["forced_R_left_falsifier_verdict"] == "unsat"


def test_envelope_if_generated() -> None:
    if not RESULT.exists():
        return
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["claim_ceiling"] == "capability_discriminator_only"
    assert payload["all_pass"] is True
    assert payload["build_gates"]["szilard_baseline_fails"] is True
    assert payload["build_gates"]["falsifier_reachable"] is True

