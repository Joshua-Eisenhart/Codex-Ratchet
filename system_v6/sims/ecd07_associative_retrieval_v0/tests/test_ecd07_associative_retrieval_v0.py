from __future__ import annotations

import ecd07_associative_retrieval_v0_common as common
import validate_ecd07_associative_retrieval_v0 as validator


def test_core_result_gates() -> None:
    result = common.build_associative_retrieval_object()
    assert result["all_pass"] is True
    assert result["storage_nontriviality_gate"]["status"] == "passed"
    assert result["information_parity_gate"]["status"] == "information_parity_passed"
    assert result["discriminator"]["verdict"] in {"SURVIVES_v0", "DIES_TIE_v0", "DIES_CLASSICAL_STRONGER_v0"}


def test_full_curve_and_capacity_present() -> None:
    result = common.build_associative_retrieval_object()
    assert set(result["discriminator"]["qit_best"]["accuracy_curve"]) == {str(level) for level in common.CORRUPTION_LEVELS}
    assert set(result["discriminator"]["classical_best"]["accuracy_curve"]) == {str(level) for level in common.CORRUPTION_LEVELS}
    assert len(result["capacity"]["rows"]) == len(common.CAPACITY_PATTERN_COUNTS)


def test_identity_leak_fields_present() -> None:
    result = common.build_associative_retrieval_object()
    leak = result["controls"]["no_identity_leak"]
    assert leak["status"] == "pass"
    assert "identity_leak_detected" in leak
    assert "identity_leak_excluded_best_accuracy" in leak
    assert leak["identity_leak_exclusion_rule"]


def test_validator_on_disk_payload() -> None:
    if common.RESULT_PATH.exists() and common.ENVELOPE_PATH.exists():
        assert validator.validate_payload(common.load_json(common.RESULT_PATH)) == []
