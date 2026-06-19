from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    spec = importlib.util.find_spec("fiber_augmented_cover_v1_common")
    assert spec is not None, "fiber_augmented_cover_v1_common module must exist"
    return importlib.import_module("fiber_augmented_cover_v1_common")


def test_nontrivial_cover_witness_gate_precedes_law_table() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_object()

    witness = obj["bundle_witness"]
    cover = obj["cover"]
    assert cover["fiber_phase_count_per_cell"] == 3
    assert obj["construction_status"] == "nontrivial_bundle_witness_passed"
    assert witness["loop_name"] == "committed_equatorial_loop"
    assert witness["directed_winding"] in {-1, 1}
    assert witness["euler_class_witness"] == witness["directed_winding"]
    assert witness["nontrivial_gate_passed"] is True
    assert any(int(shift) != 0 for shift in cover["base_lift_phase_shift_counts"])
    assert "b6_law_test" in obj
    assert obj["b6_law_test"]["witness_gate_required"] is True
    assert obj["b6_law_test"]["witness_gate_passed"] is True
    assert obj["b6_law_test"]["sample_total"] == cover["cover_state_count"]


def test_trivial_product_control_refuses_law_rows() -> None:
    common = _common()
    control = common.build_trivial_product_regression()

    assert control["construction_status"] == "construction_failed_trivial_bundle"
    assert control["bundle_witness"]["directed_winding"] == 0
    assert control["bundle_witness"]["nontrivial_gate_passed"] is False
    assert control["law_table_ran"] is False
    assert "b6_law_test" not in control
    assert control["negative_control_role"] == "v0_zero_shift_product_bundle_regression"
    assert control["at_chance_reproduced"] is True
    assert control["v0_law_reference"]["agreement_count"] == 60
    assert control["v0_law_reference"]["sample_total"] == 132


def test_faithfulness_sign_variants_and_chance_adjudication_are_present() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_object()

    faith = obj["faithfulness"]
    assert faith["axis0"]["projects_to_committed_axis0"] is True
    assert faith["axis3"]["source_backed_equivalent_adapter"] is True
    assert faith["axis3"]["predicate_mismatch_count"] == 0
    assert faith["axis6"]["projects_to_committed_axis6"] is True

    relation = obj["b6_law_test"]
    assert relation["law"] == "b6 = -b0*b3"
    assert relation["null_model"] == "independent_random_signs_match_product_law_with_p_0_5"
    assert relation["chance_thresholds"]["null_probability"] == 0.5
    assert relation["chance_thresholds"]["one_tailed_95_percent_min_agreements_for_n33"] == 23
    assert relation["binomial_p_two_sided"] >= 0.0
    assert relation["binomial_p_two_sided"] <= 1.0

    variants = obj["sign_variant_table"]
    assert len(variants) == 8
    assert {tuple(row[key] for key in ("s0", "s3", "s6")) for row in variants} == {
        (s0, s3, s6)
        for s0 in (-1, 1)
        for s3 in (-1, 1)
        for s6 in (-1, 1)
    }
    assert all("binomial_p_two_sided" in row for row in variants)
    assert all(row["classification"] in {"significant_above_chance", "at_chance", "significant_below_chance"} for row in variants)


def test_controls_and_builder_boundary() -> None:
    common = _common()
    obj = common.build_fiber_augmented_cover_object()

    controls = obj["controls"]
    assert controls["v0_trivial_bundle_regression"]["witness_zero"] is True
    assert controls["v0_trivial_bundle_regression"]["law_table_refused"] is True
    assert controls["v0_trivial_bundle_regression"]["v0_law_table_reproduced_at_chance"] is True
    assert controls["scrambled_control"]["ran"] is True
    assert controls["convention_flip_control"]["ran"] is True
    assert obj["classification"] == "scratch_diagnostic"
    assert obj["promotion_allowed"] is False
    assert obj["formal_admission_allowed"] is False
    assert obj["no_builder_audit_verdict"] is True


def test_validator_accepts_roundtrip_payload() -> None:
    common = _common()
    validator_spec = importlib.util.find_spec("validate_fiber_augmented_cover_v1")
    assert validator_spec is not None, "validate_fiber_augmented_cover_v1 module must exist"
    validator = importlib.import_module("validate_fiber_augmented_cover_v1")

    obj = common.build_fiber_augmented_cover_object()
    assert validator.validate_payload(obj) == []
