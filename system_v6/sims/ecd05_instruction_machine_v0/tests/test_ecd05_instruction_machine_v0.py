#!/usr/bin/env python3
"""Tests for ECD.05 instruction-machine discriminator."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


def _common():
    return importlib.import_module("ecd05_instruction_machine_v0_common")


def _validator():
    return importlib.import_module("validate_ecd05_instruction_machine_v0")


def test_two_sided_searches_are_complete_and_margin_is_computed() -> None:
    common = _common()
    obj = common.build_instruction_machine_object()

    assert obj["program_space_pin"]["program_length"] == common.PROGRAM_LENGTH
    assert obj["qit_side"]["nominal_program_count"] == common.comb(64, common.PROGRAM_LENGTH)
    assert obj["baseline_side"]["nominal_program_count"] == 64 ** common.PROGRAM_LENGTH
    assert obj["baseline_side"]["complete_table_materialized"] is True
    assert obj["discriminator"]["qit_max"] == obj["qit_side"]["computed_distinct_channel_count"]
    assert obj["discriminator"]["baseline_max"] == obj["baseline_side"]["computed_distinct_channel_count"]
    assert (
        obj["discriminator"]["qit_minus_baseline_margin"]
        == obj["discriminator"]["qit_max"] - obj["discriminator"]["baseline_max"]
    )
    assert obj["discriminator"]["verdict"] in {"SURVIVES_v0", "DIES_v0", "TIE_v0"}


def test_controls_and_fences_are_present() -> None:
    common = _common()
    obj = common.build_instruction_machine_object()

    assert obj["controls"]["commuting_order_blind_collapse"]["control_count_lte_qit_channels"] is True
    assert isinstance(
        obj["controls"]["commuting_order_blind_collapse"]["extra_order_sensitive_channels_over_component_multisets"],
        int,
    )
    assert obj["controls"]["dropped_half_program_space_sensitivity"]["qit_dropped_half"]["nominal_program_count"] == common.comb(32, common.PROGRAM_LENGTH)
    assert obj["controls"]["dropped_half_program_space_sensitivity"]["baseline_dropped_half"]["nominal_program_count"] == 32 ** common.PROGRAM_LENGTH
    assert obj["controls"]["no_identity_leak"]["status"] == "pass"
    assert obj["controls"]["no_identity_leak"]["fingerprints_read_slot_labels"] is False
    assert obj["controls"]["scrambled_schedule_regression"]["scrambled_differs_from_pinned"] is True
    assert obj["realization_relativity_fence"]["same_pinned_realization_for_all_programs"] is True
    assert obj["realization_relativity_fence"]["source_admitted_substage_convention"] is False
    assert "Turing-complete machine" in obj["disallowed_claims"]


def test_generated_result_validates_when_present() -> None:
    common = _common()
    validator = _validator()
    if not common.RESULT_PATH.exists() or not common.ENVELOPE_PATH.exists():
        return
    payload = json.loads(common.RESULT_PATH.read_text(encoding="utf-8"))
    assert validator.validate_payload(payload) == []


def test_validator_delegates_to_builder_audit_boundary_from_birth() -> None:
    common = _common()
    validator = _validator()
    obj = common.build_instruction_machine_object()
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    common.write_json(common.RESULT_PATH, obj)
    common.write_json(common.ENVELOPE_PATH, common.build_envelope(obj))

    audit_path = SIM_DIR / "audit_verdict.md"
    original = audit_path.read_text(encoding="utf-8") if audit_path.exists() else None
    try:
        audit_path.write_text("# Builder-authored verdict\n\nThis should fail the independent boundary.\n", encoding="utf-8")
        errors = validator.validate_payload(obj)
        assert any("audit_verdict.md exists" in error for error in errors)
    finally:
        if original is None:
            audit_path.unlink(missing_ok=True)
        else:
            audit_path.write_text(original, encoding="utf-8")
    assert builder_audit_boundary_ok(audit_path)
