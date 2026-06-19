from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    spec = importlib.util.find_spec("fiber_augmented_cover_v2_1_common")
    assert spec is not None, "fiber_augmented_cover_v2_1_common module must exist"
    return importlib.import_module("fiber_augmented_cover_v2_1_common")


def test_v2_base_is_hash_locked_and_repin_is_not_old_construction() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_v2_1_object()

    assert obj["classification"] == "scratch_diagnostic"
    assert obj["promotion_allowed"] is False
    assert obj["formal_admission_allowed"] is False
    assert obj["claim_ceiling"].startswith("axis_readout_candidate_only")
    assert obj["cellular_base"]["v2_base_unchanged_by_hash"] is True
    assert obj["cellular_base"]["chain_sha256"] == common.EXPECTED_V2_BASE_CHAIN_SHA256
    assert obj["cellular_base"]["cell_counts"] == {"C0": 33, "C1": 92, "C2": 61}
    assert obj["central_math_adjudication"]["not_a_reinterpretation_of_old_construction"] is True
    assert obj["central_math_adjudication"]["v2_1_seam_steps"] == [1, 0, 0, 0]
    assert obj["central_math_adjudication"]["v2_1_mod_fiber_holonomy"] == 1
    assert obj["central_math_adjudication"]["v2_1_integer_lift_sum"] == 1


def test_guard_v3_complex_family_and_controls_are_hash_pinned() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_v2_1_object()
    family = obj["complex_family"]

    assert set(family["complex_order"]) == {
        "v2_1_shifted_degree_one_mod3",
        "zero_shift_product_control",
        "wrong_gluing_generator_not_threaded_control",
        "old_v2_regression_coboundary_control",
    }
    assert family["all_d_squared_zero"] is True
    assert family["betti_computed"] is False
    assert family["homology_computed"] is False

    shifted = family["complexes"]["v2_1_shifted_degree_one_mod3"]
    assert shifted["integer_lift_and_mod_holonomy"]["mod_fiber_holonomy"] == 1
    assert shifted["integer_lift_and_mod_holonomy"]["integer_lift_sum"] == 1
    assert shifted["clutching"]["attaches_fiber_cycle_with_coefficient"] == 3
    assert shifted["clutching"]["threading_gate_passed"] is True
    assert shifted["chain_checks"]["d_squared_zero"] is True
    assert shifted["chain_sha256"]

    zero = family["complexes"]["zero_shift_product_control"]
    assert zero["integer_lift_and_mod_holonomy"]["mod_fiber_holonomy"] == 0
    assert zero["chain_checks"]["d_squared_zero"] is True

    wrong = family["complexes"]["wrong_gluing_generator_not_threaded_control"]
    assert wrong["integer_lift_and_mod_holonomy"]["mod_fiber_holonomy"] == 1
    assert wrong["clutching"]["threading_gate_passed"] is False
    assert wrong["chain_checks"]["d_squared_zero"] is True

    old = family["complexes"]["old_v2_regression_coboundary_control"]
    assert old["integer_lift_and_mod_holonomy"]["integer_lift_sum"] == 3
    assert old["integer_lift_and_mod_holonomy"]["mod_fiber_holonomy"] == 0
    assert old["integer_lift_and_mod_holonomy"]["old_integer_lift_winding_if_divisible"] == 1
    assert obj["controls"]["v2_regression_old_shifts"]["finite_triviality_reproduced"] is True


def test_law_table_faithfulness_and_smt_rows_recompute_on_third_construction() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_v2_1_object()

    law = obj["b6_law_test"]
    assert law["law"] == "b6 = -b0*b3"
    assert law["construction_row"] == "third_construction_v2_1_mod3_repin"
    assert law["sample_total"] == 99
    assert law["witness_gate_passed"] is True
    assert law["law_test_status"] in {
        "holds_on_decisive_repin_cover",
        "fails_on_decisive_repin_cover",
        "inconclusive_no_nonneutral_rows",
    }
    assert len(obj["sign_variant_table"]) == 8
    assert obj["faithfulness"]["axis0"]["projects_to_committed_axis0"] is True
    assert obj["faithfulness"]["axis3"]["source_backed_equivalent_adapter"] is True
    assert obj["faithfulness"]["axis3"]["predicate_mismatch_count"] == 0
    assert obj["faithfulness"]["axis6"]["projects_to_committed_axis6"] is True
    assert obj["controls"]["scrambled_control"]["ran"] is True
    assert obj["controls"]["convention_flip_control"]["ran"] is True
    assert all(row["verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in obj["smt_rows"].values())


def test_validator_accepts_roundtrip_payload_and_g2a_boundary() -> None:
    common = _common()
    validator_spec = importlib.util.find_spec("validate_fiber_augmented_cover_v2_1")
    assert validator_spec is not None, "validate_fiber_augmented_cover_v2_1 module must exist"
    validator = importlib.import_module("validate_fiber_augmented_cover_v2_1")

    obj = common.build_fiber_augmented_cover_v2_1_object()
    assert validator.validate_payload(obj) == []
    assert obj["betti_computed"] is False
    assert obj["homology_computed"] is False
    assert "betti" not in obj
    assert obj["no_builder_audit_verdict"] is True
    assert obj["no_builder_audit_verdict_envelope_gate"] is True
