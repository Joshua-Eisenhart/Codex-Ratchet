from __future__ import annotations

import importlib
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    return importlib.import_module("topology_parity_guard_v3_common")


def test_reference_gate_includes_lens_space_l31_and_torsion_trap() -> None:
    common = _common()
    refs = common.run_reference_gate()
    controls = common.run_controls()

    assert refs["reference_gate_passed"] is True
    assert refs["explicit_s3"]["homology"]["betti_b0_b1_b2_b3"] == [1, 0, 0, 1]
    assert refs["explicit_s3"]["homology"]["torsion"] == {"H0": [], "H1": [], "H2": [], "H3": []}
    assert refs["explicit_s2xs1"]["homology"]["betti_b0_b1_b2_b3"] == [1, 1, 1, 1]
    assert refs["explicit_s2xs1"]["homology"]["torsion"] == {"H0": [], "H1": [], "H2": [], "H3": []}
    assert refs["explicit_lens_space_l31"]["homology"]["betti_b0_b1_b2_b3"] == [1, 0, 0, 1]
    assert refs["explicit_lens_space_l31"]["homology"]["torsion"]["H1"] == [3]
    assert controls["degree_2_torsion_trap"]["pass"] is True
    assert controls["degree_2_torsion_trap"]["homology"]["torsion"]["H1"] == [2]


def test_consumes_all_four_v2_1_complexes_by_hash_without_builder_betti() -> None:
    common = _common()
    payload = common.build_topology_parity_guard_v3_object()
    lock = payload["source_complex_lock"]

    assert lock["hash_verification_passed"] is True
    assert lock["builder_betti_computed"] is False
    assert lock["builder_homology_computed"] is False
    assert lock["expected_chain_hashes"] == common.EXPECTED_CHAIN_HASHES
    assert set(payload["complexes"]) == set(common.COMPLEX_ORDER)
    assert payload["complexes"]["v2_1_shifted_degree_one_mod3"]["source_chain_sha256"] == (
        "6afe8ea8f778ae9f470354a641a8989e40868df5efa8c9792fcdd2eb25c3c75a"
    )


def test_boundary_matrix_only_separability_finds_two_pure_complexes() -> None:
    common = _common()
    payload = common.build_topology_parity_guard_v3_object()
    row = payload["math_content_separability"]

    assert row["boundary_matrix_only_distinct_hash_count"] == 2
    assert row["expected_distinct_pure_complexes"] == 2
    assert row["passed"] is True
    assert row["control_complexes_mutually_isomorphic_expected"] is True
    control_hashes = {
        row["by_complex"]["zero_shift_product_control"],
        row["by_complex"]["wrong_gluing_generator_not_threaded_control"],
        row["by_complex"]["old_v2_regression_coboundary_control"],
    }
    assert len(control_hashes) == 1
    assert row["by_complex"]["v2_1_shifted_degree_one_mod3"] not in control_hashes


def test_shifted_lens_profile_and_controls_product_profile_adjudicate_reading_a() -> None:
    common = _common()
    payload = common.build_topology_parity_guard_v3_object()
    shifted = payload["complexes"]["v2_1_shifted_degree_one_mod3"]

    assert shifted["homology"]["betti_b0_b1_b2_b3"] == [1, 0, 0, 1]
    assert shifted["homology"]["torsion"]["H1"] == [3]
    for complex_id in (
        "zero_shift_product_control",
        "wrong_gluing_generator_not_threaded_control",
        "old_v2_regression_coboundary_control",
    ):
        row = payload["complexes"][complex_id]
        assert row["homology"]["betti_b0_b1_b2_b3"] == [1, 1, 1, 1]
        assert row["homology"]["torsion"] == {"H0": [], "H1": [], "H2": [], "H3": []}
    assert payload["adjudication"]["winner"] == "READING_A_REPAIRED_WINS"
    assert payload["adjudication"]["certificate_status"] == "FINITE_SECOND_CERTIFICATE_EARNED_BY_TORSION_GUARD_DATA"


def test_validator_accepts_payload_and_g2a_boundary_from_birth() -> None:
    common = _common()
    validator = importlib.import_module("validate_topology_parity_guard_v3")

    payload = common.build_topology_parity_guard_v3_object()
    assert validator.validate_payload(payload) == []
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["builder_gates"]["g2a_boundary_from_birth"] is True
    assert payload["no_builder_audit_verdict"] is True
