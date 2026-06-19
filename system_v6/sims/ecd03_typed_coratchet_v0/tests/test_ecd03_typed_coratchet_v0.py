#!/usr/bin/env python3
"""Tests for the ECD.03 typed co-ratchet discriminator."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path


SIM_DIR = Path(__file__).resolve().parents[1]
ROOT = SIM_DIR.parents[2]
PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"

if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


def _common():
    return importlib.import_module("ecd03_typed_coratchet_v0_common")


def _validator():
    return importlib.import_module("validate_ecd03_typed_coratchet_v0")


def test_two_sided_equal_information_reachability_sets_are_computed() -> None:
    common = _common()
    obj = common.build_typed_coratchet_object()

    assert obj["all_pass"] is True
    assert obj["authority"]["two_sided_search_rule"] is True
    assert obj["authority"]["equal_information_rule"] is True
    assert obj["authority"]["fair_metric_no_trivial_injective_readouts"] is True
    assert obj["availability_nontriviality_gate"]["status"] == "pass"
    assert obj["qit_side"]["searched"] is True
    assert obj["baseline_side"]["searched"] is True
    assert obj["qit_side"]["shared_environment_hash"] == obj["baseline_side"]["shared_environment_hash"]
    assert obj["qit_side"]["nominal_schedule_count"] > 0
    assert obj["baseline_side"]["nominal_schedule_count"] > 0
    assert obj["discriminator"]["qit_only_sequences_count"] == len(obj["discriminator"]["qit_only_sequences"])
    assert obj["discriminator"]["baseline_only_sequences_count"] == len(obj["discriminator"]["baseline_only_sequences"])
    assert obj["discriminator"]["verdict"] in {"SURVIVES_v0", "DIES_v0", "TIE_v0"}
    assert obj["discriminator"]["either_outcome_valid"] is True


def test_controls_cover_order_sensitivity_and_label_free_fingerprints() -> None:
    common = _common()
    obj = common.build_typed_coratchet_object()
    controls = obj["controls"]

    assert controls["permuted_ops_regression"]["availability_moved"] is True
    assert controls["order_blind_collapse"]["collapses_schedule_order"] is True
    assert controls["order_blind_collapse"]["collapsed_sequence_count"] < controls["order_blind_collapse"]["full_sequence_count"]
    assert controls["order_blind_collapse"]["metric_used_for_discriminator"] is False
    assert controls["dropped_half_schedule_sensitivity"]["qit_dropped_half"]["nominal_schedule_count"] > 0
    assert controls["dropped_half_schedule_sensitivity"]["baseline_dropped_half"]["nominal_schedule_count"] > 0
    assert controls["no_identity_leak"]["status"] == "pass"
    assert controls["no_identity_leak"]["sequence_fingerprints_label_free"] is True


def test_void_carrier_is_refused() -> None:
    common = _common()
    obj = common.build_typed_coratchet_object(void_carrier=True)

    assert obj["all_pass"] is False
    assert obj["availability_nontriviality_gate"]["status"] == "void_refused"
    assert obj["discriminator"]["verdict"] == "VOID_v0"


def test_generated_packet_commands_and_validator() -> None:
    subprocess.run([PY, str(SIM_DIR / "ecd03_typed_coratchet_v0.py")], cwd=ROOT, check=True)
    subprocess.run([PY, str(SIM_DIR / "ecd03_typed_coratchet_v0_envelope.py")], cwd=ROOT, check=True)
    subprocess.run([PY, str(SIM_DIR / "validate_ecd03_typed_coratchet_v0.py")], cwd=ROOT, check=True)

    validator = json.loads((SIM_DIR / "results" / "ecd03_typed_coratchet_v0_validator_results.json").read_text())
    assert validator["ok"] is True


def test_validator_delegates_to_builder_audit_boundary_from_birth() -> None:
    common = _common()
    validator = _validator()
    obj = common.build_typed_coratchet_object()
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
