from fractions import Fraction

import pytest

from six_bit_two_trigram_szilard_fixture_v0 import (
    build_payload,
    compute_record_costs,
    enumerate_carrier,
    landauer_floor_ln2,
    szilard_order_controls,
)


def test_carrier_is_two_trigrams_over_64_states() -> None:
    states = enumerate_carrier()

    assert len(states) == 64
    assert states[0]["bits"] == (0, 0, 0, 0, 0, 0)
    assert states[0]["lower_trigram"] == 0
    assert states[0]["upper_trigram"] == 0
    assert states[-1]["bits"] == (1, 1, 1, 1, 1, 1)
    assert states[-1]["lower_trigram"] == 7
    assert states[-1]["upper_trigram"] == 7
    assert {(state["lower_trigram"], state["upper_trigram"]) for state in states} == {
        (lower, upper) for lower in range(8) for upper in range(8)
    }


def test_structured_full_state_record_cost_matches_unstructured_register() -> None:
    costs = compute_record_costs()

    assert costs["unstructured_6bit_state_record"]["bits"] == Fraction(6, 1)
    assert costs["two_trigram_full_pair_record"]["bits"] == Fraction(6, 1)
    assert costs["effect_of_3_plus_3_split"]["full_state_delta_bits"] == Fraction(0, 1)
    assert costs["effect_of_3_plus_3_split"]["full_state_verdict"] == "no_change_for_uniform_full_state_record"


def test_structured_partial_records_cost_less_because_the_variable_is_coarser() -> None:
    costs = compute_record_costs()

    assert costs["lower_trigram_only_record"]["bits"] == Fraction(3, 1)
    assert costs["upper_trigram_only_record"]["bits"] == Fraction(3, 1)
    assert costs["parity_pair_record"]["bits"] == Fraction(2, 1)
    assert costs["effect_of_3_plus_3_split"]["partial_record_boundary"] == (
        "lower/upper trigram-only records are cheaper because they erase a coarser variable, "
        "not because the full 64-state carrier became cheaper"
    )


def test_landauer_floor_scales_with_record_bits_on_this_carrier() -> None:
    assert landauer_floor_ln2(Fraction(6, 1)) == {
        "ln2_coeff": Fraction(6, 1),
        "nats_label": "6 * ln(2)",
    }
    assert landauer_floor_ln2(Fraction(3, 1))["nats_label"] == "3 * ln(2)"


def test_szilard_order_controls_keep_measure_feedback_erase_precedence() -> None:
    controls = szilard_order_controls()

    assert controls["canonical_measure_feedback_erase"]["verdict"] == "sat"
    assert controls["feedback_before_measure"]["verdict"] == "unsat"
    assert controls["erase_before_feedback"]["verdict"] == "unsat"
    assert controls["no_measurement_control"]["work_credit_ln2_coeff"] == Fraction(0, 1)


def test_payload_keeps_fixture_boundary_and_contract_fields() -> None:
    payload = build_payload()

    assert payload["sim_id"] == "six_bit_two_trigram_szilard_fixture_v0"
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["row_classification"] == "classical_baseline"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["all_pass"] is True
    assert payload["carrier_summary"]["state_count"] == 64
    assert payload["record_costs"]["effect_of_3_plus_3_split"]["full_state_delta_bits"] == {
        "num": 0,
        "den": 1,
        "string": "0/1",
        "float": 0.0,
    }
    assert "TOOL_MANIFEST" in payload
    assert "TOOL_INTEGRATION_DEPTH" in payload
    assert payload["claim_boundary"]["no_physics_bridge"] is True
    assert payload["claim_boundary"]["no_64_claims"] is True


def test_payload_is_json_serializable() -> None:
    import json

    json.dumps(build_payload(), sort_keys=True)
