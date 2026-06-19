#!/usr/bin/env python3
"""Tests for ecd04_record_conditioned_navigation_v0."""

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
    return importlib.import_module("ecd04_record_conditioned_navigation_v0_common")


def _validator():
    return importlib.import_module("validate_ecd04_record_conditioned_navigation_v0")


def test_two_sided_equal_information_search_and_metric() -> None:
    common = _common()
    obj = common.build_navigation_object()
    assert obj["authority"]["two_sided_search_rule"] is True
    assert obj["authority"]["equal_information_rule"] is True
    assert obj["witness_gates"]["basin_nontriviality"]["status"] == "pass"
    assert obj["witness_gates"]["information_parity"]["status"] == "pass"
    assert obj["qit_side"]["searched"] is True
    assert obj["baseline_side"]["searched"] is True
    assert obj["qit_side"]["best"]["target_success_rate"] == 1.0
    assert obj["baseline_side"]["best"]["target_success_rate"] == 1.0
    assert obj["metric_pin"]["does_not_reward_failure"] is True
    assert obj["discriminator"]["verdict"] in {"SURVIVES_v0", "DIES_v0", "TIE_v0"}


def test_controls_have_teeth_and_identity_leak_is_excluded() -> None:
    common = _common()
    obj = common.build_navigation_object()
    controls = obj["controls"]
    assert controls["record_erasure_regression"]["degraded"] is True
    assert controls["scrambled_records"]["degraded"] is True
    assert controls["order_blind_collapse"]["primary_eligible"] is False
    assert set(controls["dropped_half_both_sides"]) == {"first_half", "second_half"}
    assert controls["no_identity_leak"]["identity_leak_detected"] is True
    assert controls["no_identity_leak"]["identity_leak_excluded_best_accuracy"] < 1.0


def test_generated_packet_commands_and_validator() -> None:
    subprocess.run([PY, str(SIM_DIR / "ecd04_record_conditioned_navigation_v0.py")], cwd=ROOT, check=True)
    subprocess.run([PY, str(SIM_DIR / "ecd04_record_conditioned_navigation_v0_jax.py")], cwd=ROOT, check=True)
    subprocess.run([PY, str(SIM_DIR / "ecd04_record_conditioned_navigation_v0_pytorch.py")], cwd=ROOT, check=True)
    subprocess.run(
        [
            "/opt/homebrew/bin/julia",
            "--startup-file=no",
            f"--project={ROOT / 'system_v5/julia_carrier'}",
            str(SIM_DIR / "ecd04_record_conditioned_navigation_v0_julia.jl"),
        ],
        cwd=ROOT,
        env={"JULIA_LOAD_PATH": "@:@stdlib"},
        check=True,
    )
    subprocess.run([PY, str(SIM_DIR / "ecd04_record_conditioned_navigation_v0_envelope.py")], cwd=ROOT, check=True)
    subprocess.run([PY, str(SIM_DIR / "validate_ecd04_record_conditioned_navigation_v0.py")], cwd=ROOT, check=True)
    validator = json.loads((SIM_DIR / "results" / "ecd04_record_conditioned_navigation_v0_validator_results.json").read_text())
    assert validator["ok"] is True


def test_validator_delegates_to_builder_audit_boundary_from_birth() -> None:
    common = _common()
    validator = _validator()
    obj = common.build_navigation_object()
    common.write_json(common.RESULT_PATH, obj)
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
