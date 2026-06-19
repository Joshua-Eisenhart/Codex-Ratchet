from __future__ import annotations

import importlib
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))


def _common():
    return importlib.import_module("topology_parity_guard_v2_common")


def test_reference_gate_recovers_profiles_before_cover_rows() -> None:
    common = _common()
    refs = common.run_reference_gate()

    assert refs["reference_gate_passed"] is True
    assert refs["explicit_s3_like"]["homology"]["betti_b0_b1_b2_b3"] == [1, 0, 0, 1]
    assert refs["explicit_s3_like"]["homology"]["torsion"] == {"H0": [], "H1": [], "H2": [], "H3": []}
    assert refs["explicit_s2xs1"]["homology"]["betti_b0_b1_b2_b3"] == [1, 1, 1, 1]
    assert refs["explicit_s2xs1"]["homology"]["torsion"] == {"H0": [], "H1": [], "H2": [], "H3": []}


def test_consumes_hash_pinned_v2_complexes_without_builder_betti() -> None:
    common = _common()
    payload = common.build_topology_parity_guard_v2_object()
    source = payload["source_complex_lock"]

    assert source["builder_result_commit"] == "cc2f61b2a"
    assert source["builder_betti_computed"] is False
    assert source["consumer_boundary"]["builder_consumer_separation"] is True
    assert source["base"]["chain_sha256"] == "9d6655a51782305f80409cce0bd42a57329fb14ea19b05c32b95ec36016b883c"
    assert source["base"]["cell_counts"] == {"C0": 33, "C1": 92, "C2": 61}
    assert source["total"]["chain_sha256"] == "38e57e928d722046eb0b734ff76d7a636c05e0f292ca59f97a3a3e0588d12a5c"
    assert source["total"]["cell_counts"] == {"C0": 99, "C1": 375, "C2": 459, "C3": 183}


def test_committed_total_homology_is_torsion_aware_and_adjudicates_parity() -> None:
    common = _common()
    payload = common.build_topology_parity_guard_v2_object()
    total = payload["complexes"]["committed_v2_total_space"]
    adjudication = payload["parity_adjudication"]

    assert total["homology"]["betti_b0_b1_b2_b3"] == [1, 1, 1, 1]
    assert total["homology"]["torsion"] == {"H0": [], "H1": [], "H2": [], "H3": []}
    assert total["d_squared_zero"] is True
    assert adjudication["status"] == "FAILED"
    assert adjudication["expected_s3_like_betti"] == [1, 0, 0, 1]
    assert adjudication["computed_total_betti"] == [1, 1, 1, 1]
    assert adjudication["finding_kind"] == "computed_mismatch_against_cover_construction"


def test_zero_shift_gap_and_controls_are_reported() -> None:
    common = _common()
    payload = common.build_topology_parity_guard_v2_object()

    assert payload["complexes"]["zero_shift_product_cover"]["status"] == "INSUFFICIENT"
    assert payload["complexes"]["zero_shift_product_cover"]["gap"] == "v2_committed_zero_shift_chain_complex_not_emitted"
    assert payload["controls"]["torsion_trap_degree_2"]["pass"] is True
    assert payload["controls"]["torsion_trap_degree_2"]["homology"]["torsion"]["H1"] == [2]
    assert payload["controls"]["wrong_gluing_control"]["status"] == "INSUFFICIENT"


def test_validator_accepts_payload_and_g2a_boundary() -> None:
    common = _common()
    validator = importlib.import_module("validate_topology_parity_guard_v2")

    payload = common.build_topology_parity_guard_v2_object()
    assert validator.validate_payload(payload) == []
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["no_builder_audit_verdict"] is True
    assert payload["no_builder_audit_verdict_envelope_gate"] is True
